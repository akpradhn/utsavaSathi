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
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from utsava_agent.session_runner import SessionRunner
from utsava_agent.session_manager import SessionManager
from utsava_agent.memory_manager import MemoryManager

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

# Try to import coordinator agent (multi-agent system)
try:
    from utsava_agent.coordinator import coordinator_agent  # type: ignore
    MULTI_AGENT_AVAILABLE = True
    logger.info("COORDINATOR_AGENT_IMPORTED: Successfully imported coordinator_agent")
except Exception as exc:
    MULTI_AGENT_AVAILABLE = False
    logger.warning(
        "COORDINATOR_AGENT_IMPORT_FAILED: Multi-agent system not available. "
        "Error=%s. Falling back to single agent mode.",
        exc,
    )

load_dotenv()
logger.info("ENV_LOADED: Environment variables loaded from .env file")

# Initialize session and memory managers
session_manager = SessionManager(db_path="agent_sessions.db")
memory_manager = MemoryManager(db_path="agent_memory.db")
logger.info("SESSION_MEMORY_MANAGERS_INITIALIZED: Session and memory managers ready")

app = FastAPI(
    title="Utsava Sathi FestivalPlan API",
    description="Generates FestivalPlan JSON for Odisha-first festivals via Gemini.",
)


class PlanRequest(BaseModel):
    """Incoming festival planning request."""

    prompt: str  # free-form text describing festival + family context
    use_multi_agent: bool = False  # Use multi-agent coordinator if available
    session_id: Optional[str] = None  # Optional session ID for conversation continuity
    user_id: Optional[str] = None  # Optional user ID for cross-session memory


