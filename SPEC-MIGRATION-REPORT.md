# MCP 2026-07-28 migration notes

CloudTalk MCP targets protocol revision `2026-07-28`. The Python package
requires `mcp>=2.2,<3`; `uv.lock` resolves both `mcp` and `mcp-types` to
`2.2.0`. The protocol changes relevant to this server are classified in
[SPEC-DELTA-2026-07-28.md](SPEC-DELTA-2026-07-28.md).

## Server behavior

- The server uses the SDK v2 `MCPServer` entry point and runs over stdio.
  It exposes 12 tools, three prompts, and three resources. Import and tool
  discovery do not load CloudTalk credentials; a client resolves them when a
  tool or resource needs the vendor API.
- The SDK supports modern `2026-07-28` requests and legacy `2025-11-25`
  negotiation. Modern discovery, per-request metadata, result types, routing
  headers, error codes, and private zero-TTL cache hints are covered by the
  protocol tests. The HTTP app used in those tests is in process; the product
  does not expose an HTTP transport.
- Dictionary tool results retain their JSON text content. The migration does
  not add a structured output model.
- The four list tools require `page >= 1` and `1 <= limit <= 100`, and trim
  overlarge responses to the requested limit. A call returns one page.
  The vendor's default ordering is not established by these tests.
- Client rejection logs use fixed reasons and omit upstream response bodies
  and transport exception text. Tests check that sentinel personal data is
  absent from the exercised error paths.

## Reproduce checks

With the locked development environment installed, run from the repository
root:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/python tests/spec_check.py --mcp-only
uv lock --check --offline
```

The suite uses fake CloudTalk responses and an in-process SDK HTTP app. It
does not verify live vendor responses, saved-credential CLI behavior, or a
deployed stdio connection. The protocol guard checks installed SDK constants;
the lock selects SDK 2.2.0, while the requirement permits later 2.x releases.

## Public error behavior

Tool calls return `isError=true` for failures. Missing credentials, rejected
authorization, access denial, not-found responses, rate limits, upstream HTTP
failures, unreadable responses, and transport failures use fixed messages that
do not include credentials, request URLs, response bodies, or exception text.
Validation errors identify the parameter and its expected shape without
echoing the rejected value. Unexpected failures return a generic tool error.
Resource read failures return a fixed generic message and do not expose the
underlying exception. For writes with an uncertain transport outcome, clients
are told to check the operation status before retrying.
