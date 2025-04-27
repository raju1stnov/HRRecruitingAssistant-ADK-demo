# main.py
import logging
import httpx
import sys
from typing import Any, Dict, List, Optional
import os
from functools import lru_cache

try:
    from google.adk.agents import Agent
    # We might need ToolContext if we want explicit context later
    # from google.adk.tools import ToolContext
except ImportError as e:
    logging.exception("Could not import google.adk.agents.Agent. Please ensure 'google-adk==0.3.0' is installed correctly and supports this structure.")
    logging.error(f"Import error details: {e}")
    sys.exit("Exiting: ADK library components not found.")

# Import configuration (Make sure these are loaded *before* Agent instantiation)
from config import (
    AUTH_AGENT_URL,
    WEBSERVICE_AGENT_URL,
    DBSERVICE_AGENT_URL,
    VERTEX_MODEL,
    VERTEX_PROJECT_ID, # Keep these for potential model_config
    VERTEX_LOCATION,  # Keep these for potential model_config
    ADK_HOST, # These might be less relevant if using `adk run/web`
    ADK_PORT  # These might be less relevant if using `adk run/web`
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

# --------------------------------------------------
# 1) Utility: JSON-RPC helper
# --------------------------------------------------
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

# --------------------------------------------------
# 2) Tool functions (plain functions are now Tools)
# --------------------------------------------------
async def login_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticates a user via the auth_agent using username and password.

    On success, returns a dictionary containing {'success': true, 'token': 'AUTH_TOKEN'}.
    On failure, returns a dictionary containing {'success': false, 'error': 'Reason...'}
    or raises an exception if the call fails completely.
    """
    logger.info(f"Executing tool: login_user for user: {username}")
    try:
        # Assuming make_rpc_call returns the 'result' payload directly
        result = await make_rpc_call(
            # agent_url=AUTH_AGENT_URL,
            agent_url = await resolve_url("auth_agent"),
            method="login",
            params={"username": username, "password": password}
        )
        # We simply return the result dict from the underlying agent
        logger.info(f"Login result for {username}: {result}")
        return result # ADK expects JSON-serializable return (dict is fine)
    except Exception as e:
        logger.error(f"Tool 'login_user' failed: {e}")
        # Return a failure dictionary consistent with expected success structure
        return {"success": False, "error": f"Login failed: {str(e)}"}          # ADK expects dict / JSON-serialisable

async def search_job_candidates(job_title: str, skills: str, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches for job candidates via the webservice_agent based on job title and comma-separated skills.
    Optionally accepts an auth_token (currently informational, not strictly used by underlying mock service).

    Returns a list of candidate dictionaries: [{'id':..., 'name':..., 'title':..., 'skills':[], 'experience':...}, ...].
    Returns an empty list or raises an exception on failure.
    """
    logger.info(f"Executing tool: search_job_candidates - Title: '{job_title}', Skills: '{skills}'")
    # Note: auth_token is accepted but not passed to this specific mock service call
    # The LLM *might* pass the token from login_user's result here if instructed.
    if auth_token:
        logger.info("Auth token provided (informational for this tool).")
    try:
        # Assuming make_rpc_call returns the 'result' payload directly, which should be a list
        candidates = await make_rpc_call(
            # agent_url=WEBSERVICE_AGENT_URL,
            agent_url = await resolve_url("webservice_agent"),
            method="search_candidates",
            params={"title": job_title, "skills": skills}
        )
        if isinstance(candidates, list):
            logger.info(f"Search successful, found {len(candidates)} candidates.")
            return candidates # Return the list directly
        else:
            logger.warning(f"Search returned non-list result: {type(candidates)}. Returning empty list.")
            return [] # Return empty list on unexpected result type
    except Exception as e:
        logger.error(f"Tool 'search_job_candidates' failed: {e}")
        # In case of failure, return an empty list or re-raise depending on desired behavior
        # raise # Option 1: Let the agent framework handle the exception
        return [] # Option 2: Return empty list to indicate no candidates found due to error

async def save_candidate_record(name: str, title: str, skills: List[str], auth_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Saves a single candidate record (name, title, skills list) via the dbservice_agent.
    Optionally accepts an auth_token (informational).

    Returns a dictionary indicating success or failure, e.g.,
    {'status': 'saved', 'name': '...', ...} or {'status': 'failed', 'error': '...'}.
    Raises an exception on complete call failure.
    """
    logger.info(f"Executing tool: save_candidate_record - Name: '{name}', Title: '{title}'")
    # Note: auth_token is accepted but not passed to this specific mock service call
    if auth_token:
        logger.info("Auth token provided (informational for this tool).")

    # Basic validation before calling
    if not name or not title or not skills:
         logger.warning("Save candidate called with missing name, title, or skills.")
         # Return a dict indicating failure, matching potential success structure
         return {"status": "failed", "error": "Missing required candidate information (name, title, skills list)."}
    if not isinstance(skills, list):
         logger.warning(f"Save candidate called with skills not as list: {type(skills)}")
         return {"status": "failed", "error": "Skills must be provided as a list."}

    try:
        # Assuming make_rpc_call returns the 'result' payload directly
        result = await make_rpc_call(
            # agent_url=DBSERVICE_AGENT_URL,
            agent_url = await resolve_url("dbservice_agent"),
            method="create_record",
            params={"name": name, "title": title, "skills": skills}
        )
        logger.info(f"Save candidate result for {name}: {result}")
        # Add a status field if the underlying service doesn't explicitly provide one
        if isinstance(result, dict) and "error" not in result:
             result.setdefault("status", "saved") # Assume saved if no error reported
        elif isinstance(result, dict) and "error" in result:
             result.setdefault("status", "failed")

        return result # Return the result dict
    except Exception as e:
        logger.error(f"Tool 'save_candidate_record' failed for {name}: {e}")
        # Return a failure dictionary
        return {"status": "failed", "error": f"Save operation failed: {str(e)}"}

# --------------------------------------------------
# 3) Define the Agent (this *is* your “root_agent”)
# --------------------------------------------------
logger.info("Defining ADK Agent instance...")

# Prepare optional model configuration
model_config_params = {}
if VERTEX_PROJECT_ID:
    model_config_params['project'] = VERTEX_PROJECT_ID
if VERTEX_LOCATION:
    model_config_params['location'] = VERTEX_LOCATION

# Instantiate the Agent
root_agent = Agent(
    name="HR Recruiting Assistant (ADK)",
    description=(
        "An assistant that helps HR users log in, search for job candidates "
        "using external services based on title and skills, and save candidate records "
        "to a database. Requires login before searching or saving." # Added guidance
    ),
    model=f"vertexai/{VERTEX_MODEL}",   
    tools=[
        login_user,
        search_job_candidates,
        save_candidate_record
    ],
    # enable_automatic_function_calling=True # Often default or enabled by Agent class
)

logger.info(f"ADK Agent '{root_agent.name}' defined successfully with {len(root_agent.tools)} tools.")

# Add a final info message for clarity when the module is imported/processed by ADK CLI
logger.info("Agent definition complete. Use 'adk run .' or 'adk web .' to start the agent.")
