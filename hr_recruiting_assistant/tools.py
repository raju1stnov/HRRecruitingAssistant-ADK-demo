import os, requests
from google.adk.tools import FunctionTool  # 👈 new

AUTH_URL = os.getenv("AUTH_AGENT_URL", "http://auth_agent:8000/a2a")
WEB_URL  = os.getenv("WEBSERVICE_AGENT_URL", "http://webservice_agent:8000/a2a")
DB_URL   = os.getenv("DBSERVICE_AGENT_URL", "http://dbservice_agent:8000/a2a")

def _rpc(url, method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data = requests.post(url, json=payload, timeout=15).json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

@FunctionTool                 # 👈 instead of @tool
def login_user(username: str, password: str) -> str:
    """Authenticate via auth_agent and return JWT token."""
    res = _rpc(AUTH_URL, "login", {"username": username, "password": password})
    if not res.get("success"):
        raise RuntimeError(res.get("error", "login failed"))
    return res["token"]

@FunctionTool
def search_for_candidates(title: str, skills: str) -> list:
    """Search candidates via webservice_agent."""
    return _rpc(WEB_URL, "search_candidates", {"title": title, "skills": skills})

@FunctionTool
def save_candidate_record(name: str, title: str, skills: list) -> str:
    """Persist candidate via dbservice_agent."""
    res = _rpc(DB_URL, "create_record",
               {"name": name, "title": title, "skills": skills})
    if res.get("status") != "saved":
        raise RuntimeError(res.get("error", "save failed"))
    return f"Candidate '{name}' saved."
