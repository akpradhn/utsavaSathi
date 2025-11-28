"""
Coordinator Agent with ParallelAgent - Demonstrates parallel execution.

This is an alternative coordinator that uses ParallelAgent to run
independent agents (research, preparation, experience) in parallel.
"""

from __future__ import annotations

import logging

from google.adk.agents import Agent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool, google_search

from utsava_agent.agents import (
    content_agent,
    experience_agent,
    preparation_agent,
    research_agent,
)
from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

# Create a ParallelAgent that runs research, preparation, and experience agents in parallel
# These agents are independent and can run simultaneously
parallel_research_prep_exp = ParallelAgent(
    name="parallel_research_prep_exp",
    description="Runs research, preparation, and experience agents in parallel",
    sub_agents=[research_agent, preparation_agent, experience_agent],
)

# Create tools for the coordinator
parallel_tool = AgentTool(parallel_research_prep_exp)
content_tool = AgentTool(content_agent)

coordinator_agent_parallel = Agent(
    name="utsava_coordinator_parallel",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        response_mime_type="application/json",
    ),
    description=(
        "Coordinates festival planning using parallel execution. "
        "Runs research, preparation, and experience agents in parallel, "
        "then uses content agent to generate shareables."
    ),
    instruction=(
        "You are the Utsava Sathi coordinator that orchestrates festival planning using parallel execution.\n\n"
        "WORKFLOW:\n"
        "1. Parse the user request to extract:\n"
        "   - Festival name\n"
        "   - Location (city, state)\n"
        "   - Family context (number of people, children, etc.)\n\n"
        "2. Call the parallel_research_prep_exp tool with a prompt that includes:\n"
        "   - Festival name and location\n"
        "   - Family context\n"
        "   - Request for all three outputs (research, preparation, experience)\n\n"
        "   This will run three agents in parallel:\n"
        "   - ResearchAgent: Returns festival overview JSON\n"
        "   - PreparationAgent: Returns pre_festival JSON\n"
        "   - ExperienceAgent: Returns festival_day JSON\n\n"
        "3. Parse the parallel results (you'll get responses from all three agents)\n\n"
        "4. Extract the results:\n"
        "   - Research result → festival_overview (map origin_story to short_story)\n"
        "   - Preparation result → pre_festival\n"
        "   - Experience result → festival_day\n\n"
        "5. Call ContentAgent with the preparation results to generate shareables\n\n"
        "6. Assemble the final FestivalPlan JSON with this structure:\n"
        "{\n"
        '  "festival_overview": {\n'
        '    "name": "...",\n'
        '    "local_name": "...",\n'
        '    "why_celebrated": "...",\n'
        '    "short_story": "...",  // from research_agent.origin_story\n'
        '    "themes": ["..."],\n'
        '    "symbolism": ["..."],\n'
        '    "key_values": ["..."],\n'
        '    "family_roles": {"elders": "...", "parents": "...", "children": "..."},\n'
        '    "odisha_flavour": "...",\n'
        '    "greetings": ["..."]\n'
        '  },\n'
        '  "pre_festival": {...},\n'
        '  "festival_day": {...},\n'
        '  "shareables": {...},\n'
        '  "metadata": {\n'
        '    "generated_at": "ISO timestamp",\n'
        '    "location_context": "...",\n'
        '    "agent_version": "multi_agent_parallel_v1",\n'
        '    "language": "en"\n'
        '  }\n'
        "}\n\n"
        "IMPORTANT:\n"
        "- The parallel tool returns responses from all three agents\n"
        "- You need to identify which response is from which agent\n"
        "- Map research_agent's 'origin_story' to festival_overview's 'short_story'\n"
        "- Include all 10 fields in festival_overview\n"
        "- Return JSON only - no markdown, no backticks\n"
    ),
    tools=[
        parallel_tool,
        content_tool,
        google_search,
    ],
)

logger.info(
    "COORDINATOR_PARALLEL_INITIALIZED: Parallel coordinator created successfully "
    "with parallel execution for research, preparation, and experience agents"
)



