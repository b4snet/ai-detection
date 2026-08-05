"""SENTINEL AI - OCR module.

EasyOCR preferred (single pip install, downloads a small model on
first use). If unavailable, falls back to Tesseract if present, then
to a graceful 'not available' result.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from backend.core.logging import log

_OCR = None
_READER = None


def _get_reader():
    global _OCR, _READER
    if _OCR is not None:
        return _READER
    try:
        import easyocr

        log("info", "Loading EasyOCR reader (first run downloads model)...")
        _READER = easyocr.Reader(["en"], gpu=False, verbose=False)
        _OCR = "easyocr"
        return _READER
    except Exception as exc:
        log("warning", f"EasyOCR unavailable ({exc}); trying Tesseract")
        try:
            import pytesseract  # noqa: F401

            _OCR = "tesseract"
            return "tesseract"
        except Exception:
            _OCR = "none"
            return None


def extract_text(image_path: str | Path) -> Dict[str, Any]:
    """Return {found, fragments, engine} or empty."""
    reader = _get_reader()
    if reader is None:
        return {"found": False, "fragments": [], "engine": "none"}

    try:
        if reader == "tesseract":
            import pytesseract

            text = pytesseract.image_to_string(str(image_path))
            frags = _clean_fragments(text)
        else:
            # Load via Pillow -> numpy grayscale. This sidesteps a
            # cv2.imread quirk when ultralytics is imported first
            # (grayscale files come back as (H, W, 1) and crash easyocr).
            from PIL import Image

            import numpy as np

            arr = np.array(
                Image.open(str(image_path)).convert("L")
            )
            raw = reader.readtext(arr)
            frags = [t[1] for t in raw if float(t[2]) > 0.35]
            frags = _clean_fragments(" ".join(frags))
        return {
            "found": bool(frags),
            "fragments": frags,
            "engine": reader if isinstance(reader, str) else "easyocr",
        }
    except Exception as exc:
        log("warning", f"OCR failed: {exc}")
        return {"found": False, "fragments": [], "engine": "error"}


def _clean_fragments(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 3]
    # Drop noise lines (single letters, long URLs keep, junk symbols).
    clean = []
    for ln in lines:
        if all(ch in "-–—|#*" for ch in ln):
            continue
        clean.append(ln[:400])
    return clean[:40]
