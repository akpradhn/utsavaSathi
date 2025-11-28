"""
Shared utilities for specialized agents.
"""

import logging
import os

from dotenv import load_dotenv
from google.genai import types

logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not API_KEY:
    logger.error(
        "API_KEY_MISSING: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment or .env file."
    )
    raise RuntimeError(
        "GOOGLE_API_KEY or GEMINI_API_KEY must be set in your environment or .env file."
    )

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

