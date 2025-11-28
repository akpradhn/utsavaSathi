"""
Research Agent - Specialized in festival overview research.
"""

import logging

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

FESTIVAL_OVERVIEW_SCHEMA = """
Festival Overview JSON schema (you MUST follow this exactly):
{
  "name": "string",
  "local_name": "string",
  "origin_story": "string",
  "why_celebrated": "string",
  "themes": ["string", "..."],
  "symbolism": ["string", "..."],
  "key_values": ["string", "..."],
  "family_roles": {
    "elders": "string",
    "parents": "string",
    "children": "string"
  },
  "odisha_flavour": "string",
  "greetings": ["string", "..."]
}
"""

research_agent = Agent(
    name="festival_research_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
        # Ask Gemini to return pure JSON so it is easy to parse.
        response_mime_type="application/json",
    ),
    description=(
        "Researches and generates festival overview information including name, "
        "local name, origin story, significance, themes, symbolism, and cultural context. "
        "Specialized in Indian festivals with Odisha-specific details when relevant."
    ),
    instruction=(
        "You are Utsava Sathi's Festival Overview Specialist.\n\n"
        "Given a festival and a location, return a concise cultural summary as JSON.\n\n"
        "Requirements:\n"
        "- Focus on Indian context; give Odisha-specific details if relevant.\n"
        "- Be warm, accurate, and family-friendly.\n"
        "- Keep text short: origin_story max 3 sentences, why_celebrated max 2.\n"
        "- Do NOT add explanations outside JSON.\n\n"
        "Fields and meaning:\n"
        "- name: common English name.\n"
        "- local_name: local or regional name (Odia if applicable).\n"
        "- origin_story: very short story or background (max 3 sentences).\n"
        "- why_celebrated: what it honors / main purpose (max 2 sentences).\n"
        "- themes: 3–6 high-level themes (e.g. Family, Harvest, Devotion).\n"
        "- symbolism: 3–6 important symbols, foods, colors, or objects.\n"
        "- key_values: 3–6 values (e.g. Gratitude, Courage).\n"
        "- family_roles: one short line each for elders, parents, children.\n"
        "- odisha_flavour: how Odisha celebrates it (1–2 sentences; \"\" if not relevant).\n"
        "- greetings: common short greeting phrases.\n\n"
        f"Return ONLY a JSON object that strictly follows this schema:\n\n"
        f"{FESTIVAL_OVERVIEW_SCHEMA}\n\n"
        "RESPONSE RULES (VERY IMPORTANT):\n"
        "- Respond with **JSON only**. Do not include backticks, markdown, or any "
        "  explanatory text before or after the JSON.\n"
        "- The top-level value must be a single JSON object with exactly these fields:\n"
        "  name, local_name, origin_story, why_celebrated, themes, symbolism, key_values, "
        "  family_roles, odisha_flavour, greetings.\n"
        "- All fields shown in the schema must be present. Use empty lists [] or "
        "  empty strings \"\" if you have no data, but never omit required fields.\n"
        "- family_roles must be an object with exactly three keys: elders, parents, children.\n"
        "- Use valid JSON escaping (double quotes for strings, no single-quote escapes "
        "  like \\' ).\n"
        "- Use google_search to find accurate, current information.\n"
        "- When in doubt, prefer correctness of JSON over extra wording."
    ),
    tools=[google_search],
)

logger.info(
    "RESEARCH_AGENT_INITIALIZED: Festival research agent created successfully. "
    "Model=%s, Tools=%d, ResponseMimeType=%s",
    "gemini-2.5-flash-lite",
    len([google_search]),
    "application/json",
)
