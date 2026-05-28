#!/usr/bin/env python3
import base64
import os
import sys
import time
from typing import Any

import requests
from pathlib import Path

BASE_URL = "https://my.cloudtalk.io/api"
ANALYTICS_BASE_URL = "https://analytics-api.cloudtalk.io/api"
CONFIG_DIR = Path.home() / ".cloudtalk-mcp"


def _load_env():
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()


def _retry_after_seconds(resp, default=10):
    try:
        return int(resp.headers.get("Retry-After", default))
    except (TypeError, ValueError):
        return default


def _json_response(resp):
    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(
            f"CloudTalk API returned non-JSON ({resp.status_code}): {resp.text[:200]}"
        )


class CloudTalkClient:
    def __init__(self):
        key_id = os.environ.get("CLOUDTALK_KEY_ID", "")
        key_secret = os.environ.get("CLOUDTALK_KEY_SECRET", "")
        if not key_id or not key_secret:
            raise RuntimeError(
                "CloudTalk credentials not found. Run: cloudtalk-mcp-setup"
            )
        credentials = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        """Build a my.cloudtalk.io API URL. Appends .json if not already present."""
        clean = path.lstrip("/")
        if not clean.endswith(".json"):
            clean = clean + ".json"
        return f"{BASE_URL}/{clean}"

    def _analytics_url(self, path: str) -> str:
        """Build an analytics-api.cloudtalk.io URL (no .json suffix)."""
        return f"{ANALYTICS_BASE_URL}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        _rate_retries: int = 0,
    ) -> Any:
        resp = self.session.request(method, url, params=params, json=json_body)
        if resp.status_code == 401:
            raise RuntimeError(
                "CloudTalk credentials invalid. Run: cloudtalk-mcp-setup"
            )
        if resp.status_code == 429 and _rate_retries < 3:
            wait = _retry_after_seconds(resp)
            print(f"Rate limited. Waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
            return self._request(
                method,
                url,
                params=params,
                json_body=json_body,
                _rate_retries=_rate_retries + 1,
            )
        if resp.status_code == 204:
            return {"success": True}
        if not resp.ok:
            raise RuntimeError(
                f"CloudTalk API error {resp.status_code}: {resp.text[:400]}"
            )
        return _json_response(resp)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", self._url(path), params=params)

    def post(self, path: str, body: Any = None) -> Any:
        return self._request("POST", self._url(path), json_body=body)

    def put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", self._url(path), json_body=body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", self._url(path))

    # --- Identity ---

    def who_am_i(self) -> dict:
        """Return account identity by pulling the first agent from the account."""
        resp = self.list_agents(page=1, limit=1)
        data = resp.get("responseData", resp)
        items = data.get("data", [])
        agent = items[0].get("Agent", items[0]) if items else {}
        return {
            "account": "CloudTalk",
            "agent_email": agent.get("email", "unknown"),
            "agent_name": f"{agent.get('firstname', '')} {agent.get('lastname', '')}".strip(),
            "agent_id": agent.get("id"),
            "total_agents": data.get("itemsCount"),
        }

    # --- Agents ---

    def list_agents(self, page=1, limit=25):
        return self.get("/agents/index", params={"page": page, "limit": limit})

    # --- Calls ---

    def list_calls(self, page=1, limit=25, date_from="", date_to="", status=""):
        params: dict[str, Any] = {"page": page, "limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status
        return self.get("/calls/index", params=params)

    def get_call(self, call_id):
        """Get comprehensive call details from the analytics API."""
        url = self._analytics_url(f"calls/{call_id}")
        return self._request("GET", url)

    def initiate_call(self, agent_id, callee_number):
        body = {"agent_id": agent_id, "callee_number": callee_number}
        return self.post("/calls/create", body=body)

    # --- Contacts ---

    def list_contacts(self, page=1, limit=25, query=""):
        params: dict[str, Any] = {"page": page, "limit": limit}
        if query:
            params["keyword"] = query
        return self.get("/contacts/index", params=params)

    def get_contact(self, contact_id):
        return self.get(f"/contacts/show/{contact_id}")

    def create_contact(self, first_name, last_name="", phone="", email=""):
        # API requires a single `name` field; phone/email are array sub-objects.
        name = f"{first_name} {last_name}".strip() if last_name else first_name
        body: dict = {"name": name}
        if phone:
            body["ContactNumber"] = [{"public_number": phone}]
        if email:
            body["ContactEmail"] = [{"email": email}]
        return self.put("/contacts/add", body=body)

    def update_contact(
        self, contact_id, first_name="", last_name="", phone="", email=""
    ):
        body: dict = {}
        # name is required by the API; build from whichever name parts were given.
        name_parts = [p for p in [first_name, last_name] if p]
        if name_parts:
            body["name"] = " ".join(name_parts)
        if phone:
            body["ContactNumber"] = [{"public_number": phone}]
        if email:
            body["ContactEmail"] = [{"email": email}]
        if not body:
            return {"success": True, "message": "No fields to update"}
        return self.post(f"/contacts/edit/{contact_id}", body=body)

    def delete_contact(self, contact_id):
        return self.delete(f"/contacts/delete/{contact_id}")

    # --- Numbers ---

    def list_numbers(self, page=1, limit=25):
        return self.get("/numbers/index", params={"page": page, "limit": limit})

    # --- Statistics ---

    def get_call_statistics(self):
        """Return real-time group statistics (answered/unanswered calls, abandon rate, etc.)."""
        return self.get("/statistics/realtime/groups")
