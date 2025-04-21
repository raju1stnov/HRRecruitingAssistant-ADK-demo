# HRRecruitingAssistant-ADK-demo/app/agent.py

import logging
from typing import List, Dict, Any

# ADK imports - adjust based on final package structure
from google.cloud.aiplatform.preview.agents import Agent, ToolConfig, ChatAgent

from . import config
from .tools import hr_tools # Tools defined in tools.py remain the same
# Schemas are used by tools, but the main input comes via chat now
# from .schemas import RecruitingWorkflowInput, RecruitingWorkflowOutput

logger = logging.getLogger(__name__)

# --- Agent Definition ---

# Configure the tools for the agent (remains the same)
tool_config = ToolConfig(tool_list=hr_tools)

# --- *** NEW: Updated Agent Instructions for Conversational UI *** ---
AGENT_UI_INSTRUCTIONS = """
You are an HR Recruiting Assistant designed to work via chat. Your goal is to automate finding and saving candidate profiles.

Engage the user in a conversation to collect the required information step-by-step:
1.  **Greet & Initiate:** Start by explaining your purpose and ask the user if they want to begin the recruiting workflow. Wait for their confirmation.
2.  **Collect Username:** If they agree, ask for their username.
3.  **Collect Password:** Once you have the username, ask for their password. **IMPORTANT:** Acknowledge receipt but DO NOT repeat the password in your response. Use the password only for the login tool call.
4.  **Authenticate:** Use the 'login_user' tool with the collected username and password.
5.  **Handle Login Result:**
    * If login is successful, inform the user and proceed.
    * If login fails, inform the user clearly about the failure (using the error message if provided by the tool) and STOP the workflow. Do not ask for further details.
6.  **Collect Job Title:** After successful login, ask for the job title they want to search for.
7.  **Collect Skills:** After getting the title, ask for the required skills (suggest comma-separated).
8.  **Search Candidates:** Use the 'search_for_candidates' tool with the collected title and skills.
9.  **Report Search Results:**
    * If the search fails, report the error and stop.
    * If no candidates are found, inform the user and stop.
    * If candidates are found, inform the user how many were found (you can optionally list their names briefly). Then, explicitly state that you will proceed to save them.
10. **Save Candidates:** Proceed to save the found candidates. Iterate through EACH candidate and use the 'save_candidate_record' tool with their specific name, title, and skills list.
11. **Report Final Outcome:** After attempting to save all candidates, provide a clear, final summary: state the number found, the number successfully saved, and list any specific errors encountered during the saving process for individual candidates.

Maintain a polite and professional tone throughout the conversation. Only ask for one piece of information at a time and wait for the user's response before proceeding to the next step.
"""

# Create the Agent instance
# Ensure this instance is discoverable by `adk web` (defining it at module level usually works)
hr_agent = ChatAgent(
    model=config.AGENT_MODEL_NAME,
    tool_config=tool_config,
    instructions=AGENT_UI_INSTRUCTIONS, # Use the new instructions
    # project=config.GCP_PROJECT_ID,   # Uncomment if needed for auth
    # location=config.GCP_LOCATION,  # Uncomment if needed for auth
)

# --- API-Specific Workflow Function (Commented Out/Optional) ---
# This function was designed for the API endpoint (/run_workflow in main.py)
# which receives all input at once. It's not directly used by the
# conversational UI (`adk web`). The UI interaction follows the AGENT_UI_INSTRUCTIONS above.
# You can keep this function if you want the API endpoint in main.py to still
# function separately, but ensure it handles potential state/context correctly
# if ADK manages state across different interaction types. For simplicity in focusing
# on the UI, we comment it out here. If kept, it would need careful testing alongside UI usage.

# from .schemas import RecruitingWorkflowInput, RecruitingWorkflowOutput # Need these if function is active
# async def run_hr_workflow(input_data: RecruitingWorkflowInput) -> RecruitingWorkflowOutput:
#     """
#     Invokes the ADK agent to perform the recruiting workflow via API.
#     (This function is NOT used by the `adk web` UI interaction by default)
#     """
#     logger.info(f"Starting HR Workflow via API for user: {input_data.username}, title: {input_data.title}")
#     user_query = (
#         f"Please start the recruiting workflow. "
#         f"Username: {input_data.username}, Password: [REDACTED], "
#         f"Job Title: {input_data.title}, Required Skills: {input_data.skills}. "
#         f"Use the provided password for login."
#     )
#     try:
#         chat = hr_agent.start_chat()
#         # Pass input for context if needed by ADK version/implementation
#         response = await chat.send_message_async(user_query, **input_data.dict())
#         final_message = response.content
#         logger.info(f"Agent final response content via API: {final_message}")
#         # Placeholder parsing logic - NEEDS REFINEMENT based on actual LLM output
#         saved_count = 0
#         found_count = 0
#         errors_list = []
#         # TODO: Implement robust parsing of final_message to extract counts and errors.
#         if "saved" in final_message.lower():
#              import re
#              saved_match = re.search(r"(\d+)\s+candidates?\s+saved", final_message, re.IGNORECASE)
#              found_match = re.search(r"(\d+)\s+candidates?\s+found", final_message, re.IGNORECASE)
#              if saved_match: saved_count = int(saved_match.group(1))
#              if found_match: found_count = int(found_match.group(1))
#         if "error" in final_message.lower():
#             errors_list.append("Errors occurred during the workflow. Check agent logs or full response.")

#         return RecruitingWorkflowOutput(
#             message=final_message,
#             saved_candidates_count=saved_count,
#             found_candidates_count=found_count,
#             errors=errors_list
#         )
#     except Exception as e:
#         logger.exception(f"Error invoking ADK agent workflow via API: {e}")
#         return RecruitingWorkflowOutput(
#             message=f"Workflow failed: {e}",
#             saved_candidates_count=0,
#             found_candidates_count=0,
#             errors=[f"Critical agent error: {e}"]
#         )