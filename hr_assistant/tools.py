# HRRecruitingAssistant-ADK-demo/hr_assistant/tools.py

import httpx
import logging
from typing import List, Dict, Any

# ADK imports - Use the correct package 'google_adk'
from google_adk.agents import Tool

# Relative imports within the 'hr_assistant' package
from . import config
from .schemas import (
    LoginInput, LoginOutput,
    SearchInput, SearchOutput, CandidateSchema,
    SaveCandidateInput, SaveCandidateOutput
)

logger = logging.getLogger(__name__)

# --- Helper for JSON-RPC Calls ---
async def a2a_call(agent_url: str, method: str, params: dict) -> Dict[str, Any]:
    """Makes an asynchronous JSON-RPC 2.0 call to another agent."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": config.JSON_RPC_REQUEST_ID
    }
    # Use updated URLs from config (e.g., http://localhost:8100/a2a)
    logger.info(f"A2A Call to {agent_url} - Method: {method}")
    logger.debug(f"A2A Call Params: {params}")

    # Increased timeout slightly for potentially slower host network interactions
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(agent_url, json=payload)
            # Check status code before assuming JSON response
            if response.status_code >= 400:
                 logger.error(f"A2A HTTP Error {response.status_code} from {agent_url} calling {method}: {response.text}")
                 return {"error": f"HTTP error {response.status_code} from target service", "details": response.text}

            response.raise_for_status() # Raise HTTP errors for non-4xx/5xx that might slip through
            data = response.json()
            logger.debug(f"A2A Response from {agent_url} - Method: {method}: {data}")

            if "error" in data:
                error_info = data["error"]
                logger.error(f"A2A JSON-RPC Error from {agent_url} calling {method}: {error_info}")
                # Ensure the returned dict matches expected error structure if possible
                return {"error": error_info.get("message", "Unknown A2A error"), "error_details": error_info}
            elif "result" in data:
                return data["result"] # Return only the 'result' part on success
            else:
                logger.error(f"Invalid JSON-RPC response from {agent_url} (no result or error): {data}")
                return {"error": "Invalid JSON-RPC response structure"}

        except httpx.TimeoutException:
            logger.exception(f"A2A call to {agent_url} for method {method} timed out.")
            return {"error": f"Request to {method} timed out"}
        except httpx.RequestError as e:
            # Includes connection errors, DNS issues etc.
            logger.exception(f"A2A RequestError connecting to {agent_url} for method {method}: {e}")
            return {"error": f"Cannot connect to service at {agent_url}. Is it running and accessible? Details: {e}"}
        except Exception as e:
            logger.exception(f"Unexpected error during A2A call to {agent_url} for method {method}: {e}")
            return {"error": f"An unexpected error occurred: {e}"}

# --- ADK Tools ---

login_tool = Tool.from_function(
    name="login_user",
    description="Authenticates the user with their username and password via the authentication service.",
    func=lambda **kwargs: authenticate_user(**kwargs), # Use lambda to allow keyword args
    input_model=LoginInput,
    output_model=LoginOutput,
)
async def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """ Tool implementation: Calls the auth_agent's login method. """
    params = {"username": username, "password": password}
    result = await a2a_call(config.AUTH_AGENT_URL, "login", params)

    # Process result into LoginOutput structure
    if isinstance(result, dict) and "error" not in result:
        if result.get("success") is True and "token" in result:
            logger.info(f"Login successful for user '{username}'")
            # Match LoginOutput: success=True, token set, error=None
            return {"success": True, "token": result["token"], "error": None}
        else:
            # Handle specific login failure from the service
            login_error = result.get("error", "Authentication failed (no specific error provided)")
            logger.warning(f"Login failed for user '{username}': {login_error}")
            # Match LoginOutput: success=False, token=None, error set
            return {"success": False, "token": None, "error": login_error}
    else:
        # Handle A2A call failure or unexpected response structure
        a2a_error = result.get("error", "Failed to call authentication service") if isinstance(result, dict) else "Unexpected response from auth service"
        logger.error(f"A2A call failed during login for '{username}': {a2a_error}")
        # Match LoginOutput: success=False, token=None, error set
        return {"success": False, "token": None, "error": a2a_error}


