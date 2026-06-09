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

Credentials are saved to `~/.cloudtalk-mcp/.env`. Find your Key ID and Key Secret at **app.cloudtalk.io → Settings → API**.

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

<!-- mrfixcode gate demo: clean patch bump -->
