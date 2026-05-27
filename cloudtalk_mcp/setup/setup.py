#!/usr/bin/env python3
"""Interactive setup — prompts for CloudTalk API credentials and saves them."""

import sys
from pathlib import Path


CONFIG_DIR = Path.home() / ".cloudtalk-mcp"
ENV_FILE = CONFIG_DIR / ".env"


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

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    env_content = f"CLOUDTALK_KEY_ID={key_id}\n" f"CLOUDTALK_KEY_SECRET={key_secret}\n"
    ENV_FILE.write_text(env_content)
    ENV_FILE.chmod(0o600)

    print()
    print(f"Credentials saved to {ENV_FILE}")
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
