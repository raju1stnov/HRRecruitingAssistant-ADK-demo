"""
Tools for the HR Recruiting Assistant (ADK).
Each tool is a google.adk.tools.FunctionTool that wraps a plain Python
function.  The wrapped functions perform synchronous JSON‑RPC calls
to your Docker‑based platform services.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx
from google.adk.tools import FunctionTool

from . import config

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper – generic JSON‑RPC 2.0 call
# ----------------------------------------------------------------------
def _a2a_call(agent_url: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": config.JSON_RPC_REQUEST_ID,
               "method": method, "params": params}
    try:
        r = httpx.post(agent_url, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.error("A2A error contacting %s – %s", agent_url, exc)
        return {"error": str(exc)}

    return data.get("result", {}) if "error" not in data else {"error": data["error"].get("message", "unknown")}

# ----------------------------------------------------------------------
# Tool 1 – login_user
# ----------------------------------------------------------------------
def login_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticates the user and returns an auth token.

    Args:
        username: Login name.
        password: Password (not echoed back).

    Returns:
        { "success": bool, "token": str | None, "error": str | None }
    """
    res = _a2a_call(config.AUTH_AGENT_URL, "login",
                    {"username": username, "password": password})

    if "error" in res:
        return {"success": False, "token": None, "error": res["error"]}

    return {
        "success": bool(res.get("success")),
        "token": res.get("token"),
        "error": res.get("error"),
    }

login_user_tool = FunctionTool(func=login_user)

# ----------------------------------------------------------------------
# Tool 2 – search_for_candidates
# ----------------------------------------------------------------------
def search_for_candidates(title: str, skills: str) -> Dict[str, Any]:
    """
    Finds candidate profiles matching a job title and skills.

    Args:
        title: Job title to search for.
        skills: Comma‑separated skill list.

    Returns:
        { "candidates": list[dict], "error": str | None }
    """
    res = _a2a_call(config.WEBSERVICE_AGENT_URL, "search_candidates",
                    {"title": title, "skills": skills})

    if "error" in res:
        return {"candidates": [], "error": res["error"]}

    return {"candidates": res if isinstance(res, list) else [], "error": None}

search_candidates_tool = FunctionTool(func=search_for_candidates)

# ----------------------------------------------------------------------
# Tool 3 – save_candidate_record
# ----------------------------------------------------------------------
def save_candidate_record(name: str, title: str, skills: List[str]) -> Dict[str, Any]:
    """
    Persists a single candidate to the DB service.

    Args:
        name: Candidate name.
        title: Candidate title.
        skills: List of skills.

    Returns:
        { "status": "saved" | "error", "name": str, "error": str | None }
    """
    res = _a2a_call(config.DBSERVICE_AGENT_URL, "create_record",
                    {"name": name, "title": title, "skills": skills})

    if "error" in res or res.get("status") != "saved":
        return {"status": "error", "name": name,
                "error": res.get("error", "DB error")}

    return {"status": "saved", "name": name, "error": None}

save_candidate_tool = FunctionTool(func=save_candidate_record)

# ----------------------------------------------------------------------
# Exported tuple – covariant, satisfies PyLance type checker
# ----------------------------------------------------------------------
hr_tools: tuple[FunctionTool, ...] = (
    login_user_tool,
    search_candidates_tool,
    save_candidate_tool,
)
