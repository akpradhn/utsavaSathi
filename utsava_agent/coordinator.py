"""
Coordinator Agent - Orchestrates all specialized agents in the multi-agent system.

This agent receives user requests, delegates tasks to specialized agents,
and assembles the final FestivalPlan JSON.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool

from utsava_agent.agents import (
    content_agent,
    experience_agent,
    preparation_agent,
    research_agent,
)
from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

# Create tools for agent-to-agent calls using ADK's built-in AgentTool
research_tool = AgentTool(research_agent)
preparation_tool = AgentTool(preparation_agent)
experience_tool = AgentTool(experience_agent)
content_tool = AgentTool(content_agent)

coordinator_agent = Agent(
    name="utsava_coordinator",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        # Note: response_mime_type removed to allow function calling (tool use)
        # The coordinator needs to call other agents as tools via AgentTool
    ),
    description=(
        "Coordinates festival planning by orchestrating specialized agents. "
        "Delegates tasks to research, preparation, experience, and content agents, "
        "then assembles the final FestivalPlan."
    ),
    instruction=(
        "You are the Utsava Sathi coordinator that orchestrates festival planning.\n\n"
        "WORKFLOW:\n"
        "1. Parse the user request to extract:\n"
        "   - Festival name\n"
        "   - Location (city, state)\n"
        "   - Family context (number of people, children, etc.)\n\n"
        "2. Delegate tasks to specialized agents using the available tools:\n"
        "   - Use ResearchAgent tool to get festival overview\n"
        "   - Use PreparationAgent tool to get pre_festival plan\n"
        "   - Use ExperienceAgent tool to get festival_day plan\n"
        "   - Use ContentAgent tool to get shareables (after you have preparation results)\n\n"
        "3. For each agent call, provide a clear prompt like:\n"
        "   - Research: 'Research [festival name] in [location]. Return festival overview JSON.'\n"
        "   - Preparation: 'Plan pre-festival activities for [festival] in [location] for [family context]. Return pre_festival JSON.'\n"
        "   - Experience: 'Plan festival day experience for [festival] in [location] for [family context]. Return festival_day JSON.'\n"
        "   - Content: 'Create shareable content. Puja items: [list]. Tasks: [list]. Return shareables JSON.'\n\n"
        "4. Collect all results from the agents\n\n"
        "5. Map research_agent output to festival_overview:\n"
        "   The research_agent returns a JSON with these fields:\n"
        "   - name, local_name, origin_story, why_celebrated, themes, symbolism, key_values,\n"
        "     family_roles (object with elders, parents, children), odisha_flavour, greetings\n\n"
        "   CRITICAL: You MUST include ALL fields from research_agent in festival_overview.\n"
        "   Map this to festival_overview structure (ALL fields are REQUIRED):\n"
        "   {\n"
        '     "name": <from research_agent.name>,\n'
        '     "local_name": <from research_agent.local_name>,\n'
        '     "why_celebrated": <from research_agent.why_celebrated>,\n'
        '     "short_story": <from research_agent.origin_story>,\n'
        '     "themes": <from research_agent.themes>,\n'
        '     "symbolism": <from research_agent.symbolism>,\n'
        '     "key_values": <from research_agent.key_values>,\n'
        '     "family_roles": <from research_agent.family_roles>,\n'
        '     "odisha_flavour": <from research_agent.odisha_flavour>,\n'
        '     "greetings": <from research_agent.greetings>\n'
        "   }\n\n"
        "   IMPORTANT: Do NOT omit any fields. All 10 fields must be present:\n"
        "   1. name\n"
        "   2. local_name\n"
        "   3. why_celebrated\n"
        "   4. short_story (from origin_story)\n"
        "   5. themes\n"
        "   6. symbolism\n"
        "   7. key_values\n"
        "   8. family_roles\n"
        "   9. odisha_flavour\n"
        "   10. greetings\n\n"
        "6. Assemble the final FestivalPlan JSON with this exact structure:\n"
        "   CRITICAL: festival_overview MUST have exactly these 10 fields (no more, no less):\n"
        "{\n"
        '  "festival_overview": {\n'
        '    "name": "...",           // REQUIRED - from research_agent.name\n'
        '    "local_name": "...",     // REQUIRED - from research_agent.local_name\n'
        '    "why_celebrated": "...", // REQUIRED - from research_agent.why_celebrated\n'
        '    "short_story": "...",    // REQUIRED - from research_agent.origin_story\n'
        '    "themes": ["..."],       // REQUIRED - from research_agent.themes\n'
        '    "symbolism": ["..."],    // REQUIRED - from research_agent.symbolism\n'
        '    "key_values": ["..."],   // REQUIRED - from research_agent.key_values\n'
        '    "family_roles": {        // REQUIRED - from research_agent.family_roles\n'
        '      "elders": "...",\n'
        '      "parents": "...",\n'
        '      "children": "..."\n'
        '    },\n'
        '    "odisha_flavour": "...", // REQUIRED - from research_agent.odisha_flavour\n'
        '    "greetings": ["..."]     // REQUIRED - from research_agent.greetings\n'
        '  },\n'
        '  "pre_festival": {...},       // from preparation_agent\n'
        '  "festival_day": {...},       // from experience_agent\n'
        '  "shareables": {...},         // from content_agent\n'
        '  "metadata": {\n'
        '    "generated_at": "ISO timestamp in UTC (e.g., 2025-11-28T12:00:00Z)",\n'
        '    "location_context": "location from request (e.g., Bhubaneswar, Odisha, India)",\n'
        '    "agent_version": "multi_agent_v1",\n'
        '    "language": "en"\n'
        '  }\n'
        "}\n\n"
        "CRITICAL RULES FOR festival_overview:\n"
        "- festival_overview MUST contain exactly these 10 fields (ALL are mandatory):\n"
        "  1. name (string)\n"
        "  2. local_name (string)\n"
        "  3. why_celebrated (string)\n"
        "  4. short_story (string) - mapped from research_agent.origin_story\n"
        "  5. themes (array of strings)\n"
        "  6. symbolism (array of strings) - DO NOT OMIT\n"
        "  7. key_values (array of strings) - DO NOT OMIT\n"
        "  8. family_roles (object with elders, parents, children) - DO NOT OMIT\n"
        "  9. odisha_flavour (string) - DO NOT OMIT\n"
        "  10. greetings (array of strings) - DO NOT OMIT\n\n"
        "- If research_agent doesn't return a field, use empty value but include it:\n"
        "  * Empty arrays: []\n"
        "  * Empty strings: \"\"\n"
        "  * Empty objects: {}\n\n"
        "OTHER IMPORTANT RULES:\n"
        "- You MUST call all four agents (research, preparation, experience, content)\n"
        "- Parse JSON responses from each agent carefully\n"
        "- Map research_agent's 'origin_story' to festival_overview's 'short_story'\n"
        "- Do NOT create festival_overview with only 5 fields (name, local_name, why_celebrated, short_story, themes)\n"
        "- You MUST include all 10 fields in festival_overview\n"
        "- Ensure all sections are present in the final JSON\n"
        "- Generate metadata with current timestamp and location from request\n"
        "- After calling all agents and collecting their results, return the final JSON\n"
        "- CRITICAL: Your response MUST be valid JSON only. Do NOT include any explanatory text before or after the JSON.\n"
        "- Do NOT say 'A JSON has been created' or similar descriptions. Return ONLY the JSON object.\n"
        "- The final response should be valid JSON starting with '{' and ending with '}'.\n"
        "- If any agent fails, use empty objects/arrays for that section but still include it\n\n"
        "Example workflow:\n"
        "1. Call ResearchAgent: 'Research Nuakhai in Bhubaneswar. Return festival overview JSON.'\n"
        "   → Receives: {name, local_name, origin_story, why_celebrated, themes, symbolism, key_values, family_roles, odisha_flavour, greetings}\n"
        "2. Call PreparationAgent: 'Plan pre-festival for Nuakhai in Bhubaneswar for family of 3 with one child. Return pre_festival JSON.'\n"
        "3. Call ExperienceAgent: 'Plan festival day for Nuakhai in Bhubaneswar for family of 3 with one child. Return festival_day JSON.'\n"
        "4. Call ContentAgent: 'Create shareables. Puja items: [from preparation]. Tasks: [from preparation]. Return shareables JSON.'\n"
        "5. Map research result: origin_story → short_story, include all new fields\n"
        "6. Assemble all results into final FestivalPlan with metadata."
    ),
    tools=[
        research_tool,
        preparation_tool,
        experience_tool,
        content_tool,
        # Note: google_search removed - cannot be used with other tools in Gemini 1.x
    ],
)

logger.info(
    "COORDINATOR_AGENT_INITIALIZED: Multi-agent coordinator created successfully "
    "with %d specialized agent tools",
    len([research_tool, preparation_tool, experience_tool, content_tool]),
)

