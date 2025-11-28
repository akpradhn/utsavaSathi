"""
Test script to check if ParallelAgent works with ADK.
Based on the Kaggle notebook: day-1b-agent-architectures
"""

import asyncio
import logging
from google.adk.agents import Agent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY must be set")

# Create two simple agents that can run in parallel
agent1 = Agent(
    name="Agent1",
    model=Gemini(model="gemini-2.5-flash-lite", api_key=API_KEY),
    instruction="You are Agent 1. Answer concisely in 1-2 sentences.",
    tools=[google_search],
)

agent2 = Agent(
    name="Agent2",
    model=Gemini(model="gemini-2.5-flash-lite", api_key=API_KEY),
    instruction="You are Agent 2. Answer concisely in 1-2 sentences.",
    tools=[google_search],
)

# Try to create a ParallelAgent
try:
    parallel_agent = ParallelAgent(
        name="ParallelTestAgent",
        sub_agents=[agent1, agent2],
    )
    logger.info("✅ ParallelAgent created successfully!")
    logger.info(f"ParallelAgent type: {type(parallel_agent)}")
    logger.info(f"ParallelAgent attributes: {dir(parallel_agent)}")
    
    # Test running it
    async def test_parallel():
        runner = InMemoryRunner(agent=parallel_agent, app_name="test_parallel")
        events = await runner.run_debug("What is Diwali?")
        
        logger.info(f"Received {len(events)} events")
        for i, ev in enumerate(events):
            logger.info(f"Event {i}: {type(ev)}")
            if hasattr(ev, "output_text"):
                logger.info(f"  Output: {ev.output_text[:200]}")
            if hasattr(ev, "content"):
                logger.info(f"  Content: {ev.content}")
        
        return events
    
    logger.info("Testing ParallelAgent execution...")
    events = asyncio.run(test_parallel())
    logger.info("✅ ParallelAgent test completed!")
    
except ImportError as e:
    logger.error(f"❌ ParallelAgent not available: {e}")
    logger.info("Trying alternative import paths...")
    
    # Try alternative imports
    try:
        from google.adk import ParallelAgent as PA
        logger.info("✅ Found ParallelAgent in google.adk")
    except ImportError:
        try:
            from google.adk.workflow import ParallelAgent as PA
            logger.info("✅ Found ParallelAgent in google.adk.workflow")
        except ImportError:
            logger.error("❌ ParallelAgent not found in any expected location")
            logger.info("Available google.adk modules:")
            import google.adk
            logger.info(f"  {dir(google.adk)}")
            
except Exception as e:
    logger.error(f"❌ Error creating/running ParallelAgent: {e}", exc_info=True)

