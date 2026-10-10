"""In-process Streamable HTTP transport checks for MCP 2026-07-28."""

from __future__ import annotations

import contextlib
import json
from typing import Any

import httpx2 as httpx
import pytest

from cloudtalk_mcp import server
from test_canary_regressions import FakeResponse, _bare_client

PROTOCOL_VERSION = "2026-07-28"
PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"


def _headers(method: str, *, name: str | None = None) -> dict[str, str]:
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "mcp-protocol-version": PROTOCOL_VERSION,
        "mcp-method": method,
    }
    if name is not None:
        headers["mcp-name"] = name
    return headers


def _body(
    method: str,
    params: dict[str, Any] | None = None,
    *,
    request_id: int = 1,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["_meta"] = {
        PROTOCOL_VERSION_META_KEY: PROTOCOL_VERSION,
        CLIENT_CAPABILITIES_META_KEY: {},
        CLIENT_INFO_META_KEY: {"name": "cloudtalk-http-test", "version": "0"},
    }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": request_params,
    }


async def _open(app, client_headers: dict[str, str] | None = None):
    transport = httpx.ASGITransport(app=app)
    base_headers = {"host": "127.0.0.1:8000"}
    if client_headers:
        base_headers.update(client_headers)
    client = httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1:8000",
        headers=base_headers,
    )
    return client


def _result(response: httpx.Response) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["jsonrpc"] == "2.0"
    return payload["result"]


def _no_session_header(response: httpx.Response) -> None:
    assert "mcp-session-id" not in {key.lower() for key in response.headers}


@pytest.mark.asyncio
async def test_http_tools_list_matches_stdio_server() -> None:
    stdio_tools = await server.mcp.list_tools()
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        client = await _open(app)
        async with client:
            response = await client.post(
                "/mcp",
                headers=_headers("tools/list"),
                json=_body("tools/list"),
            )
    result = _result(response)
    http_tools = result["tools"]
    assert [tool["name"] for tool in http_tools] == [tool.name for tool in stdio_tools]
    assert [tool["inputSchema"] for tool in http_tools] == [
        tool.model_dump(by_alias=True)["inputSchema"] for tool in stdio_tools
    ]


@pytest.mark.asyncio
async def test_http_read_tool_uses_vendor_mock(monkeypatch) -> None:
    vendor = FakeResponse(
        200,
        body={
            "responseData": {
                "data": [
                    {
                        "Agent": {
                            "id": 7,
                            "email": "ada@example.test",
                            "firstname": "Ada",
                            "lastname": "Lovelace",
                        }
                    }
                ],
                "itemsCount": 1,
            }
        },
    )
    expected = _bare_client(vendor).who_am_i()
    monkeypatch.setattr(server, "_client", lambda: _bare_client(vendor))
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        http = await _open(app)
        async with http:
            response = await http.post(
                "/mcp",
                headers=_headers("tools/call", name="who_am_i"),
                json=_body("tools/call", {"name": "who_am_i", "arguments": {}}),
            )
    result = _result(response)
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"]) == expected


@pytest.mark.asyncio
async def test_http_requests_are_stateless() -> None:
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        client = await _open(app)
        async with client:
            first = await client.post(
                "/mcp",
                headers=_headers("tools/list"),
                json=_body("tools/list", request_id=1),
            )
            second = await client.post(
                "/mcp",
                headers={**_headers("tools/list"), "mcp-session-id": "stale-session"},
                json=_body("tools/list", request_id=2),
            )
    assert _result(first)["tools"]
    assert _result(second)["tools"] == _result(first)["tools"]
    _no_session_header(first)
    _no_session_header(second)


def test_bogus_transport_exits_and_default_is_stdio(monkeypatch) -> None:
    monkeypatch.delenv("CLOUDTALK_MCP_TRANSPORT", raising=False)
    assert server._requested_transport() == "stdio"
    ran = {"stdio": False}

    def run_stdio() -> None:
        ran["stdio"] = True

    monkeypatch.setattr(server.mcp, "run", run_stdio)
    server.main()
    assert ran["stdio"] is True

    monkeypatch.setenv("CLOUDTALK_MCP_TRANSPORT", "bogus")
    with pytest.raises(SystemExit) as exc:
        server.main()
    message = str(exc.value)
    assert "bogus" in message
    assert "stdio" in message
    assert "streamable-http" in message


@pytest.mark.asyncio
async def test_allowed_hosts_refuse_other_host_and_bad_origin(monkeypatch) -> None:
    monkeypatch.setenv("CLOUDTALK_MCP_HOST", "10.1.2.3")
    monkeypatch.setenv("CLOUDTALK_MCP_ALLOWED_HOSTS", "cloudtalk.internal")
    monkeypatch.setenv("CLOUDTALK_MCP_ALLOWED_ORIGINS", "https://cloudtalk.internal")
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        client = await _open(app)
        async with client:
            other_host = await client.post(
                "/mcp",
                headers={**_headers("tools/list"), "host": "other.example"},
                json=_body("tools/list"),
            )
            bad_origin = await client.post(
                "/mcp",
                headers={
                    **_headers("tools/list"),
                    "host": "cloudtalk.internal",
                    "origin": "https://evil.example",
                },
                json=_body("tools/list"),
            )
    assert other_host.status_code == 421
    assert bad_origin.status_code == 403


def test_non_loopback_host_without_allowed_hosts_exits(monkeypatch) -> None:
    monkeypatch.setenv("CLOUDTALK_MCP_HOST", "10.1.2.3")
    monkeypatch.delenv("CLOUDTALK_MCP_ALLOWED_HOSTS", raising=False)
    with pytest.raises(SystemExit) as exc:
        server.create_serve_app()
    assert "CLOUDTALK_MCP_ALLOWED_HOSTS" in str(exc.value)


@pytest.mark.asyncio
async def test_get_and_delete_are_rejected_and_discover_names_version() -> None:
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        client = await _open(app)
        async with client:
            get_response = await client.get("/mcp", headers=_headers("tools/list"))
            delete_response = await client.delete(
                "/mcp", headers=_headers("tools/list")
            )
            discover = await client.post(
                "/mcp",
                headers=_headers("server/discover"),
                json=_body("server/discover"),
            )
    assert get_response.status_code == 405
    assert delete_response.status_code == 405
    result = _result(discover)
    assert PROTOCOL_VERSION in result["supportedVersions"]
    version = result["_meta"][SERVER_INFO_META_KEY]["version"]
    assert isinstance(version, str) and version != ""


@pytest.mark.asyncio
async def test_stateless_lifespan_runs_once(monkeypatch) -> None:
    entered = {"count": 0}

    @contextlib.asynccontextmanager
    async def counting(_app):
        entered["count"] += 1
        yield {"entries": entered["count"]}

    monkeypatch.setattr(server.mcp._lowlevel_server, "lifespan", counting)
    monkeypatch.delenv("CLOUDTALK_MCP_HOST", raising=False)
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        client = await _open(app)
        async with client:
            first = await client.post(
                "/mcp",
                headers=_headers("tools/list"),
                json=_body("tools/list", request_id=1),
            )
            second = await client.post(
                "/mcp",
                headers=_headers("tools/list"),
                json=_body("tools/list", request_id=2),
            )
    assert first.status_code == 200
    assert second.status_code == 200
    assert entered["count"] == 1
