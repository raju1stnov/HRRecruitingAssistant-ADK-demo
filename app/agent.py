# HRRecruitingAssistant-ADK-demo/app/agent.py

import logging
from typing import List, Dict, Any

# ADK imports - Use the correct package 'google_adk'
from google_adk.agents import Agent, ToolConfig, ChatAgent

from . import config
from .tools import hr_tools # Tools defined in tools.py

logger = logging.getLogger(__name__)

# --- Agent Definition ---

# Configure the tools for the agent
tool_config = ToolConfig(tool_list=hr_tools)

# Agent Instructions for Conversational UI (Keep as provided)
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
# Make sure GCP_PROJECT_ID and GCP_LOCATION are set in your environment or .env file
# if your ADK setup requires them for authentication/operation.
hr_agent = ChatAgent(
    model=config.AGENT_MODEL_NAME,
    tool_config=tool_config,
    instructions=AGENT_UI_INSTRUCTIONS,
    project=config.GCP_PROJECT_ID,   # Pass project/location if needed by ADK
    location=config.GCP_LOCATION,  # Pass project/location if needed by ADK
)

# The API-specific workflow function 'run_hr_workflow' is removed as it's not used for 'adk web'.