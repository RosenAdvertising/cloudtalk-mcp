# cloudtalk-mcp

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F59E0B.svg)](https://opensource.org/licenses/MIT)
[![12 tools](https://img.shields.io/badge/tools-12-22C55E.svg)](https://github.com/RosenAdvertising/cloudtalk-mcp)
[![MCP](https://img.shields.io/badge/MCP-compatible-7C3AED.svg)](https://modelcontextprotocol.io)
[![CloudTalk](https://img.shields.io/badge/CloudTalk-API-6C4FE8.svg)](https://www.cloudtalk.io)

MCP server for CloudTalk — call center management, agents, contacts, and analytics for law firms.

## Tools (12)

| Tool                  | Description                                         |
| --------------------- | --------------------------------------------------- |
| `who_am_i`            | Return identity of the connected CloudTalk account  |
| `list_agents`         | List all agents                                     |
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

Secrets are saved under the service name `cloudtalk-mcp`. Nothing is written to
disk in clear text.

**File fallback.** On a host with no keyring backend (e.g. a headless Linux box
without Secret Service), or if you set `CLOUDTALK_MCP_USE_KEYRING=0`, credentials
fall back to a `~/.cloudtalk-mcp/.env` file with `0600` permissions.

**Read order.** Credentials resolve in the order OS keyring → process environment
→ `.env` file. So a rotated secret in the keyring always wins, and a
`CLOUDTALK_KEY_ID` / `CLOUDTALK_KEY_SECRET` exported in your shell overrides the
file fallback without touching the keyring.

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

## Auth

HTTP Basic Auth using `base64(KEY_ID:KEY_SECRET)`. All API paths use CloudTalk's resource-verb convention (`/agents/index.json`, `/contacts/add.json`) — handled internally by the client.

## API notes

- **GET** — list/show operations
- **PUT** — create operations (`/contacts/add.json`)
- **POST** — update operations (`/contacts/edit/{id}.json`)
- **DELETE** — delete operations
- `get_call` routes to the analytics subdomain (`analytics-api.cloudtalk.io`)
- Contact phone/email are stored as sub-object arrays (`ContactNumber`, `ContactEmail`) per the CloudTalk API schema
