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
# Entry point
# ---------------------------------------------------------------------------


def main():
    mcp.run()


if __name__ == "__main__":
    main()
