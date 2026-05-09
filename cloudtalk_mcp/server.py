#!/usr/bin/env python3
"""CloudTalk MCP server — 15 tools for call center management."""

from mcp.server.fastmcp import FastMCP
from .client import CloudTalkClient

mcp = FastMCP("cloudtalk")


def _client() -> CloudTalkClient:
    return CloudTalkClient()


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


@mcp.tool()
def get_account() -> dict:
    """Get CloudTalk account information and settings."""
    return _client().get_account()


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


@mcp.tool()
def get_agent(agent_id: int) -> dict:
    """Get details for a specific agent.

    Args:
        agent_id: The agent's numeric ID.
    """
    return _client().get_agent(agent_id)


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
    """Get details for a specific call including recording and notes.

    Args:
        call_id: The call's numeric ID.
    """
    return _client().get_call(call_id)


@mcp.tool()
def initiate_call(agent_id: int, to_number: str, caller_id: str = "") -> dict:
    """Initiate an outbound call from a CloudTalk agent.

    Args:
        agent_id: The agent who will make the call.
        to_number: Destination phone number in E.164 format (e.g. +12025551234).
        caller_id: Caller ID number to display (optional — uses account default if omitted).
    """
    return _client().initiate_call(
        agent_id=agent_id, to_number=to_number, caller_id=caller_id
    )


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


@mcp.tool()
def list_contacts(page: int = 1, limit: int = 25, query: str = "") -> dict:
    """List contacts, optionally filtered by a search query.

    Args:
        page: Page number (default 1).
        limit: Results per page (default 25).
        query: Search string to filter contacts by name, phone, or email (optional).
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


@mcp.tool()
def get_number(number_id: int) -> dict:
    """Get details for a specific phone number.

    Args:
        number_id: The number's numeric ID.
    """
    return _client().get_number(number_id)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@mcp.tool()
def get_call_statistics(
    date_from: str = "",
    date_to: str = "",
    agent_id: int = 0,
) -> dict:
    """Get call statistics (volume, duration, missed rate, etc.).

    Args:
        date_from: Start date for the report, format YYYY-MM-DD (optional).
        date_to: End date for the report, format YYYY-MM-DD (optional).
        agent_id: Filter statistics for a specific agent ID (optional, 0 = all agents).
    """
    return _client().get_call_statistics(
        date_from=date_from, date_to=date_to, agent_id=agent_id
    )


@mcp.tool()
def get_agent_statistics(
    date_from: str = "",
    date_to: str = "",
    agent_id: int = 0,
) -> dict:
    """Get per-agent performance statistics (calls handled, talk time, availability, etc.).

    Args:
        date_from: Start date for the report, format YYYY-MM-DD (optional).
        date_to: End date for the report, format YYYY-MM-DD (optional).
        agent_id: Filter statistics for a specific agent ID (optional, 0 = all agents).
    """
    return _client().get_agent_statistics(
        date_from=date_from, date_to=date_to, agent_id=agent_id
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    mcp.run()


if __name__ == "__main__":
    main()
