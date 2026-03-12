"""
live_demo.py — Real hotkey-driven capture pipeline.

Hover over any word on screen → press Ctrl+' → box flashes → text captured.

Usage:
    python live_demo.py

Press Ctrl+C in terminal to quit.
"""

import sys
import os
import time
import math
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Real screen capture + overlay, mock OCR (no EasyOCR needed)
import config
config.MOCK_MODE = False

import capture
import overlay
import ocr_engine
import hook

capture.MOCK_MODE = False
overlay.MOCK_MODE = False
ocr_engine.MOCK_MODE = False  # real EasyOCR

logging.basicConfig(
    level=logging.WARNING,  # suppress noisy INFO logs during interactive use
    format="%(message)s",
)

CAPTURES = []


def extract_target_word(image, full_ocr_segments):
    """
    Crops a small region from the CENTER of the captured image
    (where the cursor is) and OCRs just that slice to get the target word.

    Falls back to closest segment from full OCR if the crop returns nothing.
    """
    from PIL import Image as PILImage

    CROP_W, CROP_H = 250, 70
    img_w, img_h = image.size
    cx, cy = img_w // 2, img_h // 2

    crop_box = (
        max(0, cx - CROP_W // 2),
        max(0, cy - CROP_H // 2),
        min(img_w, cx + CROP_W // 2),
        min(img_h, cy + CROP_H // 2),
    )
    word_crop = image.crop(crop_box)
    crop_result = ocr_engine.extract_text(word_crop)
    target = crop_result["raw_text"].strip()

    if target:
        # Take only the first word from the crop result
        return target.split()[0], "crop"

    # Fallback: closest segment center to image center
    cursor_x, cursor_y = img_w / 2, img_h / 2
    closest_text, min_dist = None, float("inf")
    for seg in full_ocr_segments:
        bbox = seg["bbox"]
        c_bx = sum(p[0] for p in bbox) / 4
        c_by = sum(p[1] for p in bbox) / 4
        dist = math.sqrt((c_bx - cursor_x) ** 2 + (c_by - cursor_y) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest_text = seg["text"].split()[0]
    return closest_text, "fallback"


def on_hotkey():
    """Runs the full pipeline on each Ctrl+' press."""
    t = time.time()

    mouse_x, mouse_y = capture.get_mouse_position()
    image = capture.capture_region(mouse_x, mouse_y)
    overlay.show_capture_flash(mouse_x, mouse_y)

    # Save screenshot
    screenshot_path = os.path.join(os.path.dirname(__file__), "assets", "last_capture.png")
    image.save(screenshot_path)

    ocr_result = ocr_engine.extract_text(image)

    # Extract target word by cropping center of image and OCR-ing just that slice
    target_word, method = extract_target_word(image, ocr_result["segments"])

    result = hook.catalog_agent_hook(
        extracted_text=ocr_result["raw_text"],
        mouse_x=mouse_x,
        mouse_y=mouse_y,
        ocr_metadata=ocr_result,
    )

    elapsed = round(time.time() - t, 3)
    CAPTURES.append(result)

    # Save both outputs to txt file
    txt_path = os.path.join(os.path.dirname(__file__), "assets", "captures.txt")
    with open(txt_path, "a", encoding="utf-8") as f:
        f.write(f"--- Capture #{len(CAPTURES)} | {time.strftime('%Y-%m-%d %H:%M:%S')} | cursor ({mouse_x}, {mouse_y}) ---\n")
        f.write(f"TARGET WORD : {target_word}  [{method}]\n")
        f.write(f"CONTEXT     : {ocr_result['raw_text']}\n\n")

    print(f"\n{'─' * 55}")
    print(f"  Capture #{len(CAPTURES)}  |  {elapsed}s  |  cursor ({mouse_x}, {mouse_y})")
    print(f"{'─' * 55}")
    print(f"  TARGET WORD : \"{target_word}\"  [{method}]")
    print(f"  CONTEXT     : \"{ocr_result['raw_text'][:120]}\"")
    print(f"  Segments    : {len(ocr_result['segments'])}  |  Chars: {ocr_result['char_count']}")
    print(f"  Screenshot  → {screenshot_path}")
    print(f"  Text log    → {txt_path}")
    print(f"{'─' * 55}")
    print("  (hover over text and press Ctrl+' again, or Ctrl+C to quit)\n")


def main():
    from pynput import keyboard

    print("\n" + "=" * 55)
    print("  Catalog Capture Pipeline — LIVE HOTKEY MODE")
    print("=" * 55)
    print("  Hover over any word on screen and press Ctrl+'")
    print("  A green box will flash and the text will be captured.")
    print("  Press Ctrl+C here to stop.\n")

    ctrl_held = False

    def on_press(key):
        nonlocal ctrl_held
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            ctrl_held = True
        elif ctrl_held and (
            (hasattr(key, 'char') and key.char == "'") or
            (hasattr(key, 'vk') and key.vk == 222)
        ):
            try:
                print("\n  [DEBUG] Hotkey detected — running pipeline...")
                on_hotkey()
            except Exception as e:
                import traceback
                print(f"\n  [ERROR] Pipeline crashed: {e}")
                traceback.print_exc()

    def on_release(key):
        nonlocal ctrl_held
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            ctrl_held = False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            pass

    print(f"\n  Session ended. Total captures: {len(CAPTURES)}\n")


if __name__ == "__main__":
    main()
