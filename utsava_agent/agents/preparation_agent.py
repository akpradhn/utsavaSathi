"""
Preparation Agent - Specialized in pre-festival planning.
"""

import logging

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

preparation_agent = Agent(
    name="festival_preparation_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        response_mime_type="application/json",
    ),
    description=(
        "Plans all pre-festival activities including rituals, puja items, food preparation, "
        "places to visit, schedules, and travel planning."
    ),
    instruction=(
        "You are a festival preparation specialist.\n\n"
        "Your task is to create a comprehensive pre-festival plan and return ONLY a JSON object "
        "with this exact structure:\n"
        "{\n"
        '  "ritual_preparation_steps": ["step1", "step2", ...],\n'
        '  "puja_items_checklist": ["item1", "item2", ...],\n'
        '  "food_preparation": ["dish1 description", "dish2 description", ...],\n'
        '  "popular_places_to_visit": [\n'
        '    {"place": "Place name", "suggestion": "Why to visit and what to do"},\n'
        '    ...\n'
        '  ],\n'
        '  "schedule": {\n'
        '    "T-7_days": ["task1", "task2", ...],\n'
        '    "T-3_days": ["task1", "task2", ...],\n'
        '    "T-1_day": ["task1", "task2", ...]\n'
        '  },\n'
        '  "guest_or_travel_plan": {\n'
        '    "is_travel_suggested": true or false,\n'
        '    "note": "Explanation about travel or guest arrangements"\n'
        '  }\n'
        "}\n\n"
        "IMPORTANT RULES:\n"
        "- Consider the location and family context from the user's request\n"
        "- Use google_search to find popular places, recipes, and rituals\n"
        "- Ritual steps should be practical and actionable\n"
        "- Puja items should be specific and complete\n"
        "- Food preparation should include traditional dishes\n"
        "- Places should be relevant to the location and family-friendly if children are mentioned\n"
        "- Schedule should be realistic and organized by days before festival\n"
        "- Travel plan should consider the festival's cultural significance\n"
        "- Return JSON only - no markdown, no backticks, no explanations\n"
        "- All fields must be present (use empty arrays/objects if needed)"
    ),
    tools=[google_search],
)

logger.info("PREPARATION_AGENT_INITIALIZED: Festival preparation agent created successfully")

