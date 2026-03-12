"""
tests/test_pipeline.py — Unit and integration tests for the capture pipeline.

All tests run in mock mode, no display or EasyOCR required.

Usage:
    cd catalog_capture_pipeline
    python -m pytest tests/ -v
    # or simply:
    python tests/test_pipeline.py
"""

import sys
import os

# Ensure we can import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force mock mode for all tests
import config
config.MOCK_MODE = True

import capture
import ocr_engine
import overlay
capture.MOCK_MODE = True
ocr_engine.MOCK_MODE = True
overlay.MOCK_MODE = True

from PIL import Image


def test_mouse_position_mock():
    """Mock mouse position should return a valid (x, y) tuple."""
    x, y = capture.get_mouse_position()
    assert isinstance(x, int) and isinstance(y, int), "Position must be ints"
    assert x >= 0 and y >= 0, "Position must be non-negative"
    print(f"  PASS: mouse position = ({x}, {y})")


def test_capture_region_returns_image():
    """Capture should return a PIL Image in mock mode."""
    img = capture.capture_region(960, 540)
    assert isinstance(img, Image.Image), f"Expected PIL Image, got {type(img)}"
    assert img.size[0] > 0 and img.size[1] > 0, "Image must have non-zero size"
    print(f"  PASS: captured image size = {img.size}")


def test_ocr_extract_returns_structured_result():
    """OCR should return a dict with expected keys and valid values."""
    img = capture.capture_region(960, 540)
    result = ocr_engine.extract_text(img)

    required_keys = ["raw_text", "char_count", "word_count", "confidence_avg", "is_valid", "segments"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    assert isinstance(result["raw_text"], str), "raw_text must be str"
    assert result["char_count"] > 0, "char_count must be > 0"
    assert result["word_count"] > 0, "word_count must be > 0"
    assert 0 <= result["confidence_avg"] <= 1, "confidence must be 0-1"
    assert isinstance(result["is_valid"], bool), "is_valid must be bool"
    print(f"  PASS: OCR returned {result['char_count']} chars, {result['word_count']} words")


def test_ocr_meets_char_threshold():
    """Mock OCR should return at least MIN_CHAR_THRESHOLD characters."""
    img = capture.capture_region(960, 540)
    result = ocr_engine.extract_text(img)
    assert result["char_count"] >= config.MIN_CHAR_THRESHOLD, (
        f"OCR returned only {result['char_count']} chars, "
        f"need >= {config.MIN_CHAR_THRESHOLD}"
    )
    assert result["is_valid"] is True
    print(f"  PASS: {result['char_count']} chars >= threshold {config.MIN_CHAR_THRESHOLD}")


def test_hook_returns_payload():
    """Agent hook should return a structured payload dict."""
    from hook import catalog_agent_hook

    result = catalog_agent_hook(
        extracted_text="test_column: a sample column description",
        mouse_x=100,
        mouse_y=200,
        ocr_metadata={"char_count": 40, "confidence_avg": 0.92},
    )

    assert isinstance(result, dict), "Hook must return a dict"
    assert result["status"] == "stub_ok", f"Expected stub_ok, got {result['status']}"
    assert result["cursor"] == {"x": 100, "y": 200}, "Cursor position mismatch"
    assert result["captured_text"] == "test_column: a sample column description"
    assert result["agent_response"] is None, "Stub should have agent_response=None"
    print(f"  PASS: hook returned payload with status={result['status']}")


def test_full_pipeline_integration():
    """
    End-to-end integration test in mock mode:
    hotkey trigger → capture → OCR → hook.
    """
    from pipeline import on_hotkey_triggered

    result = on_hotkey_triggered()

    assert isinstance(result, dict), "Pipeline must return a dict"
    assert result["status"] == "stub_ok", "Pipeline should complete with stub_ok"
    assert result["char_count"] > 0, "Pipeline should produce text"
    assert result["cursor"]["x"] >= 0 and result["cursor"]["y"] >= 0
    print(f"  PASS: full pipeline returned {result['char_count']} chars, status={result['status']}")


def test_overlay_mock_no_crash():
    """Overlay should not crash in mock mode (no display)."""
    try:
        overlay.show_capture_flash(960, 540)
        print("  PASS: overlay mock completed without error")
    except Exception as e:
        assert False, f"Overlay should not crash in mock mode: {e}"


def run_all():
    """Run all tests manually (no pytest needed)."""
    tests = [
        test_mouse_position_mock,
        test_capture_region_returns_image,
        test_ocr_extract_returns_structured_result,
        test_ocr_meets_char_threshold,
        test_hook_returns_payload,
        test_full_pipeline_integration,
        test_overlay_mock_no_crash,
    ]

    print("=" * 60)
    print("Running Capture Pipeline Tests (MOCK MODE)")
    print("=" * 60)

    passed = 0
    failed = 0
    for test_fn in tests:
        name = test_fn.__name__
        try:
            print(f"\n[TEST] {name}")
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
