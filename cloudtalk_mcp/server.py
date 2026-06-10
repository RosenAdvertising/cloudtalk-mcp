#!/usr/bin/env python3
"""CloudTalk MCP server — 12 tools for call center management."""

import json

from mcp.server.fastmcp import FastMCP
from .client import CloudTalkClient

mcp = FastMCP("cloudtalk")


def _client() -> CloudTalkClient:
    return CloudTalkClient()


# ---------------------------------------------------------------------------
# Identity (required by mcp-test-kit write gate)
# ---------------------------------------------------------------------------


@mcp.tool()
def who_am_i() -> str:
    """Return the identity of the connected CloudTalk account."""
    return json.dumps(_client().who_am_i(), indent=2)


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@mcp.tool()
def list_agents(page: int = 1, limit: int = 25) -> dict:
    """List all agents in the CloudTalk account.

    Args:
        page: Page number (default 1).
        limit: Results per page (default 25, max 100).
    """
    return _client().list_agents(page=page, limit=limit)


# ---------------------------------------------------------------------------
# Calls
# ---------------------------------------------------------------------------


@mcp.tool()
def list_calls(
    page: int = 1,
    limit: int = 25,
    date_from: str = "",
    date_to: str = "",
    status: str = "",
) -> dict:
    """List calls with optional filters.

    Args:
        page: Page number (default 1).
        limit: Results per page (default 25).
        date_from: Filter start date, format YYYY-MM-DD (optional).
        date_to: Filter end date, format YYYY-MM-DD (optional).
        status: Filter by call status e.g. answered, missed, voicemail (optional).
    """
    return _client().list_calls(
        page=page, limit=limit, date_from=date_from, date_to=date_to, status=status
    )


@mcp.tool()
def get_call(call_id: int) -> dict:
    """Get comprehensive details for a specific call including recording, flow, and notes.

    Args:
        call_id: The call's numeric ID.
    """
    return _client().get_call(call_id)


@mcp.tool()
def initiate_call(agent_id: int, to_number: str) -> dict:
    """Create and initiate an outbound call from a CloudTalk agent.

    First rings the agent; once the agent answers, CloudTalk automatically
    connects them to the destination number.

    Args:
        agent_id: The agent who will make the call.
        to_number: Destination phone number in E.164 format (e.g. +12025551234).
    """
    return _client().initiate_call(agent_id=agent_id, callee_number=to_number)


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


@mcp.tool()
def list_contacts(page: int = 1, limit: int = 25, query: str = "") -> dict:
    """List contacts, optionally filtered by a keyword search.

    Args:
        page: Page number (default 1).
        limit: Results per page (default 25).
        query: Keyword to filter contacts by name, phone, or email (optional).
    """
    return _client().list_contacts(page=page, limit=limit, query=query)


@mcp.tool()
def get_contact(contact_id: int) -> dict:
    """Get details for a specific contact.

    Args:
        contact_id: The contact's numeric ID.
    """
    return _client().get_contact(contact_id)


@mcp.tool()
def create_contact(
    first_name: str,
    last_name: str = "",
    phone: str = "",
    email: str = "",
) -> dict:
    """Create a new contact in CloudTalk.

    Args:
        first_name: Contact's first name (required).
        last_name: Contact's last name (optional).
        phone: Phone number in E.164 format (optional).
        email: Email address (optional).
    """
    return _client().create_contact(
        first_name=first_name, last_name=last_name, phone=phone, email=email
    )


@mcp.tool()
def update_contact(
    contact_id: int,
    first_name: str = "",
    last_name: str = "",
    phone: str = "",
    email: str = "",
) -> dict:
    """Update an existing contact. Only fields provided will be updated.

    Args:
        contact_id: The contact's numeric ID.
        first_name: New first name (optional).
        last_name: New last name (optional).
        phone: New phone number in E.164 format (optional).
        email: New email address (optional).
    """
    return _client().update_contact(
        contact_id=contact_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
    )


