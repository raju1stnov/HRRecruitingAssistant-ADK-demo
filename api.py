import os, logging
from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = get_fast_api_app(
    agent_dir="hr_recruiting_assistant",  # ADK discovers root_agent here
    session_db_url=os.getenv("SESSION_DB_URL", ""),
    web=True,                             # serve ADK Web UI at /dev-ui
    allow_origins=["*"],
)
