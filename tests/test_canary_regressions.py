"""Regression coverage for the fleet canary checks."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

import pytest
import requests
from mcp.server.mcpserver.exceptions import ToolError

from cloudtalk_mcp import server
from cloudtalk_mcp.client import CloudTalkClient, _cap_response_data, _json_response
from cloudtalk_mcp.setup import verify as verify_module


LIST_TOOLS = (
    "list_agents",
    "list_calls",
    "list_contacts",
    "list_numbers",
)
PATHS = {
    "list_agents": "/agents/index",
    "list_calls": "/calls/index",
    "list_contacts": "/contacts/index",
    "list_numbers": "/numbers/index",
}
SENTINEL = "Private Person private@example.test secret-token-value"


class RecordingClient(CloudTalkClient):
    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.requests: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, path, params=None):
        self.requests.append((path, params))
        return self.response


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        *,
        body: dict[str, Any] | None = None,
        text: str = SENTINEL,
    ):
        self.status_code = status_code
        self._body = body
        self.text = text
        self.ok = 200 <= status_code < 300
        self.headers: dict[str, str] = {}

    def json(self):
        if self._body is None:
            raise ValueError("not JSON")
        return self._body


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response

    def request(self, *_args, **_kwargs):
        return self.response


class FailingSession:
    def request(self, *_args, **_kwargs):
        raise requests.RequestException(SENTINEL)


def _bare_client(response: FakeResponse | None = None) -> CloudTalkClient:
    client = object.__new__(CloudTalkClient)
    cast(Any, client).session = FakeSession(response) if response else FailingSession()
    return client


def _tool_schemas() -> dict[str, dict[str, Any]]:
    return {
        tool.name: tool.input_schema
        for tool in asyncio.run(server.mcp.list_tools())
        if tool.name in LIST_TOOLS
    }


def test_list_tool_schemas_bound_page_and_total_limit() -> None:
    schemas = _tool_schemas()
    assert set(schemas) == set(LIST_TOOLS)

    for name in LIST_TOOLS:
        page = schemas[name]["properties"]["page"]
        limit = schemas[name]["properties"]["limit"]
        assert page["default"] == 1
        assert page["minimum"] == 1
        assert limit["default"] == 25
        assert limit["minimum"] == 1
        assert limit["maximum"] == 100


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        *((name, {"limit": 0}) for name in LIST_TOOLS),
        *((name, {"limit": 101}) for name in LIST_TOOLS),
        *((name, {"page": 0}) for name in LIST_TOOLS),
    ],
)
async def test_list_tools_reject_invalid_pagination(
    tool_name: str, arguments: dict[str, Any]
) -> None:
    tool = server.mcp._tool_manager.get_tool(tool_name)
    assert tool is not None
    with pytest.raises(ToolError, match="validation error"):
        await tool.run(arguments, None)


@pytest.mark.parametrize("method_name", LIST_TOOLS)
def test_list_clients_trim_overlarge_vendor_responses(method_name: str) -> None:
    response = {
        "responseData": {
            "data": [{"id": value} for value in range(10)],
            "itemsCount": 10,
        }
    }
    client = RecordingClient(response)

    result = getattr(client, method_name)(limit=3)

    assert len(result["responseData"]["data"]) == 3
    assert result["responseData"]["itemsCount"] == 10
    assert len(client.requests) == 1
    path, params = client.requests[0]
    assert path == PATHS[method_name]
    assert params is not None
    assert params["page"] == 1
    assert params["limit"] == 3


def test_list_cap_supports_direct_data_shape_without_mutating_input() -> None:
    response = {"data": [{"id": value} for value in range(4)]}

    result = _cap_response_data(response, 2)

    assert len(result["data"]) == 2
    assert len(response["data"]) == 4


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (FakeResponse(401), "upstream_unauthorized"),
        (FakeResponse(500), "upstream_error"),
    ],
)
def test_upstream_rejections_log_reason_without_response_pii(
    response: FakeResponse,
    reason: str,
    caplog,
) -> None:
    caplog.set_level(logging.WARNING, logger="cloudtalk_mcp.client")
    client = _bare_client(response)

    with pytest.raises(RuntimeError) as error:
        client._request("GET", "https://example.test/api")

    combined = str(error.value) + caplog.text
    assert reason in caplog.text
    assert SENTINEL not in combined


def test_non_json_rejection_omits_response_pii(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="cloudtalk_mcp.client")
    response = FakeResponse(200)

    with pytest.raises(RuntimeError) as error:
        _json_response(response)

    combined = str(error.value) + caplog.text
    assert "upstream_non_json" in caplog.text
    assert SENTINEL not in combined


def test_transport_rejection_omits_exception_pii(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="cloudtalk_mcp.client")
    client = _bare_client()

    with pytest.raises(RuntimeError, match="API request failed") as error:
        client._request("GET", "https://example.test/api")

    combined = str(error.value) + caplog.text
    assert "transport_error" in caplog.text
    assert SENTINEL not in combined


def test_missing_credentials_rejection_has_pii_free_reason_log(
    monkeypatch, caplog
) -> None:
    monkeypatch.delenv("CLOUDTALK_KEY_ID", raising=False)
    monkeypatch.delenv("CLOUDTALK_KEY_SECRET", raising=False)
    monkeypatch.setattr(
        "cloudtalk_mcp.client.credentials.load_into_environ", lambda _keys: None
    )
    caplog.set_level(logging.WARNING, logger="cloudtalk_mcp.client")

    with pytest.raises(RuntimeError, match="credentials not found"):
        CloudTalkClient()

    assert "credentials_missing" in caplog.text
    assert SENTINEL not in caplog.text


def test_verification_success_does_not_print_agent_identity(monkeypatch, capsys) -> None:
    class StubClient:
        def who_am_i(self):
            return {"agent_name": SENTINEL, "agent_email": SENTINEL}

    monkeypatch.setattr(verify_module, "CloudTalkClient", StubClient)

    verify_module.run_verify()

    output = capsys.readouterr().out
    assert output == "Connection successful.\n"
    assert SENTINEL not in output
