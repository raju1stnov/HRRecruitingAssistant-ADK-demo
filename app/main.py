# HRRecruitingAssistant-ADK-demo/app/main.py (Corrected for UI Focus)

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Schemas are still needed for the optional A2A endpoint structure
from .schemas import RecruitingWorkflowInput, RecruitingWorkflowOutput, JSONRPCRequest
# We don't import the agent or specific functions here anymore,
# as the API endpoints are being disabled/modified.

# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HR Recruiting Assistant (ADK)",
    description="An agent powered by Google ADK to automate HR recruiting tasks. Primarily intended for interaction via 'adk web' UI.",
    version="1.0.0"
)

# --- REST Endpoint to trigger the workflow ---
# Modified to indicate it's not the primary interaction method for the UI-focused agent.
@app.post("/run_workflow", response_model=RecruitingWorkflowOutput)
async def trigger_workflow(input_data: RecruitingWorkflowInput):
    """
    (API Endpoint - Currently Disabled/Not Recommended for UI Agent)
    This endpoint was designed for an API-driven workflow.
    The current agent configuration in agent.py is optimized for conversational
    interaction via the 'adk web' UI and does not use the function previously
    called by this endpoint.
    """
    logger.warning("API endpoint /run_workflow called, but the agent is configured for UI interaction.")
    # Return a "Not Implemented" or similar error to avoid confusion.
    raise HTTPException(
        status_code=501, # 501 Not Implemented
        detail="This API endpoint is not active for the current UI-focused agent configuration. Please interact with the agent using the 'adk web' UI."
    )

# --- (Optional) A2A Endpoint ---
# Modified similarly to indicate it's not the primary interaction method.
@app.post("/a2a")
async def handle_a2a(rpc_req: JSONRPCRequest):
    if rpc_req.jsonrpc != "2.0":
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "id": rpc_req.id,"error": {"code": -32600, "message": "Invalid JSON-RPC version"}})

    if rpc_req.method == "start_recruiting_workflow":
        try:
            # Use model_validate for robust validation from dict
            input_data = RecruitingWorkflowInput.model_validate(rpc_req.params)
        # Catch Pydantic's validation error specifically
        except ValidationError as e:
             logger.warning(f"A2A Invalid params for start_recruiting_workflow: {e}")
             return JSONResponse(
                status_code=400, # Bad Request
                content={
                    "jsonrpc": "2.0", "id": rpc_req.id,
                    "error": {"code": -32602, "message": f"Invalid params: {e}"}
                }
            )
        # Catch other potential errors during param processing if any
        except Exception as e:
            logger.error(f"Unexpected error processing A2A params: {e}")
            return JSONResponse(
                status_code=400, # Bad Request
                content={
                    "jsonrpc": "2.0", "id": rpc_req.id,
                    "error": {"code": -32602, "message": f"Error processing parameters: {e}"}
                }
            )


        # If validation passes, proceed (but workflow is disabled for UI focus)
        logger.warning("A2A endpoint 'start_recruiting_workflow' called, but the agent is configured for UI interaction.")
        # Return a method-specific error indicating it's not available for this agent config.
        return JSONResponse(
                status_code=501, # 501 Not Implemented (or 404 Not Found)
                content={
                    "jsonrpc": "2.0", "id": rpc_req.id,
                    "error": {"code": -32601, "message": "Method 'start_recruiting_workflow' not available for the current UI-focused agent configuration. Use 'adk web'."}
                }
            )
    else:
        # Method not found
        return JSONResponse(status_code=404, content={"jsonrpc": "2.0", "id": rpc_req.id, "error": {"code": -32601, "message": "Method not found"}})


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    # This remains useful to check if the FastAPI server itself is running.
    return {"status": "ok", "service": "hr_recruiting_assistant_adk"}