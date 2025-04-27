"""Central, validated configuration – imported by hr_assistant.agent"""
from pathlib import Path
import os
import sys
import logging
from dotenv import load_dotenv

# Always load the .env that sits next to this file
load_dotenv(dotenv_path=Path(__file__).with_suffix(".env"))

log = logging.getLogger(__name__)

def req(var: str) -> str:
    val = os.getenv(var)
    if not val:
        log.critical("Missing required env var %s", var)
        sys.exit(f"Missing required env var: {var}")
    return val

# Required URLs
AUTH_AGENT_URL      : str = req("AUTH_AGENT_URL")
WEBSERVICE_AGENT_URL: str = req("WEBSERVICE_AGENT_URL")
DBSERVICE_AGENT_URL : str = req("DBSERVICE_AGENT_URL")

# Optional registry
A2A_REGISTRY_URL    : str | None = os.getenv("A2A_REGISTRY_URL")

# Vertex model (required)
VERTEX_MODEL        : str = req("VERTEX_MODEL")

# Optional Vertex project / region
VERTEX_PROJECT_ID   : str | None = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION     : str | None = os.getenv("VERTEX_LOCATION")
ADK_HOST: str= os.getenv("ADK_HOST", "127.0.0.1")
ADK_PORT: int= int(os.getenv("ADK_PORT", "8007").strip())