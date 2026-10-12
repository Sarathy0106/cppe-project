"""CampusVoice structured logging helper.
Formats logs as structured JSON.
CRITICAL SECURITY RULE: Never log raw feedback text or PII.
"""

import json
import logging
import os
import sys

logger = logging.getLogger("campusvoice")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

# Ensure stdout handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)


def log_event(event_type: str, details: dict, level: str = "INFO"):
    """Emit a structured JSON log entry.
    
    Args:
        event_type: Category of the event (e.g., 'pii_masking_complete')
        details: Dictionary of non-sensitive metrics, counts, and status
        level: Logging level ('INFO', 'WARNING', 'ERROR')
    """
    payload = {
        "event_type": event_type,
        "details": details
    }
    msg = json.dumps(payload, default=str)
    
    if level == "ERROR":
        logger.error(msg)
    elif level == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
