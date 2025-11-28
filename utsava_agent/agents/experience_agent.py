"""
Experience Agent - Specialized in festival day planning.
"""

import logging

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

experience_agent = Agent(
    name="festival_experience_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        response_mime_type="application/json",
    ),
    description=(
        "Plans the festival day experience including activities for early morning, morning, "
        "mid-day, evening, and family-friendly tips."
    ),
    instruction=(
        "You are a festival day experience specialist.\n\n"
        "Your task is to plan the festival day experience and return ONLY a JSON object "
        "with this exact structure:\n"
        "{\n"
        '  "early_morning": ["activity1", "activity2", ...],\n'
        '  "morning": ["activity1", "activity2", ...],\n'
        '  "mid_day": ["activity1", "activity2", ...],\n'
        '  "evening": ["activity1", "activity2", ...],\n'
        '  "family_friendly_tips": ["tip1", "tip2", ...]\n'
        "}\n\n"
        "IMPORTANT RULES:\n"
        "- Consider the family context from the user's request (especially children)\n"
        "- Activities should be appropriate for the time of day\n"
        "- Early morning activities typically include rituals, prayers, bathing\n"
        "- Morning activities include main rituals, puja, family gatherings\n"
        "- Mid-day activities include meals, rest, community activities\n"
        "- Evening activities include celebrations, socializing, cultural events\n"
        "- Family-friendly tips should help parents engage children meaningfully\n"
        "- Use google_search to find accurate day-of rituals and activities\n"
        "- Make activities engaging and culturally appropriate\n"
        "- Return JSON only - no markdown, no backticks, no explanations\n"
        "- All fields must be present (use empty arrays if needed)"
    ),
    tools=[google_search],
)

logger.info("EXPERIENCE_AGENT_INITIALIZED: Festival experience agent created successfully")

