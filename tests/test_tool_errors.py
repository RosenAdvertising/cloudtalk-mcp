from __future__ import annotations

import logging
from typing import Any, cast

import pytest
import requests
from mcp.types import CallToolRequestParams, CallToolResult, TextContent
from test_canary_regressions import FakeResponse as BaseResponse, _bare_client

from cloudtalk_mcp import server
from cloudtalk_mcp.client import CloudTalkClient
from cloudtalk_mcp.errors import MissingCredentialsError


PII = "Private Person private@example.test secret-token-value"


class FakeResponse(BaseResponse):
    def __init__(self, status: int, body: Any = None, headers=None, *, invalid=False):
        super().__init__(status, body=None if invalid else body)
        self.headers = headers or {}


def client_for(response=None, error=None):
    client = _bare_client(response)
    if error is not None:

        def fail(*args, **kwargs):
            raise error

        cast(Any, client.session).request = fail
    return client


async def dispatch(tool: str, args: dict[str, Any] | None = None):
    result = await server.mcp._handle_call_tool(
        cast(Any, None), CallToolRequestParams(name=tool, arguments=args or {})
    )
    assert isinstance(result, CallToolResult)
    assert result.is_error is True
    assert isinstance(result.content[0], TextContent)
    return result.content[0].text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            401,
            "Error executing tool who_am_i: CloudTalk authorization was rejected; re-run cloudtalk-mcp-setup.",
        ),
        (
            403,
            "Error executing tool who_am_i: CloudTalk access denied: the connected account lacks permission for this action (or the authorization expired; re-run cloudtalk-mcp-setup if so).",
        ),
        (
            404,
            "Error executing tool get_contact: The requested CloudTalk record was not found.",
        ),
        (
            429,
            "Error executing tool who_am_i: CloudTalk rate limit reached. Retry after a short delay.",
        ),
        (
            429,
            "Error executing tool who_am_i: CloudTalk rate limit reached. Retry after a short delay.",
        ),
        (
            503,
            "Error executing tool who_am_i: CloudTalk API returned HTTP 503: service unavailable.",
        ),
        (
            503,
            "Error executing tool who_am_i: CloudTalk API returned HTTP 503: request rejected.",
        ),
    ],
)
async def test_http_failures_have_safe_dispatch_results(monkeypatch, status, expected):
    headers = (
        {"Retry-After": "300"}
        if status == 429 and expected.endswith("300 seconds.")
        else ({"Retry-After": "-2"} if status == 429 else {})
    )
    body = (
        {"code": "service_unavailable"}
        if status == 503 and "service unavailable" in expected
        else {"message": PII}
    )
    response = FakeResponse(status, body, headers)
    monkeypatch.setattr(server, "_client", lambda: client_for(response))
    tool = "get_contact" if status == 404 else "who_am_i"
    actual = await dispatch(tool, {"contact_id": 22} if tool == "get_contact" else {})
    assert actual == expected
    assert PII not in actual


@pytest.mark.asyncio
async def test_missing_credentials_exact_dispatch_text(monkeypatch):
    monkeypatch.delenv("CLOUDTALK_KEY_ID", raising=False)
    monkeypatch.delenv("CLOUDTALK_KEY_SECRET", raising=False)
    monkeypatch.setattr(
        "cloudtalk_mcp.client.credentials.load_into_environ", lambda keys: None
    )
    monkeypatch.setattr(server, "_client", CloudTalkClient)
    assert await dispatch("who_am_i") == (
        "Error executing tool who_am_i: CloudTalk credentials are missing. Set "
        "CLOUDTALK_KEY_ID and CLOUDTALK_KEY_SECRET, or run cloudtalk-mcp-setup."
    )


@pytest.mark.asyncio
async def test_transport_failure_write_warns_check_status(monkeypatch):
    monkeypatch.setattr(
        server,
        "_client",
        lambda: client_for(error=requests.Timeout(PII)),
    )
    assert await dispatch("create_contact", {"first_name": "A"}) == (
        "Error executing tool create_contact: CloudTalk request could not be confirmed. "
        "The operation outcome is unknown. Check whether it completed before retrying."
    )


@pytest.mark.asyncio
async def test_malformed_json_response_is_safe(monkeypatch):
    monkeypatch.setattr(
        server, "_client", lambda: client_for(FakeResponse(200, invalid=True))
    )
    assert await dispatch("who_am_i") == (
        "Error executing tool who_am_i: CloudTalk API returned an unreadable response. Check the result in CloudTalk before retrying."
    )


