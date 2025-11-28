"""
Test script for content_agent.py
Tests the festival content agent to ensure it works correctly.
"""

import asyncio
import json
import logging
from google.adk.runners import InMemoryRunner
from utsava_agent.agents.content_agent import content_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_content_agent():
    """Test the content agent with a sample festival query."""
    
    logger.info("=" * 60)
    logger.info("Testing Content Agent")
    logger.info("=" * 60)
    
    # Test query - content agent needs puja items and tasks from preparation
    test_query = """Create shareable content for Nuakhai festival. 
Puja items: New rice (paddy), Milk, Flowers, Ghee, Banana, Jaggery, Clay pots, Bamboo baskets, New clothes for family members
Tasks: Purchase new clothes, Clean and decorate house, Prepare traditional sweets, Set up puja altar
Return shareables JSON."""
    
    logger.info(f"Test Query: {test_query[:200]}...")
    logger.info("-" * 60)
    
    try:
        # Create runner and execute
        runner = InMemoryRunner(agent=content_agent, app_name="test_content")
        logger.info("Running content agent...")
        
        events = await runner.run_debug(test_query)
        
        logger.info(f"Received {len(events)} events")
        logger.info("-" * 60)
        
        # Extract response text (using same logic as api.py)
        response_text = ""
        for idx, ev in enumerate(reversed(events)):
            # Try content.parts[0].text (most common in ADK)
            content = getattr(ev, "content", None)
            if content:
                try:
                    parts = getattr(content, "parts", None)
                    if parts:
                        # Handle both iterable and single part
                        if hasattr(parts, "__iter__") and not isinstance(parts, str):
                            parts_list = list(parts)
                        else:
                            parts_list = [parts]
                        
                        for part in parts_list:
                            part_text = getattr(part, "text", None)
                            if isinstance(part_text, str) and part_text.strip():
                                response_text = part_text.strip()
                                break
                        if response_text:
                            break
                except (AttributeError, TypeError, IndexError) as e:
                    logger.debug(f"Error extracting from content.parts in event {idx}: {e}")
            
            # Try direct text attributes
            if not response_text:
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
        
        # Clean JSON if needed - extract JSON block even if there's text before/after
        json_text = response_text
        
        # Look for JSON block (may be wrapped in markdown code blocks)
        json_start_markers = ["```json", "```"]
        json_end_markers = ["```"]
        
        # Try to find JSON block in markdown
        json_start = -1
        json_end = -1
        
        for marker in json_start_markers:
            marker_pos = json_text.find(marker)
            if marker_pos != -1:
                # Find the opening brace after the marker
                brace_pos = json_text.find("{", marker_pos)
                if brace_pos != -1:
                    json_start = brace_pos
                    # Find the closing marker
                    end_marker_pos = json_text.find("```", brace_pos)
                    if end_marker_pos != -1:
                        # Find the last closing brace before the end marker
                        json_end = json_text.rfind("}", marker_pos, end_marker_pos) + 1
                    break
        
        # If no markdown block found, look for JSON directly
        if json_start == -1:
            json_start = json_text.find("{")
            if json_start != -1:
                json_end = json_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_text = json_text[json_start:json_end]
        else:
            # Fallback: try to find any JSON-like structure
            start = json_text.find("{")
            end = json_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_text = json_text[start : end + 1]
        
        # Remove any remaining markdown artifacts
        json_text = json_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        try:
            parsed_json = json.loads(json_text)
            logger.info("✅ Successfully parsed JSON!")
            logger.info("-" * 60)
            
            # Validate required fields for shareables
            required_fields = [
                "puja_items_text",
                "tasks_text"
            ]
            
            logger.info("Field Validation:")
            all_present = True
            for field in required_fields:
                if field in parsed_json:
                    value = parsed_json[field]
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        logger.info(f"  ✅ {field}: {len(value)} characters")
                        logger.info(f"     Preview: {preview}")
                    elif isinstance(value, list):
                        logger.info(f"  ✅ {field}: [{len(value)} items] {value[:3] if value else '[]'}")
                    elif isinstance(value, dict):
                        logger.info(f"  ✅ {field}: {list(value.keys())}")
                    else:
                        logger.info(f"  ✅ {field}: {value}")
                else:
                    logger.error(f"  ❌ {field}: MISSING")
                    all_present = False
            
            # Validate content quality
            if all_present:
                logger.info("-" * 60)
                logger.info("Content Quality Check:")
                
                if "puja_items_text" in parsed_json:
                    puja_text = parsed_json["puja_items_text"]
                    if len(puja_text.strip()) > 0:
                        logger.info(f"  ✅ puja_items_text: Non-empty ({len(puja_text)} chars)")
                    else:
                        logger.warning(f"  ⚠️  puja_items_text: Empty")
                
                if "tasks_text" in parsed_json:
                    tasks_text = parsed_json["tasks_text"]
                    if len(tasks_text.strip()) > 0:
                        logger.info(f"  ✅ tasks_text: Non-empty ({len(tasks_text)} chars)")
                    else:
                        logger.warning(f"  ⚠️  tasks_text: Empty")
            
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
        logger.error(f"❌ Error running content agent: {e}", exc_info=True)
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_content_agent())
    exit(0 if success else 1)



