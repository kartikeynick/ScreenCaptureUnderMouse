# Catalog Capture Pipeline

Screen capture → OCR → Catalog Agent input pipeline.

Hover over a word on screen, press `Ctrl+'`, and the pipeline:
1. Records mouse position
2. Captures a screenshot region around cursor (~400×200px)
3. Flashes a visual indicator of the captured area
4. Runs OCR (EasyOCR) to extract ~50+ characters of context
5. Passes the extracted text to the Catalog Agent hook (stub)

## Quick Start

### Mock Mode (no display, no EasyOCR — for testing)
```bash
pip install Pillow
cd catalog_capture_pipeline
python pipeline.py --mock
```

### Run Tests
```bash
cd catalog_capture_pipeline
python tests/test_pipeline.py
```

### Live Mode (on your workbench with display + EasyOCR)
```bash
pip install -r requirements.txt
# Edit config.py: set MOCK_MODE = False
python pipeline.py --live
```

## Project Structure
```
catalog_capture_pipeline/
├── config.py          # All tunable parameters (box size, hotkey, thresholds)
├── capture.py         # Screen capture + mouse position (mss / pynput)
├── ocr_engine.py      # EasyOCR wrapper with mock fallback
├── overlay.py         # Visual flash feedback (tkinter)
├── hook.py            # Catalog Agent stub — wire your FastAPI endpoint here
├── pipeline.py        # Main orchestrator + hotkey listener
├── requirements.txt   # Dependencies
├── assets/            # Test images (optional)
│   └── test_screen.png
└── tests/
    └── test_pipeline.py  # Full test suite (runs in mock mode)
```

## Wiring the Catalog Agent

When your Gemma 9B model is served via FastAPI, edit `hook.py`:

```python
def catalog_agent_hook(extracted_text, mouse_x, mouse_y, ocr_metadata=None):
    import httpx
    response = httpx.post(
        "http://localhost:8000/query",
        json={"context_text": extracted_text},
    )
    return response.json()
```

## Tuning the Capture Box

If OCR returns fewer than 50 characters, increase `BOX_WIDTH` / `BOX_HEIGHT` in `config.py`.
The log file (`capture_pipeline.log`) shows char counts for each capture to help you tune.
