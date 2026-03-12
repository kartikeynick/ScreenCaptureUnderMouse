"""
capture.py — Screen capture and mouse position tracking.

Real mode: uses `mss` for screenshot, `pynput` for mouse position.
Mock mode: loads a test image from assets/ and returns a fake mouse position.
"""

import logging
from pathlib import Path
from PIL import Image

from config import MOCK_MODE, BOX_WIDTH, BOX_HEIGHT

logger = logging.getLogger(__name__)

# Path to test image used in mock mode
MOCK_IMAGE_PATH = Path(__file__).parent / "assets" / "test_screen.png"


def get_mouse_position() -> tuple[int, int]:
    """
    Returns the current (x, y) mouse cursor position on screen.
    In mock mode, returns center of a fake 1920x1080 screen.
    """
    if MOCK_MODE:
        fake_pos = (960, 540)
        logger.debug(f"[MOCK] Mouse position: {fake_pos}")
        return fake_pos

    from pynput.mouse import Controller
    mouse = Controller()
    pos = (int(mouse.position[0]), int(mouse.position[1]))
    logger.debug(f"Mouse position: {pos}")
    return pos


def capture_region(center_x: int, center_y: int) -> Image.Image:
    """
    Captures a screenshot of the region around (center_x, center_y).
    The region is BOX_WIDTH x BOX_HEIGHT pixels, centered on the cursor.

    Returns a PIL Image of the captured region.
    In mock mode, returns the test image (or a generated placeholder).
    """
    if MOCK_MODE:
        return _mock_capture()

    return _real_capture(center_x, center_y)


def _mock_capture() -> Image.Image:
    """
    Returns a test image for pipeline testing without a display.
    Tries to load assets/test_screen.png first.
    If not found, generates a simple image with text using PIL.
    """
    if MOCK_IMAGE_PATH.exists():
        img = Image.open(MOCK_IMAGE_PATH)
        logger.info(f"[MOCK] Loaded test image: {MOCK_IMAGE_PATH} ({img.size})")
        return img

    # Generate a placeholder image with text
    img = _generate_test_image()
    logger.info(f"[MOCK] Generated placeholder test image ({img.size})")
    return img


def _generate_test_image() -> Image.Image:
    """
    Creates a simple image with known text for testing OCR.
    Uses PIL to draw text so we have a predictable OCR target.
    """
    from PIL import ImageDraw, ImageFont

    width, height = BOX_WIDTH, BOX_HEIGHT
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Sample catalog-like text for testing
    test_text = (
        "customer_order_id: Primary key for\n"
        "the orders table in the retail\n"
        "data warehouse. Links to dim_customer."
    )

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except (OSError, IOError):
        font = ImageFont.load_default()

    draw.text((10, 10), test_text, fill=(0, 0, 0), font=font)
    return img


def _real_capture(center_x: int, center_y: int) -> Image.Image:
    """
    Takes a real screenshot of the region around the cursor using mss.
    Clamps the bounding box to screen edges.
    """
    import mss

    half_w = BOX_WIDTH // 2
    half_h = BOX_HEIGHT // 2

    with mss.mss() as sct:
        # Get the monitor dimensions to clamp the box
        monitor = sct.monitors[0]  # full virtual screen
        screen_w = monitor["width"]
        screen_h = monitor["height"]

        # Calculate bounding box, clamped to screen edges
        left = max(0, center_x - half_w)
        top = max(0, center_y - half_h)
        right = min(screen_w, center_x + half_w)
        bottom = min(screen_h, center_y + half_h)

        region = {
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
        }

        logger.info(f"Capturing region: {region}")
        screenshot = sct.grab(region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img
