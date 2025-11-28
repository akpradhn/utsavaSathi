"""
Utsava Sathi Agent Module

Exports both the legacy single agent and the new multi-agent coordinator.
Also exports specialized agents for individual testing.
"""

from utsava_agent.agent import root_agent  # Legacy single agent
from utsava_agent.coordinator import coordinator_agent  # New multi-agent coordinator

# Export specialized agents for individual testing
from utsava_agent.agents import (
    content_agent,
    experience_agent,
    preparation_agent,
    research_agent,
)

__all__ = [
    "root_agent",  # Legacy - single agent
    "coordinator_agent",  # New - multi-agent coordinator
    # Specialized agents for individual testing
    "research_agent",
    "preparation_agent",
    "experience_agent",
    "content_agent",
]

