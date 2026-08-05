"""SENTINEL AI - image metadata extraction.

Uses Pillow (always available). Optionally OpenCV for a fast color
profile. Safe for any image Pillow can open.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PIL import ExifTags, Image

from backend.core.logging import log


def _exif_value(raw: Any) -> Any:
    if isinstance(raw, bytes):
        return raw.decode(errors="replace")
    if isinstance(raw, tuple):
        return str(raw)
    return raw


def extract_metadata(image_path: str | Path) -> Dict[str, Any]:
    """Return size, format, EXIF camera/gps/date info."""
    path = Path(image_path)
    meta: Dict[str, Any] = {}
    try:
        with Image.open(path) as im:
            meta["width"] = im.width
            meta["height"] = im.height
            meta["format"] = im.format or ""
            meta["mode"] = im.mode
            exif = im.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id)
                    if tag in (
                        "Make", "Model", "DateTimeOriginal",
                        "Software", "GPSInfo", "DateTime",
                    ):
                        meta[tag] = _exif_value(value)
                gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                if gps:
                    meta["gps"] = _gps_to_latlon(gps)
    except Exception as exc:  # pragma: no cover - file may be corrupt
        meta["error"] = str(exc)
        log("warning", f"Metadata extraction failed: {exc}")
    return meta


def _dms_to_degrees(value) -> float:
    try:
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    except Exception:
        return 0.0


def _gps_to_latlon(gps: Dict[int, Any]) -> Dict[str, float]:
    lat = None
    lon = None
    try:
        if 2 in gps and 4 in gps:
            lat = _dms_to_degrees(gps[2])
            if gps.get(1) in ("S", "S\n"):
                lat = -lat
        if 4 in gps and 2 in gps:
            lon = _dms_to_degrees(gps[4])
            if gps.get(3) in ("W", "W\n"):
                lon = -lon
    except Exception:
        pass
    if lat is None or lon is None:
        return {}
    return {"lat": round(lat, 6), "lon": round(lon, 6)}


def dominant_colors(image_path: str | Path, k: int = 4) -> list[str]:
    """Return a short list of dominant color names using Pillow quantization."""
    from collections import Counter

    names = {
        (0, 0, 0): "black", (255, 255, 255): "white",
        (255, 0, 0): "red", (0, 255, 0): "green",
        (0, 0, 255): "blue", (255, 255, 0): "yellow",
        (255, 165, 0): "orange", (128, 0, 128): "purple",
        (139, 69, 19): "brown", (192, 192, 192): "grey",
        (128, 128, 128): "grey", (0, 128, 128): "teal",
        (255, 192, 203): "pink", (255, 215, 0): "gold",
        (0, 128, 0): "dark green", (70, 130, 180): "steel blue",
    }
    try:
        with Image.open(image_path) as im:
            small = im.convert("RGB").resize((64, 64))
            px = list(small.getdata())
        counts: Counter = Counter()
        for r, g, b in px:
            best = min(
                names,
                key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2,
            )
            counts[names[best]] += 1
        total = sum(counts.values()) or 1
        return [
            f"{color} ({round(100 * cnt / total)}%)"
            for color, cnt in counts.most_common(k)
        ]
    except Exception:
        return []