@pytest.mark.asyncio
async def test_schema_error_names_parameter_and_sanitizes_input(caplog):
    caplog.set_level(logging.INFO)
    actual = await dispatch("list_agents", {"limit": PII})
    assert actual == (
        "Error executing tool list_agents: Invalid arguments: 'limit' must be an integer from 1 to 100."
    )
    assert PII not in actual + caplog.text


@pytest.mark.asyncio
async def test_unknown_exception_stays_sdk_masked_and_logs_fixed_reason(
    monkeypatch, caplog
):
    def crash():
        raise RuntimeError(PII)

    monkeypatch.setattr(server, "_client", crash)
    caplog.set_level(logging.ERROR)
    assert await dispatch("who_am_i") == "Error executing tool who_am_i"
    assert "reason=unexpected_failure" in caplog.text
    assert PII not in caplog.text


@pytest.mark.asyncio
async def test_unexpected_outer_error_does_not_adopt_safe_cause(monkeypatch, caplog):
    def crash():
        try:
            raise MissingCredentialsError()
        except MissingCredentialsError as cause:
            raise ValueError(PII) from cause

    monkeypatch.setattr(server, "_client", crash)
    caplog.set_level(logging.ERROR)
    assert await dispatch("who_am_i") == "Error executing tool who_am_i"
    assert "credentials are missing" not in caplog.text
    assert PII not in caplog.text


@pytest.mark.asyncio
async def test_top_level_validation_names_expected_argument_shape():
    actual = await dispatch("list_calls", {"date_from": 42})
    assert actual == (
        "Error executing tool list_calls: Invalid arguments: 'date_from' must be a string."
    )


def test_schema_shape_recursively_explains_nullable_anyof():
    assert (
        server.SafeMCPServer._shape(
            {
                "anyOf": [
                    {"type": "string"},
                    {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                ]
            }
        )
        == "a string or an integer or null"
    )


def test_retry_hint_rejects_absurd_and_malformed_values():
    from cloudtalk_mcp.client import _retry_hint

    assert (
        _retry_hint(FakeResponse(429, headers={"Retry-After": "60"}))
        == "Retry after 60 seconds."
    )
    assert (
        _retry_hint(FakeResponse(429, headers={"Retry-After": "999999999"}))
        == "Retry after a short delay."
    )
    assert (
        _retry_hint(FakeResponse(429, headers={"Retry-After": "tomorrow"}))
        == "Retry after a short delay."
    )


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_every_request_has_a_timeout(method):
    client = _bare_client(FakeResponse(200, {}))
    captured = {}

    def fake_request(*args, **kwargs):
        captured.update(kwargs)
        return FakeResponse(200, {})

    cast(Any, client.session).request = fake_request
    client._request(method, "https://example.test/api")
    assert captured["timeout"] == 30
    assert captured["allow_redirects"] is False


@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError])
@pytest.mark.parametrize(
    ("method", "write"),
    [("GET", False), ("POST", True), ("PUT", True), ("PATCH", True), ("DELETE", True)],
)
def test_transport_failures_distinguish_read_and_write(method, write, error_type):
    client = client_for(error=error_type(PII))
    with pytest.raises(Exception) as raised:
        client._request(method, "https://example.test/api")
    expected = (
        "outcome is unknown. Check whether it completed before retrying"
        if write
        else "connection failed. Check connectivity and try again"
    )
    assert expected in str(raised.value)
    assert PII not in str(raised.value)


def test_string_path_ids_are_escaped(monkeypatch):
    urls = []
    client = _bare_client(FakeResponse(200, {}))
    cast(Any, client.session).request = lambda method, url, **kwargs: (
        urls.append(url) or FakeResponse(200, {})
    )
    client.get_contact("../x")
    client.update_contact("../x", first_name="A")
    client.delete_contact("../x")
    client.get_call("../x")
    assert all("../x" not in url for url in urls)
    assert urls == [
        "https://my.cloudtalk.io/api/contacts/show/..%2Fx.json",
        "https://my.cloudtalk.io/api/contacts/edit/..%2Fx.json",
        "https://my.cloudtalk.io/api/contacts/delete/..%2Fx.json",
        "https://analytics-api.cloudtalk.io/api/calls/..%2Fx",
    ]


@pytest.mark.asyncio
async def test_resource_failure_has_fixed_text_and_no_exception_log(
    monkeypatch, caplog
):
    def crash():
        raise RuntimeError(PII)

    monkeypatch.setattr(server, "_client", crash)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception) as raised:
            await server.mcp.read_resource("cloudtalk://numbers")
    assert (
        str(raised.value)
        == "CloudTalk resource could not be read. Check connectivity and try again."
    )
    assert PII not in caplog.text


