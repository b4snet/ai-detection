"""SENTINEL AI - vision pipeline orchestrator.

Runs metadata -> YOLO -> faces -> OCR -> scene/clue synthesis and
returns a complete ``VisionAnalysis``-shaped dict.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict

from backend.core.logging import log
from backend.vision import detector, ocr
from backend.vision.metadata import dominant_colors, extract_metadata

# ------------------------------------------------------------- helpers -------
_PLATE_RE = re.compile(r"\b[A-Z]{1,3}[\s\-]?\d{1,4}[\s\-]?[A-Z]{0,3}\b")
_CREDENTIAL_RE = re.compile(
    r"\b(ID|LICENSE|PASSPORT|DRIVER|NATIONAL|AADHAAR|PAN|VOTER|CERTIFICATE)\b",
    re.IGNORECASE,
)
_LOCATION_HINTS = [
    "street", "road", "avenue", "highway", "airport", "station", "terminal",
    "bridge", "building", "office", "mall", "hotel", "hospital", "city",
    "district", "city", "university", "campus", "stadium", "park",
    "downtown", "market", "port", "harbor", "beach",
]

# ------------------------------------------------------------------ main -----
def analyze_image(image_path: str | Path) -> Dict[str, Any]:
    """Full vision pass. Returns dict shaped like ``schemas.VisionAnalysis``."""
    started = time.time()
    path = Path(image_path)
    log("info", f"Vision pipeline started: {path.name}")

    meta = extract_metadata(path)
    obj = detector.detect_objects(path)
    faces = detector.detect_faces(path)
    text_res = ocr.extract_text(path)
    colors = dominant_colors(path, k=4)

    plates = _find_plates(text_res.get("fragments", []))
    credentials = _find_credentials(text_res.get("fragments", []))
    location = _synthesize_location(meta, obj, text_res.get("fragments", []))
    scene = _synthesize_scene(obj, location)

    notes: list[str] = []
    if plates:
        notes.append(f"License-plate-like text detected: {', '.join(plates)}")
    if credentials:
        notes.append("Document/credential keywords present in visible text")
    if meta.get("gps"):
        notes.append(
            f"GPS metadata present - geolocation embedded in file "
            f"({meta['gps']['lat']}, {meta['gps']['lon']})"
        )
    if not detector.vision_stack() or detector.vision_stack() == ["pillow-only"]:
        notes.append(
            "SIMULATION MODE: advanced vision modules (YOLO/OpenCV/EasyOCR) "
            "not installed - run pip install -r requirements-optional.txt"
        )

    result: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "width": meta.get("width", 0),
        "height": meta.get("height", 0),
        "format": meta.get("format", ""),
        "camera_make": meta.get("Make"),
        "camera_model": meta.get("Model"),
        "taken_at": meta.get("DateTimeOriginal"),
        "gps": meta.get("gps", {}),
        "faces": {
            "detected": faces["detected"],
            "count": faces["count"],
            "confidence": faces["confidence"],
        },
        "persons": obj.get("persons", 0),
        "objects": obj.get("objects", []),
        "vehicles": obj.get("vehicles", []),
        "text": {
            "found": text_res.get("found", False),
            "fragments": text_res.get("fragments", []),
            "engine": text_res.get("engine", "none"),
        },
        "location": location,
        "colors": colors,
        "scene": scene,
        "plates": plates,
        "credentials": credentials,
        "notes": notes,
        "processing_ms": int((time.time() - started) * 1000),
        "vision_stack": detector.vision_stack(),
    }
    log("info", f"Vision pipeline complete in {result['processing_ms']}ms")
    return result


# ------------------------------------------------------------- synthesizers ---
def _find_plates(fragments: list[str]) -> list[str]:
    hits = []
    for frag in fragments:
        for m in _PLATE_RE.findall(frag):
            cleaned = re.sub(r"\s+", "", m)
            if 4 <= len(cleaned) <= 9:
                hits.append(cleaned)
    return list(dict.fromkeys(hits))[:5]


def _find_credentials(fragments: list[str]) -> list[str]:
    return list(
        dict.fromkeys(
            m.upper()
            for frag in fragments
            for m in _CREDENTIAL_RE.findall(frag)
        )
    )


def _synthesize_location(
    meta: Dict[str, Any], obj: Dict[str, Any], fragments: list[str]
) -> Dict[str, Any]:
    clues: list[str] = []
    geohints: list[str] = []

    if meta.get("gps"):
        g = meta["gps"]
        geohints.append(f"{g['lat']},{g['lon']}")
        clues.append("Embedded GPS coordinates present in image metadata")

    has_vehicle = bool(obj.get("vehicles"))
    persons = obj.get("persons", 0)
    if has_vehicle and persons >= 1:
        clues.append("Possible roadside / traffic environment")
    elif persons >= 3 and not has_vehicle:
        clues.append("Possible gathering / public event setting")
    elif persons == 1 and not has_vehicle:
        clues.append("Possible individual portrait / indoor setting")

    for frag in fragments:
        low = frag.lower()
        for hint in _LOCATION_HINTS:
            if hint in low:
                clues.append(f'Text references location: "{frag.strip()[:80]}"')
                break

    clues = list(dict.fromkeys(clues))
    return {
        "found": bool(clues) or bool(geohints),
        "clues": clues[:8],
        "geohints": geohints,
    }


def _synthesize_scene(obj: Dict[str, Any], location: Dict[str, Any]) -> list[str]:
    scenes = list(obj.get("scenes", []))
    if location.get("geohints"):
        scenes.append("outdoor (GPS geolocated)")
    return list(dict.fromkeys(scenes)) or ["unclassified"]
