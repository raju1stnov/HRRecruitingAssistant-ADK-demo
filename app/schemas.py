# HRRecruitingAssistant-ADK-demo/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Input Schema for the Agent's API Endpoint (if used) ---
class RecruitingWorkflowInput(BaseModel):
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication (secret)")
    title: str = Field(..., description="Job title to search for candidates")
    skills: str = Field(..., description="Comma-separated string of required skills for candidates")

# --- Tool Input/Output Schemas ---

# Login Tool
class LoginInput(BaseModel):
    username: str = Field(..., description="User's login name")
    password: str = Field(..., description="User's password (secret)")

class LoginOutput(BaseModel):
    success: bool = Field(..., description="Indicates if login succeeded")
    token: Optional[str] = Field(None, description="Authentication token if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

# Search Candidates Tool
class SearchInput(BaseModel):
    title: str = Field(..., description="Job title to search for")
    skills: str = Field(..., description="Comma-separated string of required skills")

class CandidateSchema(BaseModel):
    # Mirrors the expected structure from webcrawler_agent -> webservice_agent
    id: str
    name: str
    title: str
    skills: List[str]
    experience: str

class SearchOutput(BaseModel):
    candidates: List[CandidateSchema] = Field(..., description="List of candidate objects matching the criteria.")
    error: Optional[str] = Field(None, description="Error message if search failed")


# Save Candidate Tool
class SaveCandidateInput(BaseModel):
    name: str = Field(..., description="Candidate's full name")
    title: str = Field(..., description="Candidate's job title")
    skills: List[str] = Field(..., description="List of candidate's skills")

class SaveCandidateOutput(BaseModel):
    status: str = Field(..., description="'saved' on success, 'error' on failure")
    name: Optional[str] = Field(None, description="Name of saved candidate")
    error: Optional[str] = Field(None, description="Error message on failure")

# --- Agent's API Output Schema (if API endpoint is used) ---
class RecruitingWorkflowOutput(BaseModel):
    message: str = Field(..., description="Summary message of the workflow execution")
    saved_candidates_count: int = Field(..., description="Number of candidates successfully saved")
    found_candidates_count: int = Field(..., description="Number of candidates initially found")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered during the process")

# --- Schema for JSON-RPC A2A Calls (Needed by main.py /a2a endpoint) ---
class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field(..., description="JSON-RPC version, must be '2.0'")
    method: str = Field(..., description="The name of the method to be invoked")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameters for the method")
    id: Optional[int | str] = Field(None, description="Request identifier")