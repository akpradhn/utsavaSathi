"""
Example implementation of Multi-Agent Architecture for Utsava Sathi

This is a reference implementation showing how the multi-agent system
would be structured. This file is for reference only - actual implementation
should be in separate files as outlined in MULTI_AGENT_ARCHITECTURE.md
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

logger = logging.getLogger(__name__)
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# ============================================================================
# SPECIALIZED AGENTS
# ============================================================================

def create_research_agent() -> Agent:
    """Research Agent - Handles festival overview research."""
    return Agent(
        name="festival_research_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            api_key=API_KEY,
            retry_options=retry_config,
            response_mime_type="application/json",
        ),
        description="Researches and generates festival overview information",
        instruction=(
            "You are a festival research specialist focused on Odisha festivals.\n"
            "Your task is to research a festival and return ONLY a JSON object with this structure:\n"
            "{\n"
            '  "name": "Festival name in English",\n'
            '  "local_name": "Local/Odia name",\n'
            '  "why_celebrated": "Why this festival is celebrated",\n'
            '  "short_story": "Brief story/legend about the festival",\n'
            '  "themes": ["theme1", "theme2", ...]\n'
            "}\n\n"
            "Focus on Odisha-first context. Use google_search to find accurate information.\n"
            "Return JSON only, no markdown or explanations."
        ),
        tools=[google_search],
    )


def create_preparation_agent() -> Agent:
    """Preparation Agent - Handles pre-festival planning."""
    return Agent(
        name="festival_preparation_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            api_key=API_KEY,
            retry_options=retry_config,
            response_mime_type="application/json",
        ),
        description="Plans pre-festival activities and preparations",
        instruction=(
            "You are a festival preparation specialist.\n"
            "Your task is to create a pre-festival plan and return ONLY a JSON object:\n"
            "{\n"
            '  "ritual_preparation_steps": ["step1", "step2", ...],\n'
            '  "puja_items_checklist": ["item1", "item2", ...],\n'
            '  "food_preparation": ["dish1", "dish2", ...],\n'
            '  "popular_places_to_visit": [\n'
            '    {"place": "name", "suggestion": "why visit"},\n'
            '    ...\n'
            '  ],\n'
            '  "schedule": {\n'
            '    "T-7_days": ["task1", ...],\n'
            '    "T-3_days": ["task2", ...],\n'
            '    "T-1_day": ["task3", ...]\n'
            '  },\n'
            '  "guest_or_travel_plan": {\n'
            '    "is_travel_suggested": true/false,\n'
            '    "note": "explanation"\n'
            '  }\n'
            "}\n\n"
            "Consider the location and family context provided. Use google_search for places and recipes.\n"
            "Return JSON only."
        ),
        tools=[google_search],
    )


def create_experience_agent() -> Agent:
    """Experience Agent - Handles festival day planning."""
    return Agent(
        name="festival_experience_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            api_key=API_KEY,
            retry_options=retry_config,
            response_mime_type="application/json",
        ),
        description="Plans the festival day experience",
        instruction=(
            "You are a festival day experience specialist.\n"
            "Your task is to plan the festival day and return ONLY a JSON object:\n"
            "{\n"
            '  "early_morning": ["activity1", "activity2", ...],\n'
            '  "morning": ["activity1", ...],\n'
            '  "mid_day": ["activity1", ...],\n'
            '  "evening": ["activity1", ...],\n'
            '  "family_friendly_tips": ["tip1", "tip2", ...]\n'
            "}\n\n"
            "Consider family context (especially children). Make activities engaging and appropriate.\n"
            "Return JSON only."
        ),
        tools=[google_search],
    )


def create_content_agent() -> Agent:
    """Content Agent - Generates shareable content."""
    return Agent(
        name="festival_content_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            api_key=API_KEY,
            retry_options=retry_config,
        ),
        description="Generates shareable content for social media",
        instruction=(
            "You are a content specialist for festival planning.\n"
            "Given puja items and tasks, create shareable text content.\n"
            "Return ONLY a JSON object:\n"
            "{\n"
            '  "puja_items_text": "Formatted text with puja items, ready to share",\n'
            '  "tasks_text": "Formatted text with tasks, ready to share"\n'
            "}\n\n"
            "Make the text concise, engaging, and include relevant hashtags.\n"
            "Return JSON only."
        ),
        tools=[],  # No search needed, just formatting
    )


# ============================================================================
# COORDINATOR AGENT
# ============================================================================

def create_coordinator_agent(
    research_agent: Agent,
    preparation_agent: Agent,
    experience_agent: Agent,
    content_agent: Agent,
) -> Agent:
    """
    Coordinator Agent - Orchestrates all specialized agents.
    
    Note: In ADK, agents can call other agents. The coordinator would:
    1. Parse user request
    2. Call research_agent for festival_overview
    3. Call preparation_agent for pre_festival (can be parallel with research)
    4. Call experience_agent for festival_day (can be parallel)
    5. Call content_agent for shareables (after preparation)
    6. Aggregate all results into final FestivalPlan
    7. Add metadata
    """
    return Agent(
        name="utsava_coordinator",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            api_key=API_KEY,
            retry_options=retry_config,
            response_mime_type="application/json",
        ),
        description="Coordinates festival planning across specialized agents",
        instruction=(
            "You are the Utsava Sathi coordinator that orchestrates festival planning.\n\n"
            "WORKFLOW:\n"
            "1. Parse the user request to extract: festival name, location, family context\n"
            "2. Delegate tasks to specialized agents:\n"
            "   - Call research_agent for festival overview\n"
            "   - Call preparation_agent for pre-festival planning\n"
            "   - Call experience_agent for festival day planning\n"
            "   - Call content_agent for shareables (after getting preparation results)\n"
            "3. Collect all results\n"
            "4. Assemble final FestivalPlan JSON with this structure:\n"
            "{\n"
            '  "festival_overview": {...},  // from research_agent\n'
            '  "pre_festival": {...},       // from preparation_agent\n'
            '  "festival_day": {...},       // from experience_agent\n'
            '  "shareables": {...},         // from content_agent\n'
            '  "metadata": {\n'
            '    "generated_at": "ISO timestamp",\n'
            '    "location_context": "location from request",\n'
            '    "agent_version": "multi_agent_v1",\n'
            '    "language": "en"\n'
            '  }\n'
            "}\n\n"
            "Ensure all sections are present and valid JSON.\n"
            "Return JSON only, no markdown."
        ),
        tools=[
            # In ADK, you can pass agents as tools/sub-agents
            # This is conceptual - actual implementation depends on ADK's agent calling mechanism
            google_search,
        ],
    )


# ============================================================================
# USAGE EXAMPLE (Conceptual)
# ============================================================================

async def example_usage():
    """
    Example of how the multi-agent system would be used.
    
    Note: This is conceptual. Actual implementation would depend on:
    - How ADK handles agent-to-agent calls
    - Whether agents can be passed as tools
    - Parallel execution capabilities
    """
    # Create specialized agents
    research_agent = create_research_agent()
    preparation_agent = create_preparation_agent()
    experience_agent = create_experience_agent()
    content_agent = create_content_agent()
    
    # Create coordinator
    coordinator = create_coordinator_agent(
        research_agent,
        preparation_agent,
        experience_agent,
        content_agent,
    )
    
    # User request
    user_prompt = "Plan Nuakhai in Bhubaneswar for a family of 3 with one small child"
    
    # Run coordinator (which internally calls other agents)
    # from google.adk.runners import InMemoryRunner
    # runner = InMemoryRunner(agent=coordinator, app_name="utsava_agent")
    # events = await runner.run_debug(user_prompt)
    # result = extract_json_from_events(events)
    
    # Alternative: Manual orchestration (if ADK doesn't support agent-to-agent calls directly)
    # This would be done in the coordinator's logic or in the API layer
    pass


# ============================================================================
# ALTERNATIVE: Manual Orchestration Pattern
# ============================================================================

async def manual_orchestration_example(user_prompt: str) -> Dict[str, Any]:
    """
    Alternative approach: Manual orchestration in API/coordinator logic.
    
    This pattern would be used if ADK doesn't support direct agent-to-agent calls.
    The coordinator logic would be in Python code rather than in the agent itself.
    """
    from google.adk.runners import InMemoryRunner
    from datetime import datetime
    
    # Create agents
    research_agent = create_research_agent()
    preparation_agent = create_preparation_agent()
    experience_agent = create_experience_agent()
    content_agent = create_content_agent()
    
    # Step 1: Research (can be done in parallel with preparation/experience)
    research_runner = InMemoryRunner(agent=research_agent, app_name="utsava_agent")
    research_prompt = f"Research this festival: {user_prompt}. Return festival_overview JSON."
    research_events = await research_runner.run_debug(research_prompt)
    festival_overview = extract_json_from_events(research_events)
    
    # Step 2: Preparation (parallel with experience)
    prep_runner = InMemoryRunner(agent=preparation_agent, app_name="utsava_agent")
    prep_prompt = f"Plan pre-festival activities for: {user_prompt}. Return pre_festival JSON."
    prep_events = await prep_runner.run_debug(prep_prompt)
    pre_festival = extract_json_from_events(prep_events)
    
    # Step 3: Experience (parallel with preparation)
    exp_runner = InMemoryRunner(agent=experience_agent, app_name="utsava_agent")
    exp_prompt = f"Plan festival day experience for: {user_prompt}. Return festival_day JSON."
    exp_events = await exp_runner.run_debug(exp_prompt)
    festival_day = extract_json_from_events(exp_events)
    
    # Step 4: Content (depends on preparation)
    content_runner = InMemoryRunner(agent=content_agent, app_name="utsava_agent")
    content_prompt = (
        f"Create shareable content. Puja items: {pre_festival.get('puja_items_checklist', [])}. "
        f"Tasks: {pre_festival.get('ritual_preparation_steps', [])}. Return shareables JSON."
    )
    content_events = await content_runner.run_debug(content_prompt)
    shareables = extract_json_from_events(content_events)
    
    # Step 5: Assemble final plan
    festival_plan = {
        "festival_overview": festival_overview,
        "pre_festival": pre_festival,
        "festival_day": festival_day,
        "shareables": shareables,
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "location_context": extract_location(user_prompt),
            "agent_version": "multi_agent_v1",
            "language": "en",
        },
    }
    
    return festival_plan


def extract_json_from_events(events) -> Dict[str, Any]:
    """Helper to extract JSON from ADK events (simplified)."""
    # This would use the same logic as in ui/api.py
    import json
    # ... implementation ...
    return {}


def extract_location(prompt: str) -> str:
    """Helper to extract location from prompt."""
    # Simple extraction - could be enhanced
    if "Bhubaneswar" in prompt:
        return "Bhubaneswar, Odisha, India"
    # ... more logic ...
    return "Odisha, India"

