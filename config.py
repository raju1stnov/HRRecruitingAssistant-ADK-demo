# config.py
import os
from dotenv import load_dotenv
import logging
import sys # For exiting on critical config error

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

def get_required_env(var_name: str) -> str:
    """Gets a required environment variable or exits if missing."""
    value = os.getenv(var_name)
    if value is None:
        error_message = f"CRITICAL: Missing required environment variable '{var_name}'. Please set it in your .env file or environment."
        logger.critical(error_message)
        sys.exit(error_message) # Exit the program immediately
    if not isinstance(value, str) or not value.strip():
         error_message = f"CRITICAL: Environment variable '{var_name}' must be a non-empty string. Found: '{value}'"
         logger.critical(error_message)
         sys.exit(error_message) # Exit the program immediately
    return value

# --- Agent URLs (Guaranteed to be str and non-empty) ---
AUTH_AGENT_URL: str = get_required_env("AUTH_AGENT_URL")
WEBSERVICE_AGENT_URL: str = get_required_env("WEBSERVICE_AGENT_URL")
DBSERVICE_AGENT_URL: str = get_required_env("DBSERVICE_AGENT_URL")

# --- Vertex AI Configuration (Guaranteed to be str and non-empty) ---
VERTEX_MODEL: str = get_required_env("VERTEX_MODEL")

# --- Optional Vertex AI Config (Can be None) ---
VERTEX_PROJECT_ID: str | None = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION: str | None = os.getenv("VERTEX_LOCATION")

# --- Optional ADK Server Config ---
ADK_HOST: str = os.getenv("ADK_HOST", "127.0.0.1")
ADK_PORT: int = int(os.getenv("ADK_PORT", "8000"))

# Log loaded config
logger.info("Configuration loaded successfully.")
logger.info(f"AUTH_AGENT_URL: {AUTH_AGENT_URL}")
logger.info(f"WEBSERVICE_AGENT_URL: {WEBSERVICE_AGENT_URL}")
logger.info(f"DBSERVICE_AGENT_URL: {DBSERVICE_AGENT_URL}")
logger.info(f"VERTEX_MODEL: {VERTEX_MODEL}")
if VERTEX_PROJECT_ID:
    logger.info(f"VERTEX_PROJECT_ID: {VERTEX_PROJECT_ID}")
if VERTEX_LOCATION:
    logger.info(f"VERTEX_LOCATION: {VERTEX_LOCATION}")