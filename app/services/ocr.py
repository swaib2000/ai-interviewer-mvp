from __future__ import annotations

import time
from typing import Tuple

from PIL import Image


def run_ocr(image_path: str) -> Tuple[str, float]:
    """
    Returns (text, latency_ms).
    Tries pytesseract if available; else returns a safe placeholder.
    """
    t0 = time.time()
    try:
        import pytesseract  # type: ignore

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        ms = (time.time() - t0) * 1000.0
        text = (text or "").strip()
        return text, ms
    except Exception:
        ms = (time.time() - t0) * 1000.0
        # Hackathon-safe fallback
        return "Content: (OCR unavailable)", ms

