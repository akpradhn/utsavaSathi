"""
Content Agent - Specialized in generating shareable content.
"""

import logging

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from utsava_agent.agents._shared import API_KEY, retry_config

logger = logging.getLogger(__name__)

content_agent = Agent(
    name="festival_content_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        api_key=API_KEY,
        retry_options=retry_config,
    ),
    description=(
        "Generates shareable text content for social media and messaging, including "
        "puja items checklists and task lists formatted for sharing."
    ),
    instruction=(
        "You are a content specialist for festival planning.\n\n"
        "Given puja items and tasks from the preparation plan, create shareable text content.\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        '  "puja_items_text": "Formatted text with puja items, ready to share on WhatsApp/social media",\n'
        '  "tasks_text": "Formatted text with tasks, ready to share on WhatsApp/social media"\n'
        "}\n\n"
        "IMPORTANT RULES:\n"
        "- Make the text concise, engaging, and easy to read\n"
        "- Include relevant hashtags (2-4 hashtags)\n"
        "- Format for easy sharing (use emojis sparingly, keep it professional)\n"
        "- Puja items text should list items clearly\n"
        "- Tasks text should be actionable and organized\n"
        "- Both texts should be culturally appropriate\n"
        "- Keep each text under 300 characters if possible\n"
        "- Return JSON only - no markdown, no backticks, no explanations\n"
        "- Both fields must be present (use empty strings if needed)"
    ),
    tools=[],  # No search needed, just content formatting
)

logger.info("CONTENT_AGENT_INITIALIZED: Festival content agent created successfully")

