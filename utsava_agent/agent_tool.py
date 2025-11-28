"""
Custom tool for agent-to-agent calls in ADK.

This module provides a tool wrapper that allows one agent to call another agent
as a tool, enabling multi-agent coordination.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from typing import Any, Dict

from google.adk.runners import InMemoryRunner

logger = logging.getLogger(__name__)


def create_agent_tool(agent, agent_name: str):
    """
    Create a tool that wraps an agent, allowing it to be called by another agent.
    
    ADK tools need to be synchronous, so this creates a sync wrapper that handles
    async agent execution internally.
    
    Args:
        agent: The ADK Agent instance to wrap
        agent_name: Name identifier for the agent
    
    Returns:
        A synchronous callable tool function that can be used in another agent's tools list
    """
    
    def agent_tool(prompt: str) -> str:
        """
        Execute the wrapped agent with the given prompt.
        
        Args:
            prompt: The prompt/request to send to the agent
        
        Returns:
            The agent's response as a string (JSON expected)
        """
        try:
            logger.info(
                f"AGENT_TOOL_CALL: Calling {agent_name} with prompt length={len(prompt)}"
            )
            
            # Run async agent execution in event loop
            async def run_agent():
                runner = InMemoryRunner(agent=agent, app_name="utsava_agent")
                return await runner.run_debug(prompt)
            
            # Handle event loop (support both existing and new loops)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we need to use a different approach
                    # Create a new thread with a new loop
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(run_agent())
                        )
                        events = future.result()
                else:
                    events = loop.run_until_complete(run_agent())
            except RuntimeError:
                # No event loop exists, create one
                events = asyncio.run(run_agent())
            
            # Extract text from events (similar to api.py logic)
            last_text = ""
            for ev in reversed(events):
                # Try direct text attributes
                text = getattr(ev, "output_text", None) or getattr(ev, "output", None)
                if isinstance(text, str) and text.strip():
                    last_text = text.strip()
                    break
                
                # Try content.parts[0].text
                content = getattr(ev, "content", None)
                if content:
                    try:
                        parts = getattr(content, "parts", None)
                        if parts and hasattr(parts, "__iter__") and not isinstance(parts, str):
                            parts_list = list(parts)
                            if len(parts_list) > 0:
                                first_part = parts_list[0]
                                part_text = getattr(first_part, "text", None)
                                if isinstance(part_text, str) and part_text.strip():
                                    last_text = part_text.strip()
                                    break
                    except (AttributeError, TypeError, IndexError):
                        pass
                
                # Try ev.text
                if hasattr(ev, "text"):
                    ev_text = getattr(ev, "text")
                    if isinstance(ev_text, str) and ev_text.strip():
                        last_text = ev_text.strip()
                        break
            
            # Clean JSON if needed
            if last_text:
                # Extract JSON block if wrapped in markdown
                start = last_text.find("{")
                end = last_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    last_text = last_text[start : end + 1]
                
                # Fix common JSON issues
                last_text = last_text.replace("\\'", "'")
                last_text = last_text.replace("```json", "").replace("```", "").strip()
            
            logger.info(
                f"AGENT_TOOL_SUCCESS: {agent_name} returned response length={len(last_text)}"
            )
            
            # Log the actual output for research_agent to help debug
            if agent_name == "research_agent":
                logger.info(
                    f"RESEARCH_AGENT_OUTPUT: Full response from research_agent:\n{last_text[:1000]}"
                )
                # Try to parse and log structured output
                try:
                    import json
                    parsed = json.loads(last_text)
                    logger.info(
                        f"RESEARCH_AGENT_PARSED: Successfully parsed JSON. Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}"
                    )
                    if isinstance(parsed, dict):
                        required_fields = ["name", "local_name", "origin_story", "why_celebrated", 
                                         "themes", "symbolism", "key_values", "family_roles", 
                                         "odisha_flavour", "greetings"]
                        for key in required_fields:
                            present = key in parsed
                            value_preview = str(parsed.get(key, ""))[:50] if present else "MISSING"
                            logger.info(
                                f"RESEARCH_AGENT_FIELD: {key} = {'PRESENT' if present else 'MISSING'} ({value_preview})"
                            )
                except Exception as parse_exc:
                    logger.warning(
                        f"RESEARCH_AGENT_PARSE_FAILED: Could not parse as JSON: {parse_exc}"
                    )
            
            return last_text
            
        except Exception as exc:
            logger.error(
                f"AGENT_TOOL_ERROR: {agent_name} failed with error: {exc}",
                exc_info=True,
            )
            return json.dumps({"error": f"{agent_name} failed: {str(exc)}"})
    
    # Set metadata for the tool
    agent_tool.__name__ = f"call_{agent_name}"
    agent_tool.__doc__ = f"Call the {agent_name} to handle: {agent.description}"
    
    return agent_tool



