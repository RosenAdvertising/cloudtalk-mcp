# cloudtalk-mcp

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
