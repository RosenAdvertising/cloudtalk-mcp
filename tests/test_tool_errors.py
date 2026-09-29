from __future__ import annotations

import logging
from typing import Any, cast

import pytest
import requests
from mcp.types import CallToolRequestParams
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
        None, CallToolRequestParams(name=tool, arguments=args or {})
    )
    assert result.is_error is True
    return result.content[0].text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            401,
            "Error executing tool who_am_i: CloudTalk authorization was rejected or expired. Reauthorize the account with cloudtalk-mcp-setup.",
        ),
        (
            403,
            "Error executing tool who_am_i: CloudTalk authorization was rejected or expired. Reauthorize the account with cloudtalk-mcp-setup.",
        ),
        (
            404,
            "Error executing tool get_contact: The requested CloudTalk record was not found.",
        ),
        (
            429,
            "Error executing tool who_am_i: CloudTalk rate limit reached. Retry after 300 seconds.",
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
        "The operation outcome may be unknown; check its status before retrying."
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
        _retry_hint(FakeResponse(429, headers={"Retry-After": "300"}))
        == "Retry after 300 seconds."
    )
    assert (
        _retry_hint(FakeResponse(429, headers={"Retry-After": "999999999"}))
        == "Retry after a short delay."
    )
    assert (
        _retry_hint(FakeResponse(429, headers={"Retry-After": "tomorrow"}))
        == "Retry after a short delay."
    )


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