search_candidates_tool = Tool.from_function(
    name="search_for_candidates",
    description="Searches for candidates based on job title and required skills using the candidate webservice.",
    func=lambda **kwargs: find_candidates(**kwargs), # Use lambda
    input_model=SearchInput,
    output_model=SearchOutput,
)
async def find_candidates(title: str, skills: str) -> Dict[str, Any]:
    """ Tool implementation: Calls the webservice_agent's search_candidates method. """
    params = {"title": title, "skills": skills}
    logger.info(f"Searching for candidates with title='{title}', skills='{skills}'")
    result = await a2a_call(config.WEBSERVICE_AGENT_URL, "search_candidates", params)

    # Process result into SearchOutput structure
    if isinstance(result, list): # Success case returns a list directly in 'result' field from a2a_call
        try:
            # Validate structure using Pydantic, ensures consistency
            validated_candidates = [CandidateSchema.model_validate(c).model_dump() for c in result if isinstance(c, dict)]
            logger.info(f"Found {len(validated_candidates)} candidates.")
            # Match SearchOutput: candidates list set, error=None
            return {"candidates": validated_candidates, "error": None}
        except Exception as e: # Catch potential validation errors during parsing
             logger.error(f"Error validating candidate data from search service: {e}. Raw data: {result}")
             # Match SearchOutput: candidates empty list, error set
             return {"candidates": [], "error": f"Invalid candidate data received: {e}"}
    elif isinstance(result, dict) and "error" in result:
        # Handle specific error returned by a2a_call (either A2A error or service error)
        search_error = result.get("error", "Failed to call search service (no specific error provided)")
        logger.error(f"Search candidates failed: {search_error}")
        # Match SearchOutput: candidates empty list, error set
        return {"candidates": [], "error": search_error}
    else:
        # Handle unexpected response format from a2a_call
        logger.error(f"Search candidates received unexpected result format: {result}")
        # Match SearchOutput: candidates empty list, error set
        return {"candidates": [], "error": "Invalid or unexpected response from search service"}


save_candidate_tool = Tool.from_function(
    name="save_candidate_record",
    description="Saves the details of a single candidate to the database service.",
    func=lambda **kwargs: store_candidate(**kwargs), # Use lambda
    input_model=SaveCandidateInput,
    output_model=SaveCandidateOutput,
)
async def store_candidate(name: str, title: str, skills: List[str]) -> Dict[str, Any]:
    """ Tool implementation: Calls the dbservice_agent's create_record method. """
    params = {"name": name, "title": title, "skills": skills}
    logger.info(f"Attempting to save candidate: {name}")
    result = await a2a_call(config.DBSERVICE_AGENT_URL, "create_record", params)

    # Process result into SaveCandidateOutput structure
    if isinstance(result, dict) and "error" not in result:
        # Successful call to DB service, check its reported status
        if result.get("status") == "saved":
            saved_name = result.get("name", name) # Use returned name if available
            logger.info(f"Successfully saved candidate: {saved_name}")
            # Match SaveCandidateOutput: status='saved', name set, error=None
            return {"status": "saved", "name": saved_name, "error": None}
        else:
            # Handle save failure reported by the DB service itself
            save_error = result.get("error", "Save operation failed (no specific error provided by DB service)")
            logger.warning(f"Failed to save candidate '{name}': {save_error}")
            # Match SaveCandidateOutput: status='error', name set, error set
            return {"status": "error", "name": name, "error": save_error}
    else:
         # Handle A2A call failure or unexpected response from a2a_call
        a2a_error = result.get("error", "Failed to call database service") if isinstance(result, dict) else "Unexpected response from db service"
        logger.error(f"A2A call failed during save for '{name}': {a2a_error}")
        # Match SaveCandidateOutput: status='error', name set, error set
        return {"status": "error", "name": name, "error": a2a_error}

# List of all tools for the agent
hr_tools = [
    login_tool,
    search_candidates_tool,
    save_candidate_tool,
]