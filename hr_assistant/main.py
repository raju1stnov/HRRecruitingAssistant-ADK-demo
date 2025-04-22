# HRRecruitingAssistant-ADK-demo/app/main.py (Simplified for 'adk web')

import logging
from fastapi import FastAPI

# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NOTE: We import the agent instance here IF `adk web` requires the `app` object
# from `main.py` to also have a reference to the agent or its tools.
# Often, `adk web` discovers the agent directly from `agent.py` by convention.
# If `adk web` fails to find the agent, uncommenting the next line might be necessary,
# depending on the specific discovery mechanism of your `google-adk` version.
# from .agent import hr_agent

app = FastAPI(
    title="HR Recruiting Assistant (ADK)",
    description="An agent powered by Google ADK to automate HR recruiting tasks. Run via 'adk web'.",
    version="1.0.0"
)

# The API endpoints (/run_workflow, /a2a) have been removed as they are not
# used when interacting via the 'adk web' UI. The agent logic is driven
# by the instructions in agent.py and the tools in tools.py during chat.

@app.get("/health")
async def health():
    """Simple health check endpoint."""
    # Useful to verify the underlying server spun up by 'adk web' is responsive.
    return {"status": "ok", "service": "hr_recruiting_assistant_adk_via_adkweb"}

# The 'adk web' command will typically find the 'hr_agent' instance in 'agent.py'
# and serve the necessary UI and API endpoints for the chat interaction.
# This main.py file provides the FastAPI app structure that 'adk web' might wrap.