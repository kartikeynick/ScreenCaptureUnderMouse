# ScreenCaptureUnderMouse

A hotkey-driven screen capture pipeline that captures the word under your mouse cursor and extracts surrounding text as context — designed as an input pipeline for a Catalog Agent LLM.

**Hover over any word → press `Ctrl+'` → word + context text extracted instantly.**

---

## How It Works

```
Mouse position
      │
      ▼
Screenshot (800×400px region around cursor)
      │
      ▼
EasyOCR on full region  ──────────────────▶  CONTEXT TEXT
      │
      ▼
Center-crop (250×70px) + OCR  ────────────▶  TARGET WORD
      │
      ▼
Catalog Agent hook (stub → wire your FastAPI endpoint)
      │
      ▼
assets/captures.txt  (appended each capture)
```

---

## Requirements

- Python 3.10+ (3.11 recommended)
- Works on **macOS** and **Windows**
- GPU optional — EasyOCR runs on CPU, GPU speeds it up

---

## Installation

### macOS

```bash
# 1. Clone the repo
git clone https://github.com/kartikeynick/ScreenCaptureUnderMouse.git
cd ScreenCaptureUnderMouse

# 2. Create a virtual environment (use Homebrew Python on Apple Silicon)
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install Pillow mss pynput easyocr
```

> **Apple Silicon (M1/M2/M3):** Make sure you use Homebrew Python (`/opt/homebrew/bin/python3.11`), not the system Python. The system Python is x86_64 and will fail to load native arm64 packages.

**macOS Permissions required (first run only):**
- `System Settings → Privacy & Security → Accessibility` → enable your Terminal app (needed for global hotkey)
- `System Settings → Privacy & Security → Screen Recording` → enable your Terminal app (needed for mss screenshot)

After granting permissions, quit and reopen Terminal.

---

### Windows

```bash
# 1. Clone the repo
git clone https://github.com/kartikeynick/ScreenCaptureUnderMouse.git
cd ScreenCaptureUnderMouse

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install Pillow mss pynput easyocr
```

No special permissions needed on Windows.

> **Note:** Cursor hiding during screenshot is macOS-only. On Windows the mouse cursor may appear in the captured image, which can occlude the text directly under it.

---

## Running

```bash
cd catalog_capture_pipeline
python live_demo.py
```

You'll see:
```
=======================================================
  Catalog Capture Pipeline — LIVE HOTKEY MODE
=======================================================
  Hover over any word on screen and press Ctrl+'
  A green box will flash and the text will be captured.
  Press Ctrl+C here to stop.
```

**Usage:**
1. Leave the terminal running in the background
2. Go to any app — browser, PDF, Notion, anything
3. Hover your mouse over a word
4. Press **`Ctrl+'`** (Control + apostrophe)
5. Green box flashes on screen, output prints in terminal

**Example output:**
```
───────────────────────────────────────────────────────
  Capture #1  |  1.24s  |  cursor (843, -312)
───────────────────────────────────────────────────────
  TARGET WORD : "Sponsored"  [crop]
  CONTEXT     : "Sponsored · 4.8 ★ Free shipping on orders over $35..."
  Segments    : 12  |  Chars: 187
  Screenshot  → assets/last_capture.png
  Text log    → assets/captures.txt
───────────────────────────────────────────────────────
```

Each capture is appended to `assets/captures.txt`:
```
--- Capture #1 | 2026-03-12 10:45:01 | cursor (843, -312) ---
TARGET WORD : Sponsored  [crop]
CONTEXT     : Sponsored · 4.8 ★ Free shipping on orders over $35...
```

---

## Configuration

Edit `catalog_capture_pipeline/config.py` to tune:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BOX_WIDTH` | `800` | Width of capture region around cursor (px) |
| `BOX_HEIGHT` | `400` | Height of capture region around cursor (px) |
| `HOTKEY_KEY` | `'` | Key to press with Ctrl |
| `FLASH_DURATION_MS` | `300` | How long the green overlay stays visible |
| `MIN_CHAR_THRESHOLD` | `10` | Minimum chars for a valid OCR capture |

---

## Testing (no display or GPU needed)

```bash
cd catalog_capture_pipeline
python tests/test_pipeline.py
```

All 7 tests run in mock mode — no screen, no EasyOCR, no hotkey required.

```
Results: 7 passed, 0 failed, 7 total
```

---

## Wiring the Catalog Agent

Edit `catalog_capture_pipeline/hook.py` to replace the stub with your FastAPI endpoint:

```python
def catalog_agent_hook(extracted_text, mouse_x, mouse_y, ocr_metadata=None):
    import httpx
    response = httpx.post(
        "http://localhost:8000/query",
        json={"context_text": extracted_text},
    )
    return response.json()
```

---

## Project Structure

```
catalog_capture_pipeline/
├── live_demo.py       # Entry point — hotkey listener + full pipeline
├── pipeline.py        # Core orchestrator
├── capture.py         # Screen capture + mouse position (mss / pynput)
├── ocr_engine.py      # EasyOCR wrapper with mock fallback
├── overlay.py         # Green flash overlay (tkinter)
├── hook.py            # Catalog Agent stub — wire your endpoint here
├── config.py          # All tunable parameters
├── requirements.txt   # Dependencies
├── assets/            # Runtime outputs (gitignored)
│   ├── last_capture.png   # Screenshot from last capture
│   └── captures.txt       # Log of all captures this session
└── tests/
    └── test_pipeline.py   # 7 tests, mock mode
```

---

## Known Limitations

| Issue | Platform | Notes |
|-------|----------|-------|
| Cursor appears in screenshot | Windows | macOS hides cursor via Quartz before capture |
| First capture is slow (~5–10s) | Both | EasyOCR loads neural network model on first use; subsequent captures are fast |
| Target word may be a short phrase | Both | If EasyOCR groups words together and the center crop spans multiple words |
| Hotkey requires Accessibility permission | macOS | Grant once in System Settings |
