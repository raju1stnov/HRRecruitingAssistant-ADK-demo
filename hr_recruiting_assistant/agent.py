from google.adk.agents import LlmAgent
from . import prompts, tools

root_agent = LlmAgent(
    name="hr_recruiting_assistant",
    model="gemini-1.5-flash-002",
    instruction=prompts.SYSTEM_PROMPT,
    tools=[
        tools.login_user,
        tools.search_for_candidates,
        tools.save_candidate_record,
    ],
)