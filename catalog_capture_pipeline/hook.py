"""
hook.py — Catalog Agent hook stub.

This is the integration point where OCR output feeds into your
Catalog Agent (Gemma 9B abliterated + LoRA via FastAPI).

Replace the stub implementation with your actual agent call when ready.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def catalog_agent_hook(
    extracted_text: str,
    mouse_x: int,
    mouse_y: int,
    ocr_metadata: dict | None = None,
) -> dict:
    """
    Hook function called after successful OCR capture.

    This is where you wire your Catalog Agent. The function receives:
        - extracted_text: the OCR'd text from the screen region
        - mouse_x, mouse_y: cursor position at time of capture
        - ocr_metadata: full OCR result dict (char_count, confidence, segments, etc.)

    Returns:
        A dict with the agent response (stubbed for now).

    ── When you're ready to wire the agent ──
    Replace the body of this function with something like:

        import httpx
        response = httpx.post(
            "http://localhost:8000/query",  # your FastAPI endpoint
            json={
                "context_text": extracted_text,
                "cursor_position": {"x": mouse_x, "y": mouse_y},
            },
        )
        return response.json()
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Stub: log and return the payload that would go to the agent ──
    payload = {
        "timestamp": timestamp,
        "cursor": {"x": mouse_x, "y": mouse_y},
        "captured_text": extracted_text,
        "char_count": ocr_metadata.get("char_count", 0) if ocr_metadata else len(extracted_text),
        "confidence": ocr_metadata.get("confidence_avg", None) if ocr_metadata else None,
        "agent_response": None,  # will be populated when agent is wired
        "status": "stub_ok",
    }

    logger.info(
        f"[HOOK] Agent payload ready | "
        f"chars={payload['char_count']} | "
        f"cursor=({mouse_x}, {mouse_y}) | "
        f"text_preview='{extracted_text[:60]}...'"
    )

    return payload
