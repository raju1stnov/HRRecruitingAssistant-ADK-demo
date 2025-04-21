import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .schemas import RecruitingWorkflowInput, RecruitingWorkflowOutput, JSONRPCRequest # Re-using JSONRPCRequest for potential future A2A *into* this agent
from .agent import run_hr_workflow # Import the function that runs the agent workflow

# Basic Logging Setup (customize as needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HR Recruiting Assistant (ADK)",
    description="An agent powered by Google ADK to automate HR recruiting tasks.",
    version="1.0.0"
)

# --- REST Endpoint to trigger the workflow ---
@app.post("/run_workflow", response_model=RecruitingWorkflowOutput)
async def trigger_workflow(input_data: RecruitingWorkflowInput):
    """
    Starts the HR recruiting workflow using the ADK agent.
    Takes username, password, title, and skills as input.
    """
    logger.info(f"Received request to run workflow for title: {input_data.title}")
    try:
        result = await run_hr_workflow(input_data)
        # Check if the result indicates a failure within the workflow controlled by the agent
        if result.errors and "Critical agent error" in result.errors[0]:
             raise HTTPException(status_code=500, detail=result.message)
        return result
    except Exception as e:
        logger.exception("Unhandled exception during workflow trigger")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- (Optional) A2A Endpoint ---
# If this agent needs to be called by *other* agents via JSON-RPC
@app.post("/a2a")
async def handle_a2a(rpc_req: JSONRPCRequest):
    if rpc_req.jsonrpc != "2.0":
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0", "id": rpc_req.id,
                "error": {"code": -32600, "message": "Invalid JSON-RPC version"}
            }
        )

    if rpc_req.method == "start_recruiting_workflow":
        try:
            # Validate params match RecruitingWorkflowInput schema
            input_data = RecruitingWorkflowInput(**rpc_req.params)
        except Exception as e: # Handles Pydantic validation errors
             return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0", "id": rpc_req.id,
                    "error": {"code": -32602, "message": f"Invalid params: {e}"}
                }
            )

        try:
            # Run the workflow
            result = await run_hr_workflow(input_data)
            # Return the result in JSON-RPC format
            return {
                "jsonrpc": "2.0",
                "id": rpc_req.id,
                "result": result.dict() # Convert Pydantic model to dict
            }
        except Exception as e:
            logger.exception(f"Error executing workflow via A2A for ID {rpc_req.id}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0", "id": rpc_req.id,
                    "error": {"code": -32603, "message": "Internal workflow error", "data": str(e)}
                }
            )
    else:
        # Method not found
        return JSONResponse(
            status_code=404,
            content={
                "jsonrpc": "2.0", "id": rpc_req.id,
                "error": {"code": -32601, "message": "Method not found"}
            }
        )


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "hr_recruiting_assistant_adk"}

# Example: To run directly with uvicorn for local testing
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8006) # Use a different port