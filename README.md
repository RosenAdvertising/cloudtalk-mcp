# cloudtalk-mcp

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F59E0B.svg)](https://opensource.org/licenses/MIT)
[![12 tools](https://img.shields.io/badge/tools-12-22C55E.svg)](https://github.com/RosenAdvertising/cloudtalk-mcp)
[![MCP](https://img.shields.io/badge/MCP-compatible-7C3AED.svg)](https://modelcontextprotocol.io)
[![CloudTalk](https://img.shields.io/badge/CloudTalk-API-6C4FE8.svg)](https://www.cloudtalk.io)

MCP server for CloudTalk — call center management, agents, contacts, and analytics for law firms.

Requires Python MCP SDK >=2.3,<3; protocol revision 2026-07-28 is checked separately.

## Tools (12)

| Tool                  | Description                                         |
| --------------------- | --------------------------------------------------- |
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

## Setup

```bash
pip install -e .
cloudtalk-mcp-setup
```

Find your Key ID and Key Secret at **app.cloudtalk.io → Settings → API**.

### Credential storage

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

## Verify

```bash
cloudtalk-mcp-verify
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "cloudtalk": {
      "command": "cloudtalk-mcp"
    }
  }
}
```

## HTTP mode

Stdio stays the default. Set `CLOUDTALK_MCP_TRANSPORT=streamable-http` to serve one stateless endpoint at `/mcp`. Credentials are the same variables the stdio server already reads (`CLOUDTALK_KEY_ID` and `CLOUDTALK_KEY_SECRET`, via the environment, the OS keyring, or the file fallback). They are never taken from the HTTP request.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `CLOUDTALK_MCP_ALLOWED_HOSTS` and `CLOUDTALK_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Variable | Purpose |
| --- | --- |
| `CLOUDTALK_MCP_TRANSPORT` | `stdio` (default) or `streamable-http` |
| `CLOUDTALK_MCP_HOST` | Bind address. Default `127.0.0.1` |
| `PORT` | Bind port. Default `8080`. Must be an integer |
| `CLOUDTALK_MCP_ALLOWED_HOSTS` | Comma-separated allowed `Host` values. Required when `CLOUDTALK_MCP_HOST` is not loopback (`127.0.0.1`, `localhost`, or `::1`) |
| `CLOUDTALK_MCP_ALLOWED_ORIGINS` | Optional comma-separated allowed `Origin` values, used with the allowed hosts when the bind address is not loopback |
| `CLOUDTALK_KEY_ID` | CloudTalk API key id |
| `CLOUDTALK_KEY_SECRET` | CloudTalk API key secret |

```bash
CLOUDTALK_MCP_TRANSPORT=streamable-http PORT=8080 cloudtalk-mcp
```

That listens on `http://127.0.0.1:8080/mcp`.

## Auth

HTTP Basic Auth using `base64(KEY_ID:KEY_SECRET)`. All API paths use CloudTalk's resource-verb convention (`/agents/index.json`, `/contacts/add.json`) — handled internally by the client.

## API notes

- **GET** — list/show operations
- **PUT** — create operations (`/contacts/add.json`)
- **POST** — update operations (`/contacts/edit/{id}.json`)
- **DELETE** — delete operations
- `get_call` routes to the analytics subdomain (`analytics-api.cloudtalk.io`)
- Contact phone/email are stored as sub-object arrays (`ContactNumber`, `ContactEmail`) per the CloudTalk API schema
