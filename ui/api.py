"""
FastAPI backend for Utsava Sathi.

Exposes a `/plan` endpoint that accepts a natural-language festival
planning request and returns a FestivalPlan JSON. It calls the ADK
`root_agent` defined in `utsava_agent/agent.py`, which uses Google
Gemini and `google_search` to generate the plan following the schema.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Ensure project root on sys.path so `utsava_agent` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
    logger.debug("SYSPATH_UPDATED: Added project root to sys.path: %s", ROOT_DIR)

try:
    from utsava_agent.agent import root_agent  # type: ignore
    logger.info("ROOT_AGENT_IMPORTED: Successfully imported root_agent from utsava_agent.agent")
except Exception as exc:
    logger.error(
        "ROOT_AGENT_IMPORT_FAILED: Failed to import root_agent. Error=%s, Traceback=%s",
        exc,
        traceback.format_exc(),
    )
    raise

load_dotenv()
logger.info("ENV_LOADED: Environment variables loaded from .env file")

app = FastAPI(
    title="Utsava Sathi FestivalPlan API",
    description="Generates FestivalPlan JSON for Odisha-first festivals via Gemini.",
)


class PlanRequest(BaseModel):
    """Incoming festival planning request."""

    prompt: str  # free-form text describing festival + family context


@app.post("/plan")
async def plan_festival(req: PlanRequest) -> Dict[str, Any]:
    """
    Call the ADK root_agent with the given prompt and return a parsed
    FestivalPlan JSON object.
    """
    logger.info(
        "PLAN_REQUEST_RECEIVED: Processing festival planning request. "
        "Prompt length=%d, Prompt preview=%s",
        len(req.prompt),
        req.prompt[:100] if len(req.prompt) > 100 else req.prompt,
    )

    # Pass an explicit app_name to avoid ADK's "app name mismatch" warning.
    runner = InMemoryRunner(agent=root_agent, app_name="utsava_agent")
    logger.debug("RUNNER_CREATED: InMemoryRunner initialized with app_name=utsava_agent")
    
    try:
        # Use run_debug() which returns a list of events
        logger.debug("AGENT_EXECUTION_START: Calling runner.run_debug() with prompt")
        events = await runner.run_debug(req.prompt)
        logger.info(
            "AGENT_EXECUTION_SUCCESS: Agent execution completed. "
            "Total events=%d, Event types=%s",
            len(events),
            [type(ev).__name__ for ev in events[-5:]] if events else [],
        )
    except Exception as exc:
        logger.error(
            "AGENT_EXECUTION_FAILED: Runner execution failed. "
            "Error type=%s, Error message=%s, Traceback=%s",
            type(exc).__name__,
            str(exc),
            traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {exc}",
        ) from exc

    # Extract the last meaningful text chunk from the events.
    # ADK events have a `content` attribute with `parts` containing the actual text.
    logger.debug("TEXT_EXTRACTION_START: Attempting to extract text from %d events", len(events))
    last_text = ""
    extraction_method = None
    
    for idx, ev in enumerate(reversed(events)):
        ev_type = type(ev).__name__
        logger.debug(
            "TEXT_EXTRACTION_ATTEMPT: Processing event %d/%d, Type=%s, Attributes=%s",
            idx + 1,
            len(events),
            ev_type,
            [attr for attr in dir(ev) if not attr.startswith("_")],
        )
        
        # Try direct text attributes first
        text = getattr(ev, "output_text", None) or getattr(ev, "output", None)
        if isinstance(text, str) and text.strip():
            last_text = text.strip()
            extraction_method = "output_text/output"
            logger.info(
                "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d, Preview=%s",
                extraction_method,
                len(last_text),
                last_text[:100],
            )
            break
        
        # Try extracting from content.parts[0].text (ADK structure)
        content = getattr(ev, "content", None)
        if content:
            # content might be a Content object with parts attribute
            try:
                parts = getattr(content, "parts", None)
                if parts:
                    # parts might be a list or iterable
                    if hasattr(parts, "__iter__") and not isinstance(parts, str):
                        parts_list = list(parts)
                        logger.debug(
                            "TEXT_EXTRACTION_PARTS: Found %d parts in content.parts",
                            len(parts_list),
                        )
                        if len(parts_list) > 0:
                            first_part = parts_list[0]
                            part_text = getattr(first_part, "text", None)
                            if isinstance(part_text, str) and part_text.strip():
                                last_text = part_text.strip()
                                extraction_method = "content.parts[0].text"
                                logger.info(
                                    "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d, Preview=%s",
                                    extraction_method,
                                    len(last_text),
                                    last_text[:100],
                                )
                                break
            except (AttributeError, TypeError, IndexError) as parts_exc:
                logger.debug(
                    "TEXT_EXTRACTION_PARTS_ERROR: Failed to extract from parts. Error=%s",
                    parts_exc,
                )
            
            # Also try if content itself has text
            content_text = getattr(content, "text", None)
            if isinstance(content_text, str) and content_text.strip():
                last_text = content_text.strip()
                extraction_method = "content.text"
                logger.info(
                    "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d, Preview=%s",
                    extraction_method,
                    len(last_text),
                    last_text[:100],
                )
                break
        
        # Try if event itself has text in a different attribute
        if hasattr(ev, "text"):
            ev_text = getattr(ev, "text")
            if isinstance(ev_text, str) and ev_text.strip():
                last_text = ev_text.strip()
                extraction_method = "ev.text"
                logger.info(
                    "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d, Preview=%s",
                    extraction_method,
                    len(last_text),
                    last_text[:100],
                )
                break

    # If we still don't have text, try to extract from string representation
    # This is a fallback for cases where the event structure is unexpected
    if not last_text and events:
        logger.warning(
            "TEXT_EXTRACTION_FALLBACK: Direct extraction failed, trying regex fallback. "
            "Last event type=%s, Last event str length=%d",
            type(events[-1]).__name__,
            len(str(events[-1])),
        )
        import re
        # Look for text='...' pattern in the last event's string representation
        last_ev_str = str(events[-1])
        # Try to find text='...' with proper handling of escaped quotes
        # Match text='...' where ... can contain escaped quotes
        match = re.search(r"text=['\"](.*?)['\"]", last_ev_str, re.DOTALL)
        if match:
            potential_text = match.group(1)
            # Unescape common escape sequences
            potential_text = potential_text.replace("\\'", "'").replace('\\"', '"')
            if potential_text.strip() and "{" in potential_text:
                last_text = potential_text.strip()
                extraction_method = "regex_fallback"
                logger.info(
                    "TEXT_EXTRACTION_FALLBACK_SUCCESS: Found text via regex. Text length=%d, Preview=%s",
                    len(last_text),
                    last_text[:100],
                )

    if not last_text:
        logger.error(
            "TEXT_EXTRACTION_FAILED: No text output found in agent events. "
            "Total events=%d, Last event type=%s, Last event repr=%s",
            len(events),
            type(events[-1]).__name__ if events else "N/A",
            str(events[-1])[:500] if events else "N/A",
        )
        raise HTTPException(
            status_code=500,
            detail=f"No text output found in agent events. Events: {len(events)}. Last event type: {type(events[-1]) if events else 'N/A'}",
        )

    # Trim to the JSON block inside the text. The model often wraps the
    # JSON in markdown fences like ```json ... ``` or includes debug
    # prefixes. We keep only the substring from the first '{' to the
    # last '}'.
    logger.debug(
        "JSON_EXTRACTION_START: Extracting JSON from text. Text length=%d, Has {=%s, Has }=%s",
        len(last_text),
        "{" in last_text,
        "}" in last_text,
    )
    start = last_text.find("{")
    end = last_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_candidate = last_text[start : end + 1]
        logger.debug(
            "JSON_EXTRACTION_SUCCESS: Extracted JSON block. Start=%d, End=%d, Length=%d",
            start,
            end,
            len(json_candidate),
        )
    else:
        json_candidate = last_text
        logger.warning(
            "JSON_EXTRACTION_FALLBACK: Could not find JSON boundaries, using full text. "
            "Start=%s, End=%s",
            start,
            end,
        )

    # Fix common JSON issues before parsing
    # JSON doesn't allow \' as an escape sequence - only \" is valid for quotes
    # But single quotes as regular characters are fine. The issue is \\' which is invalid.
    # Replace \\' with just ' (unescape the backslash, keep the quote)
    original_json_candidate = json_candidate
    json_candidate = json_candidate.replace("\\'", "'")
    if original_json_candidate != json_candidate:
        logger.debug(
            "JSON_FIX_APPLIED: Replaced \\' with '. Original length=%d, Fixed length=%d",
            len(original_json_candidate),
            len(json_candidate),
        )
    
    try:
        logger.debug("JSON_PARSE_ATTEMPT: Attempting to parse JSON. JSON length=%d", len(json_candidate))
        plan = json.loads(json_candidate)
        logger.info(
            "JSON_PARSE_SUCCESS: Successfully parsed JSON. "
            "Plan keys=%s, Has festival_overview=%s",
            list(plan.keys()) if isinstance(plan, dict) else "N/A",
            "festival_overview" in plan if isinstance(plan, dict) else False,
        )
    except json.JSONDecodeError as exc:
        logger.warning(
            "JSON_PARSE_ERROR: First parse attempt failed. Error=%s, Error position=%s, "
            "JSON preview=%s",
            exc.msg,
            exc.pos,
            json_candidate[max(0, exc.pos - 50) : exc.pos + 50],
        )
        # If parsing still fails, try a few more fixes
        # Remove any markdown code fences that might remain
        json_candidate = json_candidate.replace("```json", "").replace("```", "").strip()
        logger.debug("JSON_FIX_MARKDOWN: Removed markdown fences. New length=%d", len(json_candidate))
        # Try parsing again
        try:
            plan = json.loads(json_candidate)
            logger.info(
                "JSON_PARSE_RETRY_SUCCESS: Successfully parsed JSON after markdown fix. "
                "Plan keys=%s",
                list(plan.keys()) if isinstance(plan, dict) else "N/A",
            )
        except json.JSONDecodeError as retry_exc:
            logger.error(
                "JSON_PARSE_FINAL_FAILURE: All parse attempts failed. "
                "Original error=%s (pos=%d), Retry error=%s (pos=%d), "
                "Raw text length=%d, Raw text preview=%s",
                exc.msg,
                exc.pos,
                retry_exc.msg,
                retry_exc.pos,
                len(last_text),
                last_text[:1000],
            )
            raise HTTPException(
                status_code=500,
                detail=f"Agent output was not valid JSON: {retry_exc}; raw={last_text[:1000]}",
            ) from retry_exc
    except Exception as exc:
        logger.error(
            "JSON_PARSE_UNEXPECTED_ERROR: Unexpected error during JSON parsing. "
            "Error type=%s, Error message=%s, Traceback=%s, Raw text preview=%s",
            type(exc).__name__,
            str(exc),
            traceback.format_exc(),
            last_text[:1000],
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error parsing JSON: {exc}; raw={last_text[:1000]}",
        ) from exc

    logger.info(
        "PLAN_REQUEST_SUCCESS: Festival plan generated successfully. "
        "Plan has %d top-level keys",
        len(plan) if isinstance(plan, dict) else 0,
    )
    return plan