@app.post("/plan")
async def plan_festival(req: PlanRequest) -> Dict[str, Any]:
    """
    Call the ADK root_agent with the given prompt and return a parsed
    FestivalPlan JSON object.
    """
    logger.info(
        "PLAN_REQUEST_RECEIVED: Processing festival planning request. "
        "Prompt length=%d, Prompt preview=%s, Use multi-agent=%s",
        len(req.prompt),
        req.prompt[:100] if len(req.prompt) > 100 else req.prompt,
        req.use_multi_agent and MULTI_AGENT_AVAILABLE,
    )

    # Select agent based on request and availability
    if req.use_multi_agent and MULTI_AGENT_AVAILABLE:
        agent = coordinator_agent
        agent_type = "multi-agent coordinator"
    else:
        agent = root_agent
        agent_type = "single agent"
        if req.use_multi_agent:
            logger.warning(
                "MULTI_AGENT_REQUESTED_BUT_UNAVAILABLE: Multi-agent requested but not available. "
                "Using single agent mode."
            )

    logger.info(f"AGENT_SELECTED: Using {agent_type} for this request")

    # Use SessionRunner if session_id is provided, otherwise use InMemoryRunner
    use_session = req.session_id is not None or req.user_id is not None
    session_id = None
    turn_number = None
    
    if use_session:
        logger.info(
            f"SESSION_MODE_ENABLED: session_id={req.session_id}, user_id={req.user_id}"
        )
        runner = SessionRunner(
            agent=agent,
            session_manager=session_manager,
            memory_manager=memory_manager,
            app_name="utsava_agent",
            session_id=req.session_id,
            user_id=req.user_id
        )
        session_id = runner.get_session_id()
        
        try:
            # Run with session and memory context
            result = await runner.run(req.prompt)
            events = result.get("events", [])
            last_text = result.get("response", "")
            session_id = result.get("session_id", session_id)
            turn_number = result.get("turn_number", 0)
            
            logger.info(
                f"AGENT_EXECUTION_SUCCESS: Session execution completed. "
                f"session_id={session_id}, turn={turn_number}, "
                f"memories_used={result.get('memories_used', {})}"
            )
        except Exception as exc:
            logger.error(
                "AGENT_EXECUTION_FAILED: Session runner execution failed. "
                "Error type=%s, Error message=%s, Traceback=%s",
                type(exc).__name__,
                str(exc),
                traceback.format_exc(),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Agent execution failed: {exc}",
            ) from exc
    else:
        # Use standard InMemoryRunner for non-session requests
        runner = InMemoryRunner(agent=agent, app_name="utsava_agent")
        logger.debug(
            f"RUNNER_CREATED: InMemoryRunner initialized with {agent_type}, app_name=utsava_agent"
        )
        
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

    # Extract the last meaningful text chunk from the events (only for non-session mode)
    # ADK events have a `content` attribute with `parts` containing the actual text.
    if not use_session:
        logger.debug("TEXT_EXTRACTION_START: Attempting to extract text from %d events", len(events))
        last_text = ""
        extraction_method = None
        all_text_candidates = []  # Collect all text candidates to find JSON
        
        for idx, ev in enumerate(reversed(events)):
            ev_type = type(ev).__name__
            ev_attrs = [attr for attr in dir(ev) if not attr.startswith("_")]
            logger.debug(
                "TEXT_EXTRACTION_ATTEMPT: Processing event %d/%d, Type=%s, Attributes=%s",
                idx + 1,
                len(events),
                ev_type,
                ev_attrs[:10],  # Limit to first 10 attributes
            )
            
            # Log content structure if available
            content = getattr(ev, "content", None)
            if content:
                logger.debug(
                    "TEXT_EXTRACTION_CONTENT: Found content object. Type=%s, Repr=%s",
                    type(content).__name__,
                    str(content)[:300],
                )
            
            # Try direct text attributes first
            text = getattr(ev, "output_text", None) or getattr(ev, "output", None)
            if isinstance(text, str) and text.strip():
                all_text_candidates.append(("output_text/output", text.strip()))
                # If it looks like JSON, prefer it
                if "{" in text and "}" in text:
                    last_text = text.strip()
                    extraction_method = "output_text/output (JSON)"
                    logger.info(
                        "TEXT_EXTRACTION_SUCCESS: Found JSON-like text via %s. Text length=%d, Preview=%s",
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
                        # Handle both iterable and single part
                        if hasattr(parts, "__iter__") and not isinstance(parts, str):
                            parts_list = list(parts)
                        else:
                            parts_list = [parts]
                        
                        logger.debug(
                            "TEXT_EXTRACTION_PARTS: Found %d parts in content.parts",
                            len(parts_list),
                        )
                        
                        # Iterate through all parts to find text
                        # Prefer text that looks like JSON (contains { and })
                        json_candidates = []
                        text_candidates = []
                        
                        for part in parts_list:
                            part_text = getattr(part, "text", None)
                            if isinstance(part_text, str) and part_text.strip():
                                if "{" in part_text and "}" in part_text:
                                    json_candidates.append(part_text.strip())
                                else:
                                    text_candidates.append(part_text.strip())
                        
                        # Prefer JSON-like text over plain text
                        if json_candidates:
                            last_text = json_candidates[0]  # Take first JSON candidate
                            extraction_method = "content.parts[].text (JSON)"
                            logger.info(
                                "TEXT_EXTRACTION_SUCCESS: Found JSON-like text via %s. Text length=%d, Preview=%s",
                                extraction_method,
                                len(last_text),
                                last_text[:100],
                            )
                            break
                        elif text_candidates:
                            # Store for later if no JSON found
                            for txt in text_candidates:
                                all_text_candidates.append(("content.parts[].text", txt))
                            if not last_text:
                                last_text = text_candidates[0]
                                extraction_method = "content.parts[].text"
                        
                        if last_text and "{" in last_text and "}" in last_text:
                            break
                except (AttributeError, TypeError, IndexError) as parts_exc:
                    logger.debug(
                        "TEXT_EXTRACTION_PARTS_ERROR: Failed to extract from parts. Error=%s, Content repr=%s",
                        parts_exc,
                        str(content)[:200],
                    )
                
                # Also try if content itself has text attribute
                if not last_text:
                    try:
                        content_text = getattr(content, "text", None)
                        if isinstance(content_text, str) and content_text.strip():
                            all_text_candidates.append(("content.text", content_text.strip()))
                            if "{" in content_text and "}" in content_text:
                                last_text = content_text.strip()
                                extraction_method = "content.text (JSON)"
                                logger.info(
                                    "TEXT_EXTRACTION_SUCCESS: Found JSON-like text via %s. Text length=%d, Preview=%s",
                                    extraction_method,
                                    len(last_text),
                                    last_text[:100],
                                )
                                break
                            elif not last_text:
                                last_text = content_text.strip()
                                extraction_method = "content.text"
                    except (AttributeError, TypeError) as content_exc:
                        logger.debug(
                            "TEXT_EXTRACTION_CONTENT_ERROR: Failed to extract from content.text. Error=%s",
                            content_exc,
                        )
                
                # Try accessing content via different methods
                if not last_text:
                    try:
                        # Try calling content as a method if it's callable
                        if callable(content):
                            try:
                                result = content()
                                if isinstance(result, str) and result.strip():
                                    last_text = result.strip()
                                    extraction_method = "content()"
                                    logger.info(
                                        "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d",
                                        extraction_method,
                                        len(last_text),
                                    )
                                    break
                            except Exception:
                                pass
                        
                        # Try accessing via __dict__ or vars()
                        content_dict = None
                        if hasattr(content, "__dict__"):
                            content_dict = content.__dict__
                        else:
                            try:
                                content_dict = vars(content)
                            except (TypeError, AttributeError):
                                pass
                        
                        if content_dict:
                            for key in ["text", "parts", "content", "data"]:
                                if key in content_dict:
                                    value = content_dict[key]
                                    if isinstance(value, str) and value.strip():
                                        last_text = value.strip()
                                        extraction_method = f"content.{key}"
                                        logger.info(
                                            "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d",
                                            extraction_method,
                                            len(last_text),
                                        )
                                        break
                                    elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
                                        # Try to extract from iterable
                                        try:
                                            for item in value:
                                                if hasattr(item, "text"):
                                                    item_text = getattr(item, "text", None)
                                                    if isinstance(item_text, str) and item_text.strip():
                                                        last_text = item_text.strip()
                                                        extraction_method = f"content.{key}[].text"
                                                        logger.info(
                                                            "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d",
                                                            extraction_method,
                                                            len(last_text),
                                                        )
                                                        break
                                                elif isinstance(item, str) and item.strip():
                                                    last_text = item.strip()
                                                    extraction_method = f"content.{key}[]"
                                                    logger.info(
                                                        "TEXT_EXTRACTION_SUCCESS: Found text via %s. Text length=%d",
                                                        extraction_method,
                                                        len(last_text),
                                                    )
                                                    break
                                                if last_text:
                                                    break
                                        except (TypeError, AttributeError):
                                            pass
                                    if last_text:
                                        break
                            if last_text:
                                break
                    except Exception as dict_exc:
                        logger.debug(
                            "TEXT_EXTRACTION_DICT_ERROR: Failed to extract from content attributes. Error=%s",
                            dict_exc,
                        )
            
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

        # If we still don't have text, try looking at events in forward order
        # (sometimes the response is in an earlier event)
        if not last_text:
            logger.debug("TEXT_EXTRACTION_FORWARD: Trying forward order extraction")
            for idx, ev in enumerate(events):
                content = getattr(ev, "content", None)
                if content:
                    try:
                        parts = getattr(content, "parts", None)
                        if parts:
                            if hasattr(parts, "__iter__") and not isinstance(parts, str):
                                parts_list = list(parts)
                            else:
                                parts_list = [parts]
                            
                            for part in parts_list:
                                part_text = getattr(part, "text", None)
                                if isinstance(part_text, str) and part_text.strip():
                                    candidate = part_text.strip()
                                    all_text_candidates.append((f"forward_order.event_{idx}", candidate))
                                    # Prefer JSON-like text
                                    if "{" in candidate and "}" in candidate:
                                        last_text = candidate
                                        extraction_method = f"forward_order.content.parts[].text (JSON) event_{idx}"
                                        logger.info(
                                            "TEXT_EXTRACTION_SUCCESS: Found JSON via %s. Text length=%d",
                                            extraction_method,
                                            len(last_text),
                                        )
                                        break
                                    elif not last_text:
                                        last_text = candidate
                                        extraction_method = f"forward_order.content.parts[].text event_{idx}"
                            if last_text and "{" in last_text and "}" in last_text:
                                break
                    except (AttributeError, TypeError, IndexError):
                        pass
        
        # If we still don't have text, try to extract from string representation
        # This is a fallback for cases where the event structure is unexpected
        if not last_text and events:
            logger.warning(
                "TEXT_EXTRACTION_FALLBACK: Direct extraction failed, trying regex fallback. "
                "Total events=%d, Last event type=%s, Last event str length=%d",
                len(events),
                type(events[-1]).__name__,
                len(str(events[-1])),
            )
            import re
            # Look through all events for text patterns
            for idx, ev in enumerate(reversed(events)):
                ev_str = str(ev)
                # Try to find text='...' or text="..." pattern
                matches = re.finditer(r"text\s*=\s*['\"](.*?)['\"]", ev_str, re.DOTALL)
                for match in matches:
                    potential_text = match.group(1)
                    # Unescape common escape sequences
                    potential_text = potential_text.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n")
                    if potential_text.strip() and len(potential_text.strip()) > 10:  # Minimum length check
                        last_text = potential_text.strip()
                        extraction_method = f"regex_fallback_event_{len(events)-idx}"
                        logger.info(
                            "TEXT_EXTRACTION_FALLBACK_SUCCESS: Found text via %s. Text length=%d, Preview=%s",
                            extraction_method,
                            len(last_text),
                            last_text[:100],
                        )
                        break
                if last_text:
                    break

        # If we didn't find JSON, look through all collected candidates
        if not last_text or ("{" not in last_text or "}" not in last_text):
            logger.debug(
                "TEXT_EXTRACTION_SEARCHING: No JSON found yet. Searching %d candidates for JSON",
                len(all_text_candidates),
            )
            # Look for JSON in all candidates
            for method, candidate_text in all_text_candidates:
                if "{" in candidate_text and "}" in candidate_text:
                    last_text = candidate_text
                    extraction_method = f"{method} (JSON from candidates)"
                    logger.info(
                        "TEXT_EXTRACTION_SUCCESS: Found JSON in candidates via %s. Text length=%d",
                        extraction_method,
                        len(last_text),
                    )
                    break
        
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
    else:
        # For session mode, text is already extracted by SessionRunner
        logger.debug("TEXT_EXTRACTION_SKIPPED: Using text from SessionRunner")
        extraction_method = "session_runner"
        all_text_candidates = []  # Initialize for session mode

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
    
    # First, try to extract from markdown code blocks
    import re
    json_candidate = None
    
    # Look for ```json ... ``` or ``` ... ``` blocks
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)```"
    code_matches = re.finditer(code_block_pattern, last_text, re.DOTALL)
    for match in code_matches:
        potential_json = match.group(1).strip()
        if "{" in potential_json and "}" in potential_json:
            json_candidate = potential_json
            logger.debug(
                "JSON_EXTRACTION_SUCCESS: Found JSON in markdown code block. Length=%d",
                len(json_candidate),
            )
            break
    
    # If no code block found, look for JSON boundaries
    if not json_candidate:
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
            # If no JSON found, check all text candidates for JSON
            logger.warning(
                "JSON_EXTRACTION_FALLBACK: Could not find JSON boundaries in main text. "
                "Searching all candidates. Start=%s, End=%s",
                start,
                end,
            )
            # Search through all collected candidates
            for method, candidate_text in all_text_candidates:
                if "{" in candidate_text and "}" in candidate_text:
                    start = candidate_text.find("{")
                    end = candidate_text.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        json_candidate = candidate_text[start : end + 1]
                        logger.info(
                            "JSON_EXTRACTION_SUCCESS: Found JSON in candidate from %s. Length=%d",
                            method,
                            len(json_candidate),
                        )
                        break
            
            if not json_candidate:
                json_candidate = last_text
                logger.warning(
                    "JSON_EXTRACTION_FINAL_FALLBACK: Using full text as JSON candidate. Length=%d",
                    len(json_candidate),
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
        "Plan has %d top-level keys, session_id=%s",
        len(plan) if isinstance(plan, dict) else 0,
        session_id if use_session else "N/A",
    )
    
    # Add session metadata to response if using sessions
    if use_session:
        if isinstance(plan, dict):
            plan["_session_metadata"] = {
                "session_id": session_id,
                "turn_number": turn_number if use_session else None,
            }
    
    return plan

