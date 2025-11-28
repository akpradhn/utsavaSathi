"""
ADK root agent for the Utsava Sathi festival planner.

This agent uses Google Gemini (via Google ADK) plus the `google_search`
tool to generate a FestivalPlan JSON for *any* festival request, using
Odisha-first context when relevant (for example Kartika Purnima).

It follows the style and patterns from the Google AI Agents Intensive
([reference](https://rsvp.withgoogle.com/events/google-ai-agents-intensive_2025)).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY or GEMINI_API_KEY must be set in your environment or .env file "
        "for the Utsava Sathi ADK agent to call Gemini."
    )

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
    ),
    description=(
        "Odisha-first festival planning agent that generates FestivalPlan JSON "
        "for any requested festival and family context."
    ),
    instruction=(
        "You are Utsava Sathi, a helpful Odisha-first festival planning assistant.\n"
        "Given a user request (for example: "
        "'Plan Kartika Purnima in Bhubaneswar for a family of 4 with a small child'), "
        "you MUST:\n"
        "1. Use the google_search tool whenever you need up-to-date information "
        "   about the festival, Odia traditions, or local places.\n"
        "2. Think step by step about each part of the plan: festival_overview, "
        "   pre_festival, festival_day, shareables, and metadata.\n"
        "3. Respond with a SINGLE JSON object that EXACTLY matches this schema "
        "(no extra top-level keys, no renaming fields):\n\n"
        f"{FESTIVAL_PLAN_SCHEMA}\n\n"
        "Fill all keys. Use empty lists where appropriate, but never omit any "
        "required key. Do not wrap the JSON in backticks or add commentary."
    ),
    tools=[google_search],
)

print("✅ Utsava Sathi ADK root_agent defined.")


