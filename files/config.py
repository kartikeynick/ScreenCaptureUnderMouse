"""
Configuration for the Screen Capture → OCR → Agent Pipeline.

Tune these values based on your display, font size, and resolution.
On your data science workbench, set MOCK_MODE = False.
"""

# ── Mode ─────────────────────────────────────────────────────────────
# When True: uses fake screen capture + fake OCR (no display/easyocr needed)
# When False: uses real screen capture + real EasyOCR
MOCK_MODE = True

# ── Hotkey ───────────────────────────────────────────────────────────
# Modifier + key combination that triggers capture
# Uses pynput key names
HOTKEY_MODIFIER = "ctrl"
HOTKEY_KEY = "'"  # apostrophe

# ── Capture Box ──────────────────────────────────────────────────────
# Size of the screenshot region around the mouse cursor (in pixels)
# Aim: capture enough text to get ~50+ characters of context
# Tune these based on your screen resolution and typical font size
#   - Small fonts / high DPI: increase these
#   - Large fonts / low DPI: decrease these
BOX_WIDTH = 400   # pixels, horizontal span around cursor
BOX_HEIGHT = 200  # pixels, vertical span around cursor

# ── OCR ──────────────────────────────────────────────────────────────
# EasyOCR language list (add more if your catalog has multilingual content)
OCR_LANGUAGES = ["en"]

# Minimum characters we want from OCR to consider it a valid capture
MIN_CHAR_THRESHOLD = 10

# ── Visual Feedback ──────────────────────────────────────────────────
# Show a brief overlay rectangle where the capture happened
SHOW_FLASH_OVERLAY = True
FLASH_DURATION_MS = 300  # how long the overlay stays visible

# ── Logging ──────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"  # DEBUG for verbose output during testing
LOG_FILE = "capture_pipeline.log"
