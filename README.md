# CloudTalk MCP server

[![CI](https://github.com/RosenAdvertising/cloudtalk-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/RosenAdvertising/cloudtalk-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP 2026-07-28](https://img.shields.io/badge/MCP-2026--07--28-7C3AED.svg)](https://modelcontextprotocol.io)
[![PyPI version](https://img.shields.io/pypi/v/cloudtalk-mcp.svg)](https://pypi.org/project/cloudtalk-mcp/)

Connect Claude and other MCP clients to CloudTalk to manage calls, agents, contacts and numbers.

CloudTalk MCP server is a [Model Context Protocol](https://modelcontextprotocol.io) server for [CloudTalk](https://www.cloudtalk.io), the cloud call center platform. It registers 12 tools that read and write CloudTalk data. It runs over stdio by default, for desktop clients such as Claude Desktop, and offers an opt-in stateless Streamable HTTP mode that implements MCP specification 2026-07-28. CloudTalk credentials stay on the machine that runs the server: they come from the setup command and your operating system's keyring, or from environment variables, never from the client.

## Features

- **Calls**: list calls with date and status filters, read call details from the CloudTalk analytics API, and start outbound calls from an agent.
- **Contacts**: list, search, create, update and delete contacts.
- **Agents**: list the agents on your account.
- **Numbers**: list your account's phone numbers.
- **Statistics**: read real-time group statistics, such as answered calls and abandon rate.
- **Account**: confirm which CloudTalk account is connected.

## Tools

The server registers 12 tools.

| Tool | What it does |
| --- | --- |
| `who_am_i`            | Return identity of the connected CloudTalk account  |
| `list_agents`         | List one page of agents                             |
| `list_calls`          | List calls with date/status filters                 |
| `get_call`            | Get comprehensive call details including recording  |
| `initiate_call`       | Place an outbound call from an agent                |
| `list_contacts`       | List/search contacts by keyword                     |
| `get_contact`         | Get a specific contact                              |
| `create_contact`      | Create a new contact                                |
| `update_contact`      | Update contact fields                               |
| `delete_contact`      | Delete a contact                                    |
| `list_numbers`        | List account phone numbers                          |
| `get_call_statistics` | Real-time group statistics (answered, abandon rate) |

### Prompts and resources

The server also registers three prompts and three read-only resources.

| Prompt | What it does |
| --- | --- |
| `missed_call_review` | Review missed calls for the day and recommend follow-up actions. |
| `call_quality_review` | Review call quality and content for a specific call. Takes a `call_id`. |
| `agent_performance_brief` | Call volume and performance brief for all agents today. |

| Resource | What it holds |
| --- | --- |
| `cloudtalk://numbers` | Up to 100 assigned phone numbers. |
| `cloudtalk://agents` | Up to 100 agents in your account. |
| `cloudtalk://security-notes` | Security notes for this server, as Markdown. |

## Requirements

- Python 3.10 or later
- A CloudTalk account with API access: a Key ID and a Key Secret
- An MCP client such as Claude Desktop

## Installation

Install [uv](https://docs.astral.sh/uv/), then clone the repository and install its locked dependencies:

```bash
git clone https://github.com/RosenAdvertising/cloudtalk-mcp.git
cd cloudtalk-mcp
uv sync --locked
```

Releases are also published to PyPI: `pip install cloudtalk-mcp` installs version 0.2.0, which predates the HTTP mode described below. Install from source to use HTTP mode.

## Configuration

Run the guided setup from your clone of the repository:

```bash
uv run --locked cloudtalk-mcp-setup
```

Setup prompts for your Key ID and Key Secret, stores them (see [Credential storage](#credential-storage)), and then verifies the connection by reading one agent from your account. Find your Key ID and Key Secret at **app.cloudtalk.io → Settings → API**.

To verify again later:

```bash
uv run --locked cloudtalk-mcp-verify
```

The server reads these environment variables. A variable set in the process environment takes precedence over a stored value.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `CLOUDTALK_KEY_ID` | Yes | Stored value from setup | CloudTalk API key ID. |
| `CLOUDTALK_KEY_SECRET` | Yes | Stored value from setup | CloudTalk API key secret. Sent with the key ID as HTTP Basic authentication. |
| `CLOUDTALK_MCP_USE_KEYRING` | No | `1` | Set to `0` (or `false`, `no`, `off`) to skip the OS keyring and use the `.env` file fallback. |

## Usage with Claude Desktop

Add the server to Claude Desktop's configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "cloudtalk": {
      "command": "uv",
      "args": ["run", "--locked", "--directory", "/absolute/path/to/cloudtalk-mcp", "cloudtalk-mcp"]
    }
  }
}
```

Replace `/absolute/path/to/cloudtalk-mcp` with the path of your clone. Restart Claude Desktop after saving. Any other stdio MCP client uses the same command and arguments.

## HTTP mode

Stdio is the default. Set `CLOUDTALK_MCP_TRANSPORT=streamable-http` to serve the stateless Streamable HTTP transport from MCP specification 2026-07-28 at `/mcp`. Each request stands alone: no initialization handshake and no `Mcp-Session-Id`. Clients on earlier protocol versions are served on the same endpoint.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `CLOUDTALK_MCP_ALLOWED_HOSTS` and `CLOUDTALK_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Variable | Default | Purpose |
| --- | --- | --- |
| `CLOUDTALK_MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http`. A set but empty value selects `stdio`. |
| `CLOUDTALK_MCP_HOST` | `127.0.0.1` | Bind address. `127.0.0.1`, `localhost` and `::1` use the SDK's built-in Host and Origin checks; any other value requires `CLOUDTALK_MCP_ALLOWED_HOSTS`. |
| `PORT` | `8080` | Port; must be an integer. |
| `CLOUDTALK_MCP_ALLOWED_HOSTS` | unset | Comma-separated `Host` header values accepted on a non-loopback bind, such as `mcp.example.com:8080` or `mcp.example.com:*`. |
| `CLOUDTALK_MCP_ALLOWED_ORIGINS` | unset | Comma-separated `Origin` values accepted on a non-loopback bind, such as `https://client.example.com`. Requests without an `Origin` header are accepted; with this unset on a non-loopback bind, a request that carries an `Origin` header is rejected. |

CloudTalk credentials come from the same configuration as stdio (see [Configuration](#configuration)), never from the request.

```bash
CLOUDTALK_MCP_TRANSPORT=streamable-http PORT=8080 uv run --locked cloudtalk-mcp
```

Point the MCP client at `http://127.0.0.1:8080/mcp`.

## Error handling

A failed tool call returns an MCP error result (`isError`) with a fixed message that starts with `Error executing tool <name>: `. The server never passes a CloudTalk response body, a request URL or a credential back to the client.

| Situation | What the tool returns |
| --- | --- |
| Credentials missing | "CloudTalk credentials are missing. Set CLOUDTALK_KEY_ID and CLOUDTALK_KEY_SECRET, or run cloudtalk-mcp-setup." |
| HTTP 401 | "CloudTalk authorization was rejected; re-run cloudtalk-mcp-setup." |
| HTTP 403 | "CloudTalk access denied: the connected account lacks permission for this action (or the authorization expired; re-run cloudtalk-mcp-setup if so)." |
| HTTP 404 | "The requested CloudTalk record was not found." |
| HTTP 429 | "CloudTalk rate limit reached. Retry after N seconds." N comes from the `Retry-After` header, or is 10 when the header is missing; an unusable value gives "Retry after a short delay." |
| Redirect response | "CloudTalk API returned HTTP 302: unexpected redirect." (redirects are never followed) |
| Other HTTP error statuses | "CloudTalk API returned HTTP 500: upstream service error." The reason is one fixed phrase chosen from the error code in the CloudTalk response: invalid request, record not found, permission denied, authorization rejected, rate limit exceeded, request validation failed, upstream service error or service unavailable; any other or missing code gives "request rejected". |
| Success response that is not valid JSON | "CloudTalk API returned an unreadable response. Check the result in CloudTalk before retrying." |
| Timeout or connection failure on a read | "CloudTalk connection failed. Check connectivity and try again." |
| Timeout or connection failure on a write | "CloudTalk request could not be confirmed. The operation outcome is unknown. Check whether it completed before retrying." |
| Invalid arguments | A message such as "Invalid arguments: 'limit' must be an integer from 1 to 100." |
| Anything else | `Error executing tool <name>` with no detail. |

Every CloudTalk request has a 30-second timeout. The server does not retry failed requests: it returns the message above and leaves any retry to you.

Missing credentials do not stop the server from starting: each tool call reports them. At startup the server exits with a message and a non-zero status when `CLOUDTALK_MCP_TRANSPORT` is neither `stdio` nor `streamable-http`, when `PORT` is not an integer, or when a non-loopback `CLOUDTALK_MCP_HOST` is set without `CLOUDTALK_MCP_ALLOWED_HOSTS`.

## Credential storage

By default credentials are stored in your operating system's native secret store
via the cross-platform [`keyring`](https://github.com/jaraco/keyring) library:

| OS      | Backend                                  |
| ------- | ---------------------------------------- |
| macOS   | Keychain                                 |
| Windows | Credential Manager                       |
| Linux   | Secret Service (GNOME Keyring / KWallet) |

Secrets are saved under the service name `cloudtalk-mcp` when a usable keyring
is available.

**File fallback.** On a host with no keyring backend (e.g. a headless Linux box
without Secret Service), or if you set `CLOUDTALK_MCP_USE_KEYRING=0`, credentials
fall back to a `~/.cloudtalk-mcp/.env` file with `0600` permissions.

On Windows, the file is stored in the user's profile and protected by Windows'
default per-user access rules. On POSIX, files are created with `0600` permissions
and writes fail closed if private permissions cannot be established.

**Read order.** A credential already present in the server process environment
takes precedence. Otherwise the client checks the OS keyring, then the `.env`
file. If you change credentials after the server has loaded them, restart the
MCP server to reload the new values.

**Pluggable backend.** `keyring` lets you point at any secret store. For example,
install [`keyrings.cryptfile`](https://pypi.org/project/keyrings.cryptfile/) for
an encrypted file backend, or a cloud backend, then select it with the standard
`PYTHON_KEYRING_BACKEND` environment variable or a `keyringrc.cfg`. See the
[keyring configuration docs](https://github.com/jaraco/keyring#configuring).

## Auth

HTTP Basic Auth using `base64(KEY_ID:KEY_SECRET)`. All API paths use CloudTalk's resource-verb convention (`/agents/index.json`, `/contacts/add.json`) — handled internally by the client.

## API notes

- **GET** — list/show operations
- **PUT** — create operations (`/contacts/add.json`)
- **POST** — update operations (`/contacts/edit/{id}.json`) and call initiation (`/calls/create.json`)
- **DELETE** — delete operations
- `get_call` routes to the analytics subdomain (`analytics-api.cloudtalk.io`)
- Contact phone/email are stored as sub-object arrays (`ContactNumber`, `ContactEmail`) per the CloudTalk API schema

## Testing

The test suite runs offline and needs no CloudTalk account: CloudTalk API calls are replaced with test doubles. It covers the error messages tools return, argument validation, page and limit controls, path identifier handling, credential loading and private file storage, the setup and verify command help, logs that omit call and contact data, the MCP transport boundary, MCP specification 2026-07-28 behavior, and the Streamable HTTP transport including Host and Origin checks and stateless requests.

```bash
uv sync --locked
uv run --locked pytest -q
```

CI runs the suite on every push and pull request to `main`.

## License

MIT. See [LICENSE](LICENSE).
