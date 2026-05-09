#!/usr/bin/env python3
"""Verify CloudTalk credentials by calling get_account()."""

import sys
from cloudtalk_mcp.client import CloudTalkClient


def run_verify():
    client = CloudTalkClient()
    result = client.get_account()
    print("Connection successful.")
    if isinstance(result, dict):
        name = result.get("name") or result.get("account_name") or result.get("company")
        if name:
            print(f"Account: {name}")
    return result


def main():
    try:
        run_verify()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
