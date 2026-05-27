#!/usr/bin/env python3
import base64
import os
import sys
import time
import requests
from pathlib import Path

BASE_URL = "https://my.cloudtalk.io/api"
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

    def _url(self, path):
        clean = path.lstrip("/")
        if not clean.endswith(".json"):
            clean = clean + ".json"
        return f"{BASE_URL}/{clean}"

    def _request(self, method, path, params=None, json_body=None, _rate_retries=0):
        url = self._url(path)
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
                path,
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

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, body=None):
        return self._request("POST", path, json_body=body)

    def put(self, path, body=None):
        return self._request("PUT", path, json_body=body)

    def delete(self, path):
        return self._request("DELETE", path)

    # --- Account ---

    def get_account(self):
        return self.get("/accounts")

    # --- Agents ---

    def list_agents(self, page=1, limit=25):
        return self.get("/agents", params={"page": page, "limit": limit})

    def get_agent(self, agent_id):
        return self.get(f"/agents/{agent_id}")

    # --- Calls ---

    def list_calls(self, page=1, limit=25, date_from="", date_to="", status=""):
        params = {"page": page, "limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status
        return self.get("/calls", params=params)

    def get_call(self, call_id):
        return self.get(f"/calls/{call_id}")

    def initiate_call(self, agent_id, to_number, caller_id=""):
        body = {"agent_id": agent_id, "to": to_number}
        if caller_id:
            body["caller_id"] = caller_id
        return self.post("/calls", body=body)

    # --- Contacts ---

    def list_contacts(self, page=1, limit=25, query=""):
        params = {"page": page, "limit": limit}
        if query:
            params["search"] = query
        return self.get("/contacts", params=params)

    def get_contact(self, contact_id):
        return self.get(f"/contacts/{contact_id}")

    def create_contact(self, first_name, last_name="", phone="", email=""):
        body = {"first_name": first_name}
        if last_name:
            body["last_name"] = last_name
        if phone:
            body["phone"] = phone
        if email:
            body["email"] = email
        return self.post("/contacts", body=body)

    def update_contact(
        self, contact_id, first_name="", last_name="", phone="", email=""
    ):
        body = {}
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if phone:
            body["phone"] = phone
        if email:
            body["email"] = email
        return self.put(f"/contacts/{contact_id}", body=body)

    def delete_contact(self, contact_id):
        return self.delete(f"/contacts/{contact_id}")

    # --- Numbers ---

    def list_numbers(self, page=1, limit=25):
        return self.get("/numbers", params={"page": page, "limit": limit})

    def get_number(self, number_id):
        return self.get(f"/numbers/{number_id}")

    # --- Statistics ---

    def get_call_statistics(self, date_from="", date_to="", agent_id=0):
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if agent_id:
            params["agent_id"] = agent_id
        return self.get("/statistics/calls", params=params if params else None)

    def get_agent_statistics(self, date_from="", date_to="", agent_id=0):
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if agent_id:
            params["agent_id"] = agent_id
        return self.get("/statistics/agents", params=params if params else None)
