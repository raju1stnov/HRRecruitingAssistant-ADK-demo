import logging
from typing import List, Dict, Any

# ADK imports - adjust based on final package structure
from google.cloud.aiplatform.preview.agents import Agent, ToolConfig, ChatAgent # Using ChatAgent for potential future extensions

from . import config
from .tools import hr_tools
from .schemas import RecruitingWorkflowInput, RecruitingWorkflowOutput, CandidateSchema

logger = logging.getLogger(__name__)

# --- Agent Definition ---

# Configure the tools for the agent
tool_config = ToolConfig(tool_list=hr_tools)

# Define the core instructions for the LLM. This is crucial for guiding the workflow.
# It needs to understand the sequence: Login -> Search -> Save (Loop)
AGENT_INSTRUCTIONS = """
You are an HR Recruiting Assistant. Your goal is to automate the process of finding and saving candidate profiles based on user-provided criteria.

Follow these steps precisely:
1.  **Authenticate:** Use the 'login_user' tool with the provided username and password.
2.  **Check Login:** If login fails, stop immediately and report the authentication error. Do not proceed.
3.  **Search Candidates:** If login is successful, use the 'search_for_candidates' tool with the provided job title and skills.
4.  **Check Search Results:** If the search fails or returns no candidates, report this outcome.
5.  **Save Candidates:** If candidates are found, iterate through EACH candidate returned by the search results. For EACH candidate, use the 'save_candidate_record' tool with their name, title, and skills list. Keep track of which candidates were saved successfully and which failed.
6.  **Report Outcome:** Summarize the entire process. Report the total number of candidates found, the number successfully saved, and list any specific errors encountered during login, search, or saving individual candidates.
"""

# Create the Agent instance
# Using ChatAgent allows potential multi-turn interactions if needed later,
# but for this workflow, we'll use a single invoke call.
hr_agent = ChatAgent(
    model=config.AGENT_MODEL_NAME,
    tool_config=tool_config,
    instructions=AGENT_INSTRUCTIONS,
    # Add project/location if required by your ADK setup/authentication
    # project=config.GCP_PROJECT_ID,
    # location=config.GCP_LOCATION,
)

# --- Agent Interaction Logic ---
async def run_hr_workflow(input_data: RecruitingWorkflowInput) -> RecruitingWorkflowOutput:
    """
    Invokes the ADK agent to perform the recruiting workflow.
    This function acts as the entry point for the agent's task.
    """
    logger.info(f"Starting HR Workflow for user: {input_data.username}, title: {input_data.title}")

    # Construct the initial prompt/query for the agent based on the input
    # This tells the agent *what* to do with the provided details, guided by its instructions.
    user_query = (
        f"Please start the recruiting workflow. "
        f"Username: {input_data.username}, Password: [REDACTED], " # Avoid logging/sending raw password if possible
        f"Job Title: {input_data.title}, Required Skills: {input_data.skills}. "
        f"Remember to use the actual password provided in the input context." # LLM needs access to the password via tools
    )

    # Agent context can be used to pass sensitive data like passwords securely if needed,
    # depending on ADK's specific mechanisms. For simplicity, we assume the LLM
    # uses the tool inputs directly here, based on the user query.
    # A more robust approach might involve managing state/tokens within the agent's execution context.

    # Invoke the agent (using chat interaction model for potential future use)
    # The agent will use its instructions and the query to call tools sequentially.
    try:
        # For a single workflow execution, we start a chat and get the response.
        chat = hr_agent.start_chat()
        # Pass necessary details implicitly or explicitly depending on ADK version
        # The LLM needs the input_data details to make the *first* tool call (login)
        # Let's assume the LLM can extract parameters from the query for the initial tools
        response = await chat.send_message_async(user_query, **input_data.dict()) # Pass input for context if needed by ADK version

        # --- Process the final response from the agent ---
        # The agent's final response *should* be the summary requested in the instructions.
        # We need to parse this response to create the structured RecruitingWorkflowOutput.
        # This part is highly dependent on how the LLM formats its final answer based on the prompt.
        # It might require some string parsing or expecting a specific JSON structure in the response content.

        # Example: Simple parsing assuming the LLM provides a text summary.
        # A more robust solution would be to ask the LLM to format its *final* output as JSON matching RecruitingWorkflowOutput.
        final_message = response.content
        logger.info(f"Agent final response content: {final_message}")

        # Placeholder parsing logic - NEEDS REFINEMENT based on actual LLM output
        saved_count = 0
        found_count = 0
        errors_list = []        
        # For now, returning raw message and placeholder counts/errors.
        if "saved" in final_message.lower():
             # Try to extract numbers
             import re
             saved_match = re.search(r"(\d+)\s+candidates?\s+saved", final_message, re.IGNORECASE)
             found_match = re.search(r"(\d+)\s+candidates?\s+found", final_message, re.IGNORECASE)
             if saved_match: saved_count = int(saved_match.group(1))
             if found_match: found_count = int(found_match.group(1))
        if "error" in final_message.lower():
            errors_list.append("Errors occurred during the workflow. Check agent logs or full response.")

        return RecruitingWorkflowOutput(
            message=final_message,
            saved_candidates_count=saved_count,
            found_candidates_count=found_count,
            errors=errors_list
        )

    except Exception as e:
        logger.exception(f"Error invoking ADK agent workflow: {e}")
        return RecruitingWorkflowOutput(
            message=f"Workflow failed: {e}",
            saved_candidates_count=0,
            found_candidates_count=0,
            errors=[f"Critical agent error: {e}"]
        )