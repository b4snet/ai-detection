"""Authorized Nepal identity directory matcher.

Matches an uploaded image only against profiles explicitly enrolled in
backend/sample_data/authorized_nepal_profiles.json. It does not scrape the
internet or identify random people.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
PROFILE_DB = settings.data / "authorized_nepal_profiles.json"


def load_profiles() -> List[Dict[str, Any]]:
    if not PROFILE_DB.exists():
        return []
    return json.loads(PROFILE_DB.read_text(encoding="utf-8"))


def save_upload(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename or "upload.jpg").suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Unsupported image type. Use jpg/png/webp/bmp.")
    stored = f"directory_{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
    dest = settings.uploads / stored
    dest.write_bytes(file_bytes)
    return stored


def _fingerprint(path: Path) -> List[float]:
    """Small visual fingerprint. Uses Pillow if available; falls back to file hash."""
    try:
        from PIL import Image, ImageStat

        img = Image.open(path).convert("RGB").resize((32, 32))
        stat = ImageStat.Stat(img)
        means = [v / 255.0 for v in stat.mean]
        hist = img.histogram()
        buckets = []
        for channel in range(3):
            h = hist[channel * 256:(channel + 1) * 256]
            total = sum(h) or 1
            buckets.extend(sum(h[i:i + 32]) / total for i in range(0, 256, 32))
        return means + buckets
    except Exception:
        digest = hashlib.sha256(path.read_bytes()).digest()[:16]
        return [b / 255.0 for b in digest]


def _similarity(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dist = math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)) / n)
    return max(0.0, min(1.0, 1.0 - dist))


def match_authorized(stored_upload: str) -> Dict[str, Any]:
    upload_path = settings.uploads / stored_upload
    profiles = load_profiles()
    upload_fp = _fingerprint(upload_path)
    matches = []

    for profile in profiles:
        ref = (profile.get("reference_image") or "").strip()
        ref_path = settings.data / "authorized_directory" / ref if ref else None
        if ref_path and ref_path.exists():
            score = _similarity(upload_fp, _fingerprint(ref_path))
            method = "authorized_reference_image"
        else:
            # Demo-only deterministic score so the UI works until real enrolled photos are added.
            seed = hashlib.sha256((stored_upload + profile.get("id", "")).encode()).digest()[0]
            score = 0.42 + (seed / 255.0) * 0.28
            method = "demo_placeholder_no_reference_image"
        matches.append({
            "profile": profile,
            "confidence": round(score, 3),
            "method": method,
            "verification": "AUTHORIZED DIRECTORY MATCH - HUMAN CONFIRMATION REQUIRED",
        })

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return {
        "scope": "Nepal authorized directory only",
        "notice": "No internet scraping, no random face identification. Add consent-based profiles and reference images to make real matches.",
        "uploaded_image": f"/uploads/{stored_upload}",
        "matches": matches[:5],
    }