def test_verify_without_credentials_exits_actionably(capsys, monkeypatch):
    from cloudtalk_mcp.setup import verify

    monkeypatch.setattr(
        verify,
        "CloudTalkClient",
        lambda: (_ for _ in ()).throw(MissingCredentialsError()),
    )
    with pytest.raises(SystemExit) as raised:
        verify.main()
    assert raised.value.code == 1
    assert "CloudTalk credentials are missing" in capsys.readouterr().err


def test_setup_eof_exits_cleanly(capsys, monkeypatch):
    from cloudtalk_mcp.setup import setup

    monkeypatch.setattr(
        "builtins.input", lambda prompt: (_ for _ in ()).throw(EOFError)
    )
    with pytest.raises(SystemExit) as raised:
        setup.main()
    assert raised.value.code == 1
    assert "Key ID is required" in capsys.readouterr().err


def test_setup_bad_key_exits_with_typed_message(capsys, monkeypatch):
    from cloudtalk_mcp.setup import setup, verify

    answers = iter(["id", "secret"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(setup, "getpass", lambda prompt: next(answers))
    monkeypatch.setattr(setup.credentials, "set_secret", lambda key, value: "file")
    monkeypatch.setattr(setup.credentials, "ENV_FILE", "/isolated/fake.env")
    monkeypatch.setattr(
        verify, "run_verify", lambda: (_ for _ in ()).throw(MissingCredentialsError())
    )
    with pytest.raises(SystemExit) as raised:
        setup.main()
    captured = capsys.readouterr()
    assert raised.value.code == 1
    assert "CloudTalk credentials are missing" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.asyncio
async def test_unreadable_write_response_advises_checking_result(monkeypatch, caplog):
    monkeypatch.setattr(
        server, "_client", lambda: client_for(FakeResponse(200, invalid=True))
    )
    with caplog.at_level(logging.INFO):
        actual = await dispatch("create_contact", {"first_name": "Example"})
    assert (
        actual
        == "Error executing tool create_contact: CloudTalk API returned an unreadable response. Check the result in CloudTalk before retrying."
    )
    assert PII not in actual + caplog.text


@pytest.mark.asyncio
async def test_retry_after_over_sixty_keeps_advice_without_sleep(monkeypatch):
    monkeypatch.setattr(
        server,
        "_client",
        lambda: client_for(FakeResponse(429, headers={"Retry-After": "300"})),
    )
    assert await dispatch("who_am_i") == (
        "Error executing tool who_am_i: CloudTalk rate limit reached. Retry after a short delay."
    )


def test_redirect_response_is_not_returned_as_success():
    client = _bare_client(FakeResponse(302, {"success": True}))
    with pytest.raises(Exception) as raised:
        client._request("GET", "https://example.test/api")
    assert "HTTP 302: unexpected redirect" in str(raised.value)


def test_setup_reads_secret_with_getpass(capsys, monkeypatch):
    from cloudtalk_mcp.setup import setup

    monkeypatch.setattr("builtins.input", lambda _prompt: "key-id")
    monkeypatch.setattr(setup, "getpass", lambda _prompt: "private-secret")
    monkeypatch.setattr(setup.credentials, "set_secret", lambda *_args: "file")
    monkeypatch.setattr(setup.credentials, "ENV_FILE", "/isolated/fake.env")
    monkeypatch.setattr(
        "cloudtalk_mcp.setup.verify.run_verify", lambda: (_ for _ in ()).throw(MissingCredentialsError())
    )
    with pytest.raises(SystemExit):
        setup.main()
    output = capsys.readouterr()
    assert "private-secret" not in output.out + output.err


def test_fallback_secret_file_is_private_at_write(tmp_path, monkeypatch):
    import stat

    from cloudtalk_mcp import credentials

    config_dir = tmp_path / "config"
    env_file = config_dir / ".env"
    monkeypatch.setattr(credentials, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(credentials, "ENV_FILE", env_file)
    credentials._write_env_file({"CLOUDTALK_KEY_SECRET": "private-secret"})
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert env_file.read_text() == "CLOUDTALK_KEY_SECRET=private-secret\n"


@pytest.mark.asyncio
async def test_unexpected_vendor_reason_parser_error_is_masked(monkeypatch, caplog):
    response = FakeResponse(500, {})

    def fail():
        raise RuntimeError(PII)

    monkeypatch.setattr(response, "json", fail)
    monkeypatch.setattr(server, "_client", lambda: client_for(response))
    with caplog.at_level(logging.ERROR):
        actual = await dispatch("who_am_i")
    assert actual == "Error executing tool who_am_i"
    assert PII not in caplog.text
    assert "reason=unexpected_failure" in caplog.text
