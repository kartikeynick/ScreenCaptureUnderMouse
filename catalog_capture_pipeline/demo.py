"""
demo.py — Interactive demo: real screen capture + visual overlay + live output.

No EasyOCR needed. Uses real mss capture and real tkinter overlay.
Saves a screenshot of exactly what was captured so you can see it.

Usage:
    python demo.py

    Move your mouse over any text on screen, then press Enter in the terminal.
"""

import sys
import os
import time
import threading

# Ensure imports work from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force real capture + overlay, but keep OCR mocked
import config
config.MOCK_MODE = False          # real mss + real overlay

import capture
import overlay
import ocr_engine
import hook

capture.MOCK_MODE = False
overlay.MOCK_MODE = False
ocr_engine.MOCK_MODE = True       # skip EasyOCR — use mock text


def run_demo():
    print("\n" + "=" * 60)
    print("  Catalog Capture Pipeline — LIVE DEMO")
    print("=" * 60)
    print("\n  1. Move your mouse over any text on your screen.")
    print("  2. KEEP YOUR MOUSE THERE — don't click back here.")
    print("  3. The capture fires automatically after a 4-second countdown.")
    print("\n  (You'll see a green box flash where the capture happened)")
    print("-" * 60)
    input("\n  >>> Press Enter to start the countdown, then move your mouse to the target...\n")

    for i in range(4, 0, -1):
        print(f"  Capturing in {i}...", flush=True)
        time.sleep(1)
    print("  CAPTURING NOW!", flush=True)

    # Step 1: Real mouse position
    mouse_x, mouse_y = capture.get_mouse_position()
    print(f"  Mouse position  : ({mouse_x}, {mouse_y})")

    # Step 2: Real screen capture
    image = capture.capture_region(mouse_x, mouse_y)
    print(f"  Captured region : {image.size[0]}x{image.size[1]}px around cursor")

    # Step 3: Show the real green flash overlay
    overlay.show_capture_flash(mouse_x, mouse_y)
    print(f"  Overlay         : green box flashed at ({mouse_x}, {mouse_y})")

    # Step 4: Save screenshot so you can inspect it
    screenshot_path = os.path.join(os.path.dirname(__file__), "assets", "last_capture.png")
    image.save(screenshot_path)
    print(f"  Screenshot saved: {screenshot_path}")

    # Step 5: Mock OCR (swap for real EasyOCR later)
    ocr_result = ocr_engine.extract_text(image)
    print(f"  OCR text        : \"{ocr_result['raw_text'][:80]}...\"")
    print(f"  Chars / Words   : {ocr_result['char_count']} chars, {ocr_result['word_count']} words")

    # Step 6: Agent hook payload
    result = hook.catalog_agent_hook(
        extracted_text=ocr_result["raw_text"],
        mouse_x=mouse_x,
        mouse_y=mouse_y,
        ocr_metadata=ocr_result,
    )

    print("\n" + "=" * 60)
    print("  Pipeline Output")
    print("=" * 60)
    for k, v in result.items():
        if k == "captured_text":
            print(f"  {k:<18}: {str(v)[:70]}")
        else:
            print(f"  {k:<18}: {v}")

    print("=" * 60)
    print(f"\n  Open {screenshot_path}")
    print("  to see exactly what pixel region was captured.\n")


if __name__ == "__main__":
    run_demo()
