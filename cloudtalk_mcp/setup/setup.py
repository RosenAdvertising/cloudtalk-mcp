#!/usr/bin/env python3
"""Interactive setup — prompts for CloudTalk API credentials and saves them."""

import os
import sys

from cloudtalk_mcp import credentials


def main():
    print("CloudTalk MCP Setup")
    print("=" * 40)
    print("Find your credentials at: app.cloudtalk.io → Settings → API")
    print()

    key_id = input("Key ID: ").strip()
    if not key_id:
        print("Error: Key ID cannot be empty.", file=sys.stderr)
        sys.exit(1)

    key_secret = input("Key Secret: ").strip()
    if not key_secret:
        print("Error: Key Secret cannot be empty.", file=sys.stderr)
        sys.exit(1)

    backend = credentials.set_secret("CLOUDTALK_KEY_ID", key_id)
    credentials.set_secret("CLOUDTALK_KEY_SECRET", key_secret)

    # Make the just-entered values visible to the in-process verify() below.
    os.environ["CLOUDTALK_KEY_ID"] = key_id
    os.environ["CLOUDTALK_KEY_SECRET"] = key_secret

    print()
    if backend == "keyring":
        print(f"Credentials saved to the OS keyring ({credentials.storage_backend()}).")
    else:
        print(f"Credentials saved to {credentials.ENV_FILE} (0600).")
    print()

    # Verify immediately after saving
    try:
        from cloudtalk_mcp.setup.verify import run_verify

        run_verify()
    except Exception as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        print("Check your credentials and try again.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
