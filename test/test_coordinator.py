"""
Test script for coordinator.py
Tests the multi-agent coordinator system end-to-end.
"""

import asyncio
import json
import logging
from google.adk.runners import InMemoryRunner
from utsava_agent.coordinator import coordinator_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_coordinator():
    """Test the coordinator agent with a complete festival planning request."""
    
    logger.info("=" * 60)
    logger.info("Testing Multi-Agent Coordinator System")
    logger.info("=" * 60)
    
    # Test query - full festival planning request
    test_query = "Plan Nuakhai festival in Bhubaneswar, Odisha for a family of 3 with one child."
    
    logger.info(f"Test Query: {test_query}")
    logger.info("-" * 60)
    
    try:
        # Create runner and execute
        runner = InMemoryRunner(agent=coordinator_agent, app_name="test_coordinator")
        logger.info("Running coordinator agent...")
        logger.info("This will orchestrate: Research, Preparation, Experience, and Content agents")
        logger.info("-" * 60)
        
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
                logger.info(f"Event {i}: {type(ev)}")
            return False
        
        logger.info("Raw Response (first 500 chars):")
        logger.info(response_text[:500] + "..." if len(response_text) > 500 else response_text)
        logger.info("-" * 60)
        
        # Clean JSON if needed - extract JSON block even if there's text before/after
        json_text = response_text
        
        # Look for JSON block (may be wrapped in markdown code blocks)
        json_start_markers = ["```json", "```"]
        
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
            
            # Validate top-level structure
            required_sections = [
                "festival_overview",
                "pre_festival",
                "festival_day",
                "shareables",
                "metadata"
            ]
            
            logger.info("Top-Level Structure Validation:")
            all_sections_present = True
            for section in required_sections:
                if section in parsed_json:
                    logger.info(f"  ✅ {section}: Present")
                    if isinstance(parsed_json[section], dict):
                        logger.info(f"     Keys: {list(parsed_json[section].keys())[:5]}...")
                    elif isinstance(parsed_json[section], list):
                        logger.info(f"     Items: {len(parsed_json[section])}")
                else:
                    logger.error(f"  ❌ {section}: MISSING")
                    all_sections_present = False
            
            # Validate festival_overview has all 10 fields
            if "festival_overview" in parsed_json:
                logger.info("-" * 60)
                logger.info("Festival Overview Validation:")
                overview = parsed_json["festival_overview"]
                required_overview_fields = [
                    "name", "local_name", "why_celebrated", "short_story",
                    "themes", "symbolism", "key_values", "family_roles",
                    "odisha_flavour", "greetings"
                ]
                overview_complete = True
                for field in required_overview_fields:
                    if field in overview:
                        logger.info(f"  ✅ {field}: Present")
                    else:
                        logger.error(f"  ❌ {field}: MISSING")
                        overview_complete = False
                
                if not overview_complete:
                    all_sections_present = False
            
            logger.info("-" * 60)
            
            if all_sections_present:
                logger.info("✅ All required sections are present!")
                logger.info("=" * 60)
                logger.info("Pretty JSON Output (abbreviated):")
                # Print a condensed version
                output = {
                    "festival_overview": {
                        "name": parsed_json.get("festival_overview", {}).get("name", "N/A"),
                        "fields_count": len(parsed_json.get("festival_overview", {})),
                    },
                    "pre_festival": {
                        "has_ritual_steps": "ritual_preparation_steps" in parsed_json.get("pre_festival", {}),
                        "has_schedule": "schedule" in parsed_json.get("pre_festival", {}),
                    },
                    "festival_day": {
                        "has_early_morning": "early_morning" in parsed_json.get("festival_day", {}),
                        "has_evening": "evening" in parsed_json.get("festival_day", {}),
                    },
                    "shareables": {
                        "has_puja_items": "puja_items_text" in parsed_json.get("shareables", {}),
                        "has_tasks": "tasks_text" in parsed_json.get("shareables", {}),
                    },
                    "metadata": parsed_json.get("metadata", {}),
                }
                print(json.dumps(output, indent=2, ensure_ascii=False))
                logger.info("=" * 60)
                logger.info("Full JSON saved to coordinator_test_output.json")
                with open("coordinator_test_output.json", "w") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                return True
            else:
                logger.error("❌ Some required sections are missing!")
                logger.info("=" * 60)
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            logger.error(f"JSON text (first 500 chars): {json_text[:500]}")
            logger.info("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running coordinator: {e}", exc_info=True)
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_coordinator())
    exit(0 if success else 1)







