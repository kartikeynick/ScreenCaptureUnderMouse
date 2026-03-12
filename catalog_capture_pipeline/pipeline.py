"""
pipeline.py — Main orchestrator.

Ties together: hotkey listener → screen capture → OCR → agent hook.

Usage:
    python pipeline.py          # runs with whatever MOCK_MODE is set in config
    python pipeline.py --mock   # force mock mode
    python pipeline.py --live   # force live mode
"""

import logging
import sys
import time

from config import (
    MOCK_MODE,
    HOTKEY_MODIFIER,
    HOTKEY_KEY,
    LOG_LEVEL,
    LOG_FILE,
    MIN_CHAR_THRESHOLD,
)
from capture import get_mouse_position, capture_region
from ocr_engine import extract_text
from hook import catalog_agent_hook
from overlay import show_capture_flash

# ── Logging setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-12s | %(levelname)-5s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a"),
    ],
)
logger = logging.getLogger("pipeline")


def on_hotkey_triggered():
    """
    Called when the hotkey (Ctrl+') is pressed.
    This is the main pipeline sequence:
        1. Get mouse position
        2. Capture screen region around cursor
        3. Show visual flash feedback
        4. Run OCR on captured image
        5. Validate OCR output
        6. Pass to agent hook
    """
    logger.info("=" * 60)
    logger.info("HOTKEY TRIGGERED — starting capture pipeline")
    t_start = time.time()

    # Step 1: Mouse position
    mouse_x, mouse_y = get_mouse_position()
    logger.info(f"Step 1/5 — Mouse position: ({mouse_x}, {mouse_y})")

    # Step 2: Capture screenshot region
    image = capture_region(mouse_x, mouse_y)
    logger.info(f"Step 2/5 — Captured image: {image.size}")

    # Step 3: Visual flash (non-blocking)
    show_capture_flash(mouse_x, mouse_y)
    logger.info(f"Step 3/5 — Flash overlay triggered")

    # Step 4: OCR
    ocr_result = extract_text(image)
    logger.info(
        f"Step 4/5 — OCR complete: {ocr_result['char_count']} chars, "
        f"{ocr_result['word_count']} words, "
        f"confidence={ocr_result['confidence_avg']}"
    )

    # Step 5: Validate
    if not ocr_result["is_valid"]:
        logger.warning(
            f"OCR below threshold ({ocr_result['char_count']} < {MIN_CHAR_THRESHOLD} chars). "
            f"Consider increasing box size in config.py."
        )
        # Still pass it through — let the hook decide what to do with low-quality input

    # Step 6: Agent hook
    result = catalog_agent_hook(
        extracted_text=ocr_result["raw_text"],
        mouse_x=mouse_x,
        mouse_y=mouse_y,
        ocr_metadata=ocr_result,
    )

    elapsed = round(time.time() - t_start, 3)
    logger.info(f"Step 5/5 — Pipeline complete in {elapsed}s")
    logger.info(f"Hook result: {result}")
    logger.info("=" * 60)

    return result


def start_listener():
    """
    Starts the global hotkey listener.
    In mock mode, simulates a single hotkey press for testing.
    """
    if MOCK_MODE:
        logger.info("[MOCK] Simulating hotkey press...")
        result = on_hotkey_triggered()
        print("\n--- Pipeline Output ---")
        for k, v in result.items():
            print(f"  {k}: {v}")
        return

    # Real mode: global hotkey listener using pynput
    from pynput import keyboard

    logger.info(f"Listening for hotkey: {HOTKEY_MODIFIER}+{HOTKEY_KEY}")
    logger.info("Press Ctrl+' to capture. Press Ctrl+C to quit.")

    # Track modifier state
    ctrl_pressed = False

    def on_press(key):
        nonlocal ctrl_pressed
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                ctrl_pressed = True
            elif ctrl_pressed and hasattr(key, "char") and key.char == HOTKEY_KEY:
                on_hotkey_triggered()
        except AttributeError:
            pass

    def on_release(key):
        nonlocal ctrl_pressed
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def main():
    """Entry point with CLI flag support."""
    # Allow overriding mock mode from CLI
    import config

    if "--mock" in sys.argv:
        config.MOCK_MODE = True
        # Also update imported modules that cache the value
        import capture
        import ocr_engine
        import overlay
        capture.MOCK_MODE = True
        ocr_engine.MOCK_MODE = True
        overlay.MOCK_MODE = True
        logger.info("Forced MOCK_MODE=True via CLI flag")
    elif "--live" in sys.argv:
        config.MOCK_MODE = False
        import capture
        import ocr_engine
        import overlay
        capture.MOCK_MODE = False
        ocr_engine.MOCK_MODE = False
        overlay.MOCK_MODE = False
        logger.info("Forced MOCK_MODE=False via CLI flag — requires display + EasyOCR")

    mode = "MOCK" if config.MOCK_MODE else "LIVE"
    logger.info(f"Starting Catalog Capture Pipeline [{mode} MODE]")
    start_listener()


if __name__ == "__main__":
    main()
