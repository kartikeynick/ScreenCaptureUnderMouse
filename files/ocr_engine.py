"""
ocr_engine.py — OCR text extraction from captured images.

Real mode: uses EasyOCR.
Mock mode: returns predictable text for testing.
"""

import logging
from PIL import Image

from config import MOCK_MODE, OCR_LANGUAGES, MIN_CHAR_THRESHOLD

logger = logging.getLogger(__name__)

# Lazy-loaded EasyOCR reader (heavy initialization, do it once)
_reader = None


def _get_reader():
    """Lazy-initialize the EasyOCR reader (only in real mode)."""
    global _reader
    if _reader is None:
        import easyocr
        logger.info(f"Initializing EasyOCR with languages: {OCR_LANGUAGES}")
        _reader = easyocr.Reader(OCR_LANGUAGES, gpu=True)
        logger.info("EasyOCR reader ready.")
    return _reader


def extract_text(image: Image.Image) -> dict:
    """
    Runs OCR on the given PIL Image and returns extracted text + metadata.

    Returns:
        {
            "raw_text": str,          # full concatenated OCR output
            "char_count": int,        # number of characters extracted
            "word_count": int,        # number of words extracted
            "confidence_avg": float,  # average OCR confidence (0-1)
            "is_valid": bool,         # True if char_count >= MIN_CHAR_THRESHOLD
            "segments": list,         # individual OCR segments with bbox + confidence
        }
    """
    if MOCK_MODE:
        return _mock_extract(image)

    return _real_extract(image)


def _mock_extract(image: Image.Image) -> dict:
    """
    Returns mock OCR output. Uses a fixed string that simulates
    what you'd get from hovering over a data catalog page.
    """
    mock_text = (
        "customer_order_id: Primary key for "
        "the orders table in the retail "
        "data warehouse. Links to dim_customer."
    )

    result = {
        "raw_text": mock_text,
        "char_count": len(mock_text),
        "word_count": len(mock_text.split()),
        "confidence_avg": 0.95,
        "is_valid": len(mock_text) >= MIN_CHAR_THRESHOLD,
        "segments": [
            {
                "text": mock_text,
                "confidence": 0.95,
                "bbox": [[0, 0], [400, 0], [400, 200], [0, 200]],
            }
        ],
    }

    logger.info(
        f"[MOCK] OCR result: {result['char_count']} chars, "
        f"{result['word_count']} words, valid={result['is_valid']}"
    )
    return result


def _real_extract(image: Image.Image) -> dict:
    """
    Runs EasyOCR on the image. Returns structured result.
    """
    import numpy as np

    reader = _get_reader()

    # EasyOCR expects numpy array
    img_array = np.array(image)
    results = reader.readtext(img_array)

    # results format: list of (bbox, text, confidence)
    segments = []
    text_parts = []
    confidences = []

    for bbox, text, confidence in results:
        segments.append({
            "text": text,
            "confidence": confidence,
            "bbox": bbox,
        })
        text_parts.append(text)
        confidences.append(confidence)

    raw_text = " ".join(text_parts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    result = {
        "raw_text": raw_text,
        "char_count": len(raw_text),
        "word_count": len(raw_text.split()),
        "confidence_avg": round(avg_conf, 3),
        "is_valid": len(raw_text) >= MIN_CHAR_THRESHOLD,
        "segments": segments,
    }

    logger.info(
        f"OCR result: {result['char_count']} chars, "
        f"{result['word_count']} words, "
        f"avg_confidence={result['confidence_avg']}, "
        f"valid={result['is_valid']}"
    )
    return result
