# cloudtalk-mcp

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F59E0B.svg)](https://opensource.org/licenses/MIT)
[![15 tools](https://img.shields.io/badge/tools-15-22C55E.svg)](https://github.com/RosenAdvertising/cloudtalk-mcp)
[![MCP](https://img.shields.io/badge/MCP-compatible-7C3AED.svg)](https://modelcontextprotocol.io)
[![CloudTalk](https://img.shields.io/badge/CloudTalk-API-6C4FE8.svg)](https://www.cloudtalk.io)

MCP server for CloudTalk — call center management, agents, contacts, and analytics for law firms.

## Tools (15)

| Tool | Description |
|---|---|
| `get_account` | Account info and settings |
| `list_agents` | List all agents |
| `get_agent` | Get a specific agent |
| `list_calls` | List calls with date/status filters |
| `get_call` | Get call details including recording |
| `initiate_call` | Place an outbound call |
| `list_contacts` | List/search contacts |
| `get_contact` | Get a specific contact |
| `create_contact` | Create a new contact |
| `update_contact` | Update contact fields |
| `delete_contact` | Delete a contact |
| `list_numbers` | List account phone numbers |
| `get_number` | Get a specific number |
| `get_call_statistics` | Call volume and performance metrics |
| `get_agent_statistics` | Per-agent performance metrics |

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

HTTP Basic Auth using `base64(KEY_ID:KEY_SECRET)`. All endpoints use the `.json` suffix (handled internally — tools do not require it).
