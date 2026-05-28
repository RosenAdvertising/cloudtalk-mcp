#!/usr/bin/env python3
"""
Phase 0 data seed for the CloudTalk developer account.

Creates 3 law-firm-representative contacts tagged [SEED].
These give smoke and write tiers a populated account to work against.

Note: CloudTalk agents and phone numbers are provisioned via the CloudTalk
dashboard — they cannot be created via the REST API. Only contacts are
writable via API and are seeded here.

Prerequisites:
  1. Add CloudTalk credentials to ~/.cloudtalk-mcp/.env:
       CLOUDTALK_KEY_ID=your_key_id
       CLOUDTALK_KEY_SECRET=your_key_secret

  2. Run the seed:
       python tests/seed_data.py

Usage:
    python tests/seed_data.py            # create seed contacts
    python tests/seed_data.py --reset    # wipe existing seed contacts, then re-create
    python tests/seed_data.py --wipe     # wipe only (no re-create)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cloudtalk_mcp.client import CloudTalkClient

SEED_TAG = "[SEED]"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _extract_id(resp: dict, label: str) -> str | None:
    """Extract contact ID from a CloudTalk create_contact response; print status."""
    # CloudTalk wraps results in responseData.data or returns id directly
    contact_id = None
    if isinstance(resp.get("responseData"), dict):
        data = resp["responseData"].get("data") or resp["responseData"]
        contact_id = data.get("id") or data.get("contact_id")
    if not contact_id:
        contact_id = resp.get("id") or resp.get("contact_id")
    if not contact_id:
        err = resp.get("message") or resp.get("error") or str(resp)[:200]
        print(f"  ✗  {label} — {err}", file=sys.stderr)
        return None
    print(f"  ✓  {label}  (id={contact_id})")
    return str(contact_id)


def _list_all_contacts(client: CloudTalkClient) -> list[dict]:
    """Page through /contacts and return every contact."""
    contacts: list[dict] = []
    page = 1
    while True:
        resp = client.list_contacts(page=page, limit=100)
        # CloudTalk wraps list results in responseData
        batch: list = []
        if isinstance(resp.get("responseData"), dict):
            data = resp["responseData"].get("data") or []
            if isinstance(data, list):
                batch = data
        elif isinstance(resp.get("data"), list):
            batch = resp["data"]
        contacts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return contacts


# ── Seed ──────────────────────────────────────────────────────────────────────


def seed(client: CloudTalkClient) -> list[str]:
    """Create 3 law-firm contacts tagged [SEED]. Returns list of created IDs."""
    created: list[str] = []
    print("\n── Contacts ─────────────────────────────────────────")

    contacts_to_create = [
        dict(
            first_name=f"{SEED_TAG} Maria",
            last_name="Ramirez",
            phone="+12025550101",
            email="seed-maria.ramirez@example.com",
        ),
        dict(
            first_name=f"{SEED_TAG} James",
            last_name="Chen",
            phone="+12025550102",
            email="seed-james.chen@example.com",
        ),
        dict(
            first_name=f"{SEED_TAG} Aisha",
            last_name="Thompson",
            phone="+12025550103",
            email="seed-aisha.thompson@example.com",
        ),
    ]

    for cfg in contacts_to_create:
        label = f"{cfg['first_name']} {cfg['last_name']}"
        try:
            resp = client.create_contact(**cfg)
            contact_id = _extract_id(resp, label)
            if contact_id:
                created.append(contact_id)
        except Exception as exc:
            print(f"  ✗  {label} — {exc}", file=sys.stderr)

    return created


# ── Wipe ──────────────────────────────────────────────────────────────────────


def wipe(client: CloudTalkClient) -> None:
    """Delete all contacts whose first_name contains [SEED]."""
    print(f"\nWiping '{SEED_TAG}' seed contacts...")
    contacts = _list_all_contacts(client)
    deleted = 0
    for contact in contacts:
        first_name = contact.get("first_name") or contact.get("name") or ""
        contact_id = str(contact.get("id") or contact.get("contact_id") or "")
        if SEED_TAG in first_name and contact_id:
            try:
                client.delete_contact(int(contact_id))
                print(f"  deleted contact {contact_id} ({first_name})")
                deleted += 1
            except Exception as exc:
                print(
                    f"  ✗  failed to delete {contact_id} ({first_name}): {exc}",
                    file=sys.stderr,
                )
    if deleted == 0:
        print("  (no seed contacts found)")
    print("Wipe complete.\n")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the CloudTalk developer account with representative contacts."
    )
    parser.add_argument(
        "--reset", action="store_true", help="Wipe seed contacts then re-create"
    )
    parser.add_argument(
        "--wipe", action="store_true", help="Wipe seed contacts only (no re-create)"
    )
    args = parser.parse_args()

    try:
        client = CloudTalkClient()
    except RuntimeError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Identity check — confirm which account we're seeding.
    try:
        client.list_agents(page=1, limit=1)
        print("Authenticated — CloudTalk account")
    except Exception as exc:
        print(f"Auth check failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.wipe or args.reset:
        wipe(client)
    if not args.wipe:
        created = seed(client)
        print(f"\nSeed complete — {len(created)} contact(s) created.")
        print("\nNext step:")
        print(
            "  SEED_CONFIRMED=1 mcp-test-kit run --tier smoke --config tests/config.py"
        )


if __name__ == "__main__":
    main()
