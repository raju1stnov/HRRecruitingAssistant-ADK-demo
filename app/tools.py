import httpx
import logging
from typing import List, Dict, Any

# Assuming google.cloud.aiplatform.private_preview.agents imports Agent and Tool
# Adjust the import based on the actual ADK package structure if it changes
from google.cloud.aiplatform.preview.agents import Tool

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
    logger.debug(f"A2A Call to {agent_url} - Method: {method}, Params: {params}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(agent_url, json=payload, timeout=15.0)
            response.raise_for_status() # Raise HTTP errors
            data = response.json()
            logger.debug(f"A2A Response from {agent_url} - Method: {method}: {data}")

            if "error" in data:
                error_info = data["error"]
                logger.error(f"A2A Error from {agent_url} calling {method}: {error_info}")
                # Return a dictionary indicating error, letting the tool handle it
                return {"error": error_info.get("message", "Unknown A2A error"), "error_details": error_info}
            elif "result" in data:
                return data["result"]
            else:
                logger.error(f"Invalid JSON-RPC response from {agent_url} (no result or error): {data}")
                return {"error": "Invalid JSON-RPC response structure"}

        except httpx.TimeoutException:
            logger.exception(f"A2A call to {agent_url} for method {method} timed out.")
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            logger.exception(f"A2A RequestError to {agent_url} for method {method}: {e}")
            return {"error": f"Network or connection error: {e}"}
        except Exception as e:
            logger.exception(f"Unexpected error during A2A call to {agent_url} for method {method}: {e}")
            return {"error": f"An unexpected error occurred: {e}"}

# --- ADK Tools ---

login_tool = Tool.from_function(
    name="login_user",
    description="Authenticates the user with their username and password, returning an access token.",
    func=lambda input_data: authenticate_user(**input_data), # Wrap async call
    input_model=LoginInput,
    output_model=LoginOutput,
)
async def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """ Tool implementation: Calls the auth_agent's login method. """
    params = {"username": username, "password": password}
    result = await a2a_call(config.AUTH_AGENT_URL, "login", params)

    # Process result into LoginOutput format
    if isinstance(result, dict) and "error" not in result:
        if result.get("success") and "token" in result:
            return {"success": True, "token": result["token"]}
        else:
            # Handle login failure reported by the service
            return {"success": False, "error": result.get("error", "Authentication failed")}
    else:
        # Handle A2A call failure
        return {"success": False, "error": result.get("error", "Failed to call authentication service")}


search_candidates_tool = Tool.from_function(
    name="search_for_candidates",
    description="Searches for candidates based on job title and required skills. Requires prior successful login.",
    func=lambda input_data: find_candidates(**input_data), # Wrap async call
    input_model=SearchInput,
    output_model=SearchOutput,
)
async def find_candidates(title: str, skills: str) -> Dict[str, Any]:
    """ Tool implementation: Calls the webservice_agent's search_candidates method. """
    # NOTE: The token management needs to happen in the *Agent Core* logic.
    # This tool assumes it's called *after* login was successful and the token is available in the agent's context.
    # For this example, we focus on the A2A call itself. A real agent would fetch the token from its state.
    params = {"title": title, "skills": skills}
    result = await a2a_call(config.WEBSERVICE_AGENT_URL, "search_candidates", params)

    if isinstance(result, list): # Success case returns a list directly
        # Validate structure slightly if needed, Pydantic output_model helps here
        validated_candidates = [CandidateSchema(**c).dict() for c in result if isinstance(c, dict)]
        return {"candidates": validated_candidates}
    elif isinstance(result, dict) and "error" in result:
        return {"candidates": [], "error": result.get("error", "Failed to call search service")}
    else:
        logger.error(f"Search candidates returned unexpected result format: {result}")
        return {"candidates": [], "error": "Invalid response from search service"}


save_candidate_tool = Tool.from_function(
    name="save_candidate_record",
    description="Saves the details of a single candidate to the database.",
    func=lambda input_data: store_candidate(**input_data), # Wrap async call
    input_model=SaveCandidateInput,
    output_model=SaveCandidateOutput,
)
async def store_candidate(name: str, title: str, skills: List[str]) -> Dict[str, Any]:
    """ Tool implementation: Calls the dbservice_agent's create_record method. """
    params = {"name": name, "title": title, "skills": skills}
    result = await a2a_call(config.DBSERVICE_AGENT_URL, "create_record", params)

    if isinstance(result, dict) and "error" not in result:
        if result.get("status") == "saved":
            return {"status": "saved", "name": result.get("name")}
        else:
            # Handle save failure reported by the service (might have specific errors)
            return {"status": "error", "error": result.get("error", "Save operation failed"), "name": name}
    else:
         # Handle A2A call failure
        return {"status": "error", "error": result.get("error", "Failed to call database service"), "name": name}

# List of all tools for the agent
hr_tools = [
    login_tool,
    search_candidates_tool,
    save_candidate_tool,
]