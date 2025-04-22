"""
ADK Agent definition for the HR Recruiting Assistant.
"""
from __future__ import annotations
import logging
from google.adk.agents import Agent

from . import config
from .tools import hr_tools

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
INSTRUCTIONS = """
You are an HR Recruiting Assistant designed to automate candidate sourcing.

Workflow:
1. Ask if the user wants to start.
2. Collect username, then password → call login_user.
3. On success, collect job title, then skills → call search_for_candidates.
4. If candidates are returned, announce you will save them → call
   save_candidate_record once per candidate.
5. Finish with a summary (found vs.​ saved and any errors).

Be polite and ask only one piece of information at a time.
"""

# ----------------------------------------------------------------------
hr_agent = Agent(
    name="hr_recruiting_assistant",
    model=config.AGENT_MODEL_NAME,
    instruction=INSTRUCTIONS,
    tools=hr_tools,              # tuple[FunctionTool, …]
    # project=config.GCP_PROJECT_ID or None,
    # location=config.GCP_LOCATION or None,
)

logger.info("HR Recruiting Assistant initialised (model=%s)", config.AGENT_MODEL_NAME)
