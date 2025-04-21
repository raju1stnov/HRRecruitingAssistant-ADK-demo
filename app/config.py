import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file if present

# URLs for the dependent platform services (using Docker DNS by default)
# These should match the service names and ports defined in the platform-setup_repo docker-compose
AUTH_AGENT_URL = os.getenv("AUTH_AGENT_URL", "http://auth_agent:8000/a2a")
WEBSERVICE_AGENT_URL = os.getenv("WEBSERVICE_AGENT_URL", "http://webservice_agent:8000/a2a")
DBSERVICE_AGENT_URL = os.getenv("DBSERVICE_AGENT_URL", "http://dbservice_agent:8000/a2a")

# ADK Agent Configuration (Example - adjust as needed for your GCP setup)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gemini-1.5-flash-001") # Or other suitable Gemini model

# A simple identifier for JSON-RPC requests initiated by this agent
JSON_RPC_REQUEST_ID = "hra-adk-agent-1"