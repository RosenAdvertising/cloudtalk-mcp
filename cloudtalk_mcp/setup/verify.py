#!/usr/bin/env python3
"""Verify CloudTalk credentials by calling who_am_i()."""

import sys
from cloudtalk_mcp.client import CloudTalkClient


def run_verify():
    client = CloudTalkClient()
    result = client.who_am_i()
    print("Connection successful.")
    return result


def main():
    try:
        run_verify()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("Unexpected error during verification.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
