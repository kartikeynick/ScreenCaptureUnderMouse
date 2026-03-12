"""
overlay.py — Visual feedback: briefly flashes a rectangle on screen
showing the captured region.

Real mode: uses tkinter to draw a transparent overlay.
Mock mode: just logs that the overlay would have been shown.
"""

import logging
import threading

from config import MOCK_MODE, SHOW_FLASH_OVERLAY, FLASH_DURATION_MS, BOX_WIDTH, BOX_HEIGHT

logger = logging.getLogger(__name__)


def show_capture_flash(center_x: int, center_y: int):
    """
    Shows a brief rectangular overlay on screen at the capture location.
    Runs in a separate thread so it doesn't block the pipeline.
    """
    if not SHOW_FLASH_OVERLAY:
        return

    if MOCK_MODE:
        logger.info(
            f"[MOCK] Flash overlay would appear at ({center_x}, {center_y}), "
            f"size={BOX_WIDTH}x{BOX_HEIGHT}, duration={FLASH_DURATION_MS}ms"
        )
        return

    # Run overlay in a thread to avoid blocking
    thread = threading.Thread(
        target=_draw_overlay,
        args=(center_x, center_y),
        daemon=True,
    )
    thread.start()


def _draw_overlay(center_x: int, center_y: int):
    """
    Draws a semi-transparent rectangle using tkinter.
    Auto-closes after FLASH_DURATION_MS.
    """
    try:
        import tkinter as tk

        half_w = BOX_WIDTH // 2
        half_h = BOX_HEIGHT // 2

        left = center_x - half_w
        top = center_y - half_h

        root = tk.Tk()
        root.overrideredirect(True)  # no window decorations
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.3)  # semi-transparent
        root.geometry(f"{BOX_WIDTH}x{BOX_HEIGHT}+{left}+{top}")

        # Green-tinted overlay to indicate capture
        canvas = tk.Canvas(root, bg="#00ff88", highlightthickness=2, highlightbackground="#00aa55")
        canvas.pack(fill="both", expand=True)

        # Auto-close after flash duration
        root.after(FLASH_DURATION_MS, root.destroy)
        root.mainloop()

    except Exception as e:
        logger.warning(f"Could not show overlay (expected if no display): {e}")
