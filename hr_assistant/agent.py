"""
HR Recruiting Assistant – ADK implementation
--------------------------------------------
An LLM-orchestrated agent that can:

1. login_user(username, password)             -> token
2. search_job_candidates(job_title, skills)   -> list[dict]
3. save_candidate_record(name, title, skills) -> status

All three tools call existing JSON-RPC micro-services.  Service
end-points are resolved dynamically via the a2a_registry if its URL is
set, otherwise they fall back to the fixed URLs in .env / config.py.
"""
from __future__ import annotations

import asyncio
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from google.adk.tools import ToolContext

import httpx
from google.adk.agents import Agent
from config import (
    AUTH_AGENT_URL,
    WEBSERVICE_AGENT_URL,
    DBSERVICE_AGENT_URL,
    A2A_REGISTRY_URL,
    VERTEX_MODEL,
    VERTEX_PROJECT_ID,
    VERTEX_LOCATION,
    ADK_PORT,
    ADK_HOST
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hr_assistant.agent")


# ---------------------------------------------------------------------
# 0.  Helper: JSON-RPC 2.0 call
# ---------------------------------------------------------------------
async def make_rpc_call(agent_url: str, method: str, params: Dict[str, Any], request_id: int = 1) -> Dict[str, Any]:
    """
    Makes an asynchronous JSON-RPC 2.0 call to a specified agent URL.
    (Includes more detailed error handling than the minimal sample)
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Making RPC call to {agent_url} - Method: {method}, Params: {params}")
            response = await client.post(agent_url, json=payload)
            response.raise_for_status() # Raise exception for 4xx/5xx responses

            data = response.json()
            logger.debug(f"RPC Response from {agent_url} for {method}: {data}")

            if "error" in data:
                error_details = data["error"]
                logger.error(f"RPC Error from {agent_url} calling {method}: {error_details}")
                # Raise a specific exception the calling tool can potentially catch or log
                raise RuntimeError(f"Agent Error: {error_details.get('message', 'Unknown RPC error')} (Code: {error_details.get('code', 'N/A')})")
            elif "result" in data:
                logger.info(f"RPC Success from {agent_url} for {method}.")
                return data["result"]
            else:
                logger.error(f"Invalid RPC response structure from {agent_url} for {method}: Missing 'result' or 'error'. Response: {data}")
                raise ValueError("Invalid JSON-RPC response structure received.")

        except httpx.TimeoutException as e:
            logger.exception(f"Timeout during RPC call to {agent_url} for method {method}")
            raise TimeoutError(f"Timeout calling {method} at {agent_url}") from e
        except httpx.RequestError as e:
            logger.exception(f"Network error during RPC call to {agent_url} for method {method}: {e}")
            raise ConnectionError(f"Network error calling {method} at {agent_url}") from e
        except Exception as e:
             # Catch other potential errors (like JSON decoding, unexpected exceptions)
            logger.exception(f"Unexpected error during RPC call to {agent_url} for method {method}: {e}")
            # Re-raise if it's not one of the specific errors above
            if not isinstance(e, (RuntimeError, ValueError, TimeoutError, ConnectionError)):
                 raise Exception(f"Failed RPC call to {method} at {agent_url}") from e
            else:
                 raise # Re-raise the specific error

# ---------------------------------------------------------------------
# 1.  Optional dynamic service discovery via registry
# ---------------------------------------------------------------------
REGISTRY_URL = os.getenv("A2A_REGISTRY_URL", "http://a2a_registry:8000/a2a")

@lru_cache              # caches the lookup per agent name
async def resolve_url(agent_name: str) -> str:
    """Ask the a2a_registry for the runtime URL of `agent_name`."""
    card = await make_rpc_call(
        agent_url=REGISTRY_URL,
        method="get_agent",
        params={"name": agent_name},
    )
    if not card or "url" not in card:
        raise RuntimeError(f"Registry has no URL for {agent_name}")
    return card["url"]    


# ---------------------------------------------------------------------
# 2.  Tool functions (LLM will call these)
# ---------------------------------------------------------------------
async def login_user(username: str, password: str, tool_context: ToolContext) -> dict:
    """
    Authenticate with the auth_agent microservice.
    Returns {"status":"success","token":...} or {"status":"error","message":...}
    """
    # call the auth_agent.login JSON-RPC method
    result = await make_rpc_call(
        agent_url=AUTH_AGENT_URL,
        method="login",
        params={"username": username, "password": password}
    )

    if result.get("success"):
        token = result["token"]
        # store for later tools
        tool_context.state["auth_token"] = token
        return {"status": "success", "token": token}
    else:
        return {"status": "error", "message": result.get("error", "Login failed")} 

async def search_job_candidates(skill: str, location: str, tool_context: ToolContext) -> dict:
    """
    Query webservice_agent.search_candidates via JSON-RPC.
    Requires prior login (token in session state).
    Returns {"status":"success","candidates":[...]} or {"status":"error",...}
    """
    token = tool_context.state.get("auth_token")
    if not token:
        return {"status": "error", "message": "You must log in first."}

    # call webservice_agent.search_candidates
    candidates = await make_rpc_call(
        agent_url=WEBSERVICE_AGENT_URL,
        method="search_candidates",
        params={"title": skill, "skills": skill, "token": token}
    )

    # `candidates` should be a list if successful
    if isinstance(candidates, list):
        return {"status": "success", "candidates": candidates}
    else:
        return {"status": "error", "message": "Search failed or returned no results."}

async def save_candidate_record(candidate_id: str, tool_context: ToolContext) -> dict:
    """
    Send a JSON-RPC create_record to the dbservice_agent.
    Returns {"status":"success"} or {"status":"error",...}
    """
    token = tool_context.state.get("auth_token")
    if not token:
        return {"status": "error", "message": "You must log in first."}

    result = await make_rpc_call(
        agent_url=DBSERVICE_AGENT_URL,
        method="create_record",
        params={"id": candidate_id, "token": token}
    )

    if result.get("status") == "saved":
        return {"status": "success", "message": f"Candidate {candidate_id} saved."}
    else:
        return {"status": "error", "message": result.get("error", "Save failed.")}

# ---------------------------------------------------------------------
# 3.  Instantiate the Agent (global variable *agent*)
# ---------------------------------------------------------------------
vertex_cfg = {}
if VERTEX_PROJECT_ID:
    vertex_cfg["project"] = VERTEX_PROJECT_ID
if VERTEX_LOCATION:
    vertex_cfg["location"] = VERTEX_LOCATION

agent = Agent(
    name="HR_Recruiting_Assistant",
    description=(
        "You are an HR Recruiting Assistant. Your goal is to help users find and save job candidates. "
        "The typical workflow is: 1. Log in the user, 2. Search for candidates, 3. Save selected candidates.\n"
        "IMPORTANT: To log in, you MUST have the user's username and password. "
        "If the user asks to start the process or hasn't provided credentials, FIRST ask them for their username and password "
        "BEFORE attempting to call the login_user tool. \n"
        "Once login is successful (the login_user tool returns success and a token), then ask the user what job title and skills they want to search for. "
        "Use the search_job_candidates tool for this. \n"
        "After presenting the search results, if the user wants to save candidates, confirm which ones and use the save_candidate_record tool for each one. \n"
        "Remember to potentially pass the auth_token obtained from the login result to subsequent tool calls like search_job_candidates and save_candidate_record where the tool accepts it."
    ),
    model="gemini-1.5-flash-002",
    # model_config=vertex_cfg or None, # If using specific project/location
    tools=[login_user, search_job_candidates, save_candidate_record],
)

logger.info("✔ Agent initialised with %d tools", len(agent.tools))

# # ---------------------------------------------------------------------
# # 4.  CLI debug helper
# # ---------------------------------------------------------------------
# if __name__ == "__main__":
#     # Simple REPL to test the tools without the ADK web UI
#     async def _quick_test():
#         print(await login_user("admin", "secret"))
#     asyncio.run(_quick_test())
