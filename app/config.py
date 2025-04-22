# HRRecruitingAssistant-ADK-demo/app/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file if present

# --- IMPORTANT ---
# URLs for the dependent platform services running in Docker.
# Since this ADK agent will run directly on your HOST (via 'adk web'),
# it needs to connect to the HOST ports mapped in the platform-setup_repo's docker-compose.yml.

AUTH_AGENT_URL = os.getenv("AUTH_AGENT_URL", "http://localhost:8100/a2a") # Host Port 8100
WEBSERVICE_AGENT_URL = os.getenv("WEBSERVICE_AGENT_URL", "http://localhost:8101/a2a") # Host Port 8101
DBSERVICE_AGENT_URL = os.getenv("DBSERVICE_AGENT_URL", "http://localhost:8102/a2a") # Host Port 8102

# ADK Agent Configuration (Example - adjust as needed for your GCP setup)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") # Load from env or .env is recommended
GCP_LOCATION = os.getenv("GCP_LOCATION") # Load from env or .env is recommended
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gemini-1.5-flash-001") # Or other suitable Gemini model
# Ensure your environment where you run 'adk web' has GCP credentials configured
# (e.g., via `gcloud auth application-default login`)

# A simple identifier for JSON-RPC requests initiated by this agent
JSON_RPC_REQUEST_ID = "hra-adk-agent-host-1"