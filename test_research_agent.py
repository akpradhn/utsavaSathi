"""
Test script for research_agent.py
Tests the festival research agent to ensure it works correctly.
"""

import asyncio
import json
import logging
from google.adk.runners import InMemoryRunner
from utsava_agent.agents.research_agent import research_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_research_agent():
    """Test the research agent with a sample festival query."""
    
    logger.info("=" * 60)
    logger.info("Testing Research Agent")
    logger.info("=" * 60)
    
    # Test query
    test_query = "Research Nuakhai festival in Bhubaneswar, Odisha. Return festival overview JSON."
    
    logger.info(f"Test Query: {test_query}")
    logger.info("-" * 60)
    
    try:
        # Create runner and execute
        runner = InMemoryRunner(agent=research_agent, app_name="test_research")
        logger.info("Running research agent...")
        
        events = await runner.run_debug(test_query)
        
        logger.info(f"Received {len(events)} events")
        logger.info("-" * 60)
        
        # Extract response text (similar to api.py logic)
        response_text = ""
        for ev in reversed(events):
            # Try content.parts[0].text (most common in ADK)
            content = getattr(ev, "content", None)
            if content:
                try:
                    parts = getattr(content, "parts", None)
                    if parts:
                        parts_list = list(parts) if hasattr(parts, "__iter__") and not isinstance(parts, str) else [parts]
                        for part in parts_list:
                            part_text = getattr(part, "text", None)
                            if isinstance(part_text, str) and part_text.strip():
                                response_text = part_text.strip()
                                break
                        if response_text:
                            break
                except (AttributeError, TypeError, IndexError) as e:
                    logger.debug(f"Error extracting from content.parts: {e}")
            
            # Try direct text attributes
            text = getattr(ev, "output_text", None) or getattr(ev, "output", None) or getattr(ev, "text", None)
            if isinstance(text, str) and text.strip():
                response_text = text.strip()
                break
        
        if not response_text:
            logger.error("❌ No response text found in events")
            for i, ev in enumerate(events):
                logger.info(f"Event {i}: {type(ev)} - {ev}")
            return False
        
        logger.info("Raw Response:")
        logger.info(response_text[:500] + "..." if len(response_text) > 500 else response_text)
        logger.info("-" * 60)
        
        # Clean JSON if needed
        json_text = response_text
        start = json_text.find("{")
        end = json_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_text = json_text[start : end + 1]
        
        # Remove markdown code blocks if present
        json_text = json_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        try:
            parsed_json = json.loads(json_text)
            logger.info("✅ Successfully parsed JSON!")
            logger.info("-" * 60)
            
            # Validate required fields
            required_fields = [
                "name", "local_name", "origin_story", "why_celebrated",
                "themes", "symbolism", "key_values", "family_roles",
                "odisha_flavour", "greetings"
            ]
            
            logger.info("Field Validation:")
            all_present = True
            for field in required_fields:
                if field in parsed_json:
                    value = parsed_json[field]
                    if isinstance(value, str):
                        preview = value[:50] + "..." if len(value) > 50 else value
                        logger.info(f"  ✅ {field}: {preview}")
                    elif isinstance(value, list):
                        logger.info(f"  ✅ {field}: [{len(value)} items] {value[:3] if value else '[]'}")
                    elif isinstance(value, dict):
                        logger.info(f"  ✅ {field}: {list(value.keys())}")
                    else:
                        logger.info(f"  ✅ {field}: {value}")
                else:
                    logger.error(f"  ❌ {field}: MISSING")
                    all_present = False
            
            # Validate family_roles structure
            if "family_roles" in parsed_json:
                family_roles = parsed_json["family_roles"]
                if isinstance(family_roles, dict):
                    required_roles = ["elders", "parents", "children"]
                    for role in required_roles:
                        if role in family_roles:
                            logger.info(f"    ✅ family_roles.{role}: {family_roles[role][:50]}")
                        else:
                            logger.error(f"    ❌ family_roles.{role}: MISSING")
                            all_present = False
                else:
                    logger.error(f"  ❌ family_roles is not a dict: {type(family_roles)}")
                    all_present = False
            
            logger.info("-" * 60)
            
            if all_present:
                logger.info("✅ All required fields are present!")
                logger.info("=" * 60)
                logger.info("Pretty JSON Output:")
                print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ Some required fields are missing!")
                logger.info("=" * 60)
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            logger.error(f"JSON text (first 500 chars): {json_text[:500]}")
            logger.info("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running research agent: {e}", exc_info=True)
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_research_agent())
    exit(0 if success else 1)