@mcp.tool()
def delete_contact(contact_id: int) -> dict:
    """Delete a contact from CloudTalk.

    Args:
        contact_id: The contact's numeric ID.
    """
    return _client().delete_contact(contact_id)


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------


@mcp.tool()
def list_numbers(page: int = 1, limit: int = 25) -> dict:
    """List all phone numbers assigned to the CloudTalk account.

    Args:
        page: Page number (default 1).
        limit: Results per page (default 25).
    """
    return _client().list_numbers(page=page, limit=limit)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@mcp.tool()
def get_call_statistics() -> dict:
    """Get real-time call group statistics.

    Returns live data for each call group: answered/unanswered calls today,
    abandon rate, average waiting time, average call duration, and agent counts.
    """
    return _client().get_call_statistics()


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("cloudtalk://numbers", mime_type="application/json")
def numbers_resource() -> str:
    """All phone numbers assigned to this CloudTalk account — read-only reference data."""
    return json.dumps(_client().list_numbers(limit=100), indent=2)


@mcp.resource("cloudtalk://agents", mime_type="application/json")
def agents_resource() -> str:
    """All agents in this CloudTalk account — read-only reference data."""
    return json.dumps(_client().list_agents(limit=100), indent=2)


@mcp.resource("cloudtalk://security-notes", mime_type="text/markdown")
def security_notes_resource() -> str:
    """Security posture for cloudtalk-mcp.

    ## Credentials
    - **CLOUDTALK_API_KEY**: CloudTalk REST API key (Bearer token).
    - Resolution order: OS keyring (macOS Keychain / libsecret) → process env →
      `~/.cloudtalk-mcp/.env` (chmod 0600 fallback). Set via `cloudtalk-mcp-setup`.

    ## Tool classification
    - **Read-only (safe):** who_am_i, list_agents, list_calls, get_call,
      list_contacts, get_contact, list_numbers, get_call_statistics.
    - **Write / side-effect:** initiate_call, create_contact, update_contact,
      delete_contact.

    ## Data sensitivity
    Call recordings and contact data may contain attorney-client privileged
    communications. Handle under legal-privilege standards; do not store or
    transmit call content outside firm-approved systems.
    """
    return security_notes_resource.__doc__ or ""


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def missed_call_review() -> str:
    """Review missed calls for the day and recommend follow-up actions."""
    return """You are a legal intake coordinator reviewing today's missed calls.

1. Call list_calls with status='missed' to retrieve today's missed calls.
2. For each missed call: call get_call to get caller details and any notes.
3. Search list_contacts for matching phone numbers to identify known contacts.
4. For unknown callers: flag as potential new client intake.
5. Call get_call_statistics to see the overall missed-call rate for the day.
6. Output a prioritized action list: Caller | Known Contact | Time | Recommended Action.
7. Flag callers who have called more than once today as high-priority."""


@mcp.prompt()
def call_quality_review(call_id: str) -> str:
    """Review call quality and content for a specific call."""
    return f"""Review CloudTalk call {call_id} for quality and follow-up requirements:

1. Call get_call({call_id}) — capture agent, duration, status, direction, and any notes.
2. Identify the call type: new inquiry, existing client, or internal.
3. If the call was answered: assess duration relative to typical intake length.
4. If call was missed or abandoned: check if a contact record exists via list_contacts.
5. Determine next action: callback required, contact record to create, escalation needed.
6. Output: Call summary | Agent | Outcome | Next Action | Priority."""


@mcp.prompt()
def agent_performance_brief() -> str:
    """Call volume and performance brief for all agents today."""
    return """Generate a performance brief for all CloudTalk agents:

1. Call list_agents to get the full agent roster.
2. Call get_call_statistics to get current live statistics by call group.
3. Call list_calls filtered to today to see answered vs missed by agent.
4. For each agent: count calls handled, calculate average duration from call records.
5. Cross-reference against get_call_statistics abandon rate and wait times.
6. Output a table: Agent | Calls Handled | Missed | Avg Duration | Notes.
7. Flag agents with zero calls today as potentially offline or unavailable."""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    mcp.run()


if __name__ == "__main__":
    main()
