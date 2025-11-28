"""
ADK root agent for the Utsava Sathi festival planner.

This agent uses Google Gemini (via Google ADK) plus the `google_search`
tool to generate a FestivalPlan JSON for *any* festival request, using
Odisha-first context when relevant (for example Kartika Purnima).

It follows the style and patterns from the Google AI Agents Intensive
([reference](https://rsvp.withgoogle.com/events/google-ai-agents-intensive_2025)).
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

# Configure logging for agent module
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not API_KEY:
    logger.error(
        "API_KEY_MISSING: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment or .env file. "
        "Checked env vars: GOOGLE_API_KEY=%s, GEMINI_API_KEY=%s",
        bool(os.getenv("GOOGLE_API_KEY")),
        bool(os.getenv("GEMINI_API_KEY")),
    )
    raise RuntimeError(
        "GOOGLE_API_KEY or GEMINI_API_KEY must be set in your environment or .env file "
        "for the Utsava Sathi ADK agent to call Gemini."
    )

logger.info("API_KEY_LOADED: Successfully loaded API key from environment (length=%d)", len(API_KEY))

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

FESTIVAL_PLAN_SCHEMA = """
FestivalPlan JSON schema (you MUST follow this exactly):
{
  "festival_overview": {
    "name": "string",
    "local_name": "string",
    "why_celebrated": "string",
    "short_story": "string",
    "themes": ["string", "..."]
  },
  "pre_festival": {
    "ritual_preparation_steps": ["string", "..."],
    "puja_items_checklist": ["string", "..."],
    "food_preparation": ["string", "..."],
    "popular_places_to_visit": [
      { "place": "string", "suggestion": "string" }
    ],
    "schedule": {
      "T-7_days": ["string", "..."],
      "T-3_days": ["string", "..."],
      "T-1_day": ["string", "..."]
    },
    "guest_or_travel_plan": {
      "is_travel_suggested": true,
      "note": "string"
    }
  },
  "festival_day": {
    "early_morning": ["string", "..."],
    "morning": ["string", "..."],
    "mid_day": ["string", "..."],
    "evening": ["string", "..."],
    "family_friendly_tips": ["string", "..."]
  },
  "shareables": {
    "puja_items_text": "string",
    "tasks_text": "string"
  },
  "metadata": {
    "generated_at": "ISO timestamp string",
    "location_context": "string",
    "agent_version": "string",
    "language": "string"
  }
}
"""


root_agent = Agent(
    name="utsava_sathi_festival_planner",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        # Ask Gemini to return pure JSON so it is easy to parse.
        response_mime_type="application/json",
    ),
    description=(
        "Odisha-first festival planning agent that generates FestivalPlan JSON "
        "for any requested festival and family context."
    ),
    instruction=(
        "You are Utsava Sathi, a helpful Odisha-first festival planning assistant.\n"
        "The user will describe a festival and their family context. Your job is to "
        "produce a single FestivalPlan JSON object that strictly follows this "
        "schema:\n\n"
        f"{FESTIVAL_PLAN_SCHEMA}\n\n"
        "RESPONSE RULES (VERY IMPORTANT):\n"
        "- Respond with **JSON only**. Do not include backticks, markdown, or any "
        "  explanatory text before or after the JSON.\n"
        "- The top-level value must be a single JSON object with exactly these five "
        "  keys: festival_overview, pre_festival, festival_day, shareables, metadata.\n"
        "- All nested keys shown in the schema must be present. Use empty lists [] or "
        "  empty strings \"\" if you have no data, but never omit required keys.\n"
        "- Use valid JSON escaping (double quotes for strings, no single-quote escapes "
        "  like \\' ).\n"
        "- When in doubt, prefer correctness of JSON over extra wording."
    ),
    tools=[google_search],
)

logger.info(
    "ROOT_AGENT_INITIALIZED: Utsava Sathi ADK root_agent defined successfully. "
    "Model=%s, Tools=%d, ResponseMimeType=%s",
    "gemini-2.5-flash-lite",
    len([google_search]),
    "application/json",
)


