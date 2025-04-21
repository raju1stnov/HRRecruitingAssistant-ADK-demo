"""
ADK tool wrappers that forward JSON‑RPC 2.0 calls to the live
platform services running in platform‑setup_repo.
"""

import os, json, requests
from google.adk.tools import tool

AUTH_URL = os.getenv("AUTH_AGENT_URL", "http://auth_agent:8000/a2a")
WEB_URL  = os.getenv("WEBSERVICE_AGENT_URL", "http://webservice_agent:8000/a2a")
DB_URL   = os.getenv("DBSERVICE_AGENT_URL", "http://dbservice_agent:8000/a2a")

def _json_rpc(url: str, method: str, params: dict, rpc_id: int = 1):
    payload = {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params}
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"{url} returned error: {data['error']}")
    return data.get("result")

# ---------------- ADK tools ----------------
@tool
def login_user(username: str, password: str) -> str:
    """Authenticate the user via auth_agent. Returns a JWT token on success."""
    result = _json_rpc(AUTH_URL, "login", {"username": username, "password": password})
    if result.get("success"):
        return result["token"]
    raise RuntimeError(result.get("error", "login failed"))

@tool
def search_for_candidates(title: str, skills: str) -> list:
    """Search for candidates using webservice_agent."""
    return _json_rpc(WEB_URL, "search_candidates",
                     {"title": title, "skills": skills})

@tool
def save_candidate_record(name: str, title: str, skills: list) -> str:
    """Save a candidate record in dbservice_agent and return status."""
    out = _json_rpc(DB_URL, "create_record",
                    {"name": name, "title": title, "skills": skills})
    if out.get("status") != "saved":
        raise RuntimeError(out.get("error", "save failed"))
    return f"Candidate '{name}' saved."