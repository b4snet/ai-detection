"""Authorized Nepal identity directory matcher.

Only matches uploaded images against profiles that were manually enrolled with
consent. It does not scrape the internet, does not identify random people, and
returns no fake/demo identities.
"""
from __future__ import annotations

import json
import math
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
PROFILE_DB = settings.data / "authorized_nepal_profiles.json"
REFERENCE_DIR = settings.data / "authorized_directory"
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json() -> List[Dict[str, Any]]:
    if not PROFILE_DB.exists():
        PROFILE_DB.write_text("[]", encoding="utf-8")
    try:
        data = json.loads(PROFILE_DB.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_json(profiles: List[Dict[str, Any]]) -> None:
    PROFILE_DB.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")


def load_profiles() -> List[Dict[str, Any]]:
    return _read_json()


def _validate_image_name(filename: str) -> str:
    ext = Path(filename or "upload.jpg").suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Unsupported image type. Use jpg/png/webp/bmp.")
    return ext


def save_upload(file_bytes: bytes, filename: str) -> str:
    ext = _validate_image_name(filename)
    stored = f"directory_query_{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
    dest = settings.uploads / stored
    dest.write_bytes(file_bytes)
    return stored


def enroll_profile(profile: Dict[str, Any], image_bytes: bytes, filename: str) -> Dict[str, Any]:
    ext = _validate_image_name(filename)
    profile_id = f"np-{uuid.uuid4().hex[:10]}"
    ref_name = f"{profile_id}{ext}"
    (REFERENCE_DIR / ref_name).write_bytes(image_bytes)

    socials = {
        k: v.strip()
        for k, v in (profile.get("public_socials") or {}).items()
        if isinstance(v, str) and v.strip()
    }
    row = {
        "id": profile_id,
        "consent_status": "authorized",
        "name": (profile.get("name") or "").strip(),
        "city": (profile.get("city") or "").strip(),
        "district": (profile.get("district") or "").strip(),
        "province": (profile.get("province") or "").strip(),
        "public_socials": socials,
        "notes": (profile.get("notes") or "").strip(),
        "reference_image": ref_name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if not row["name"]:
        raise ValueError("Name is required.")

    profiles = load_profiles()
    profiles.append(row)
    _write_json(profiles)
    return row


def _fingerprint(path: Path) -> List[float]:
    """Simple image fingerprint for an authorized-directory prototype."""
    try:
        from PIL import Image, ImageStat

        img = Image.open(path).convert("RGB").resize((48, 48))
        stat = ImageStat.Stat(img)
        means = [v / 255.0 for v in stat.mean]
        hist = img.histogram()
        buckets = []
        for channel in range(3):
            h = hist[channel * 256:(channel + 1) * 256]
            total = sum(h) or 1
            buckets.extend(sum(h[i:i + 16]) / total for i in range(0, 256, 16))
        return means + buckets
    except Exception as exc:
        raise ValueError(f"Could not process image: {exc}") from exc


def _similarity(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dist = math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)) / n)
    return max(0.0, min(1.0, 1.0 - dist))


def match_authorized(stored_upload: str) -> Dict[str, Any]:
    upload_path = settings.uploads / stored_upload
    profiles = [p for p in load_profiles() if p.get("reference_image")]
    if not profiles:
        return {
            "scope": "Nepal authorized directory only",
            "notice": "No enrolled profiles found. Enroll authorized profiles first.",
            "uploaded_image": f"/uploads/{stored_upload}",
            "matches": [],
        }

    upload_fp = _fingerprint(upload_path)
    matches = []
    for profile in profiles:
        ref_path = REFERENCE_DIR / profile["reference_image"]
        if not ref_path.exists():
            continue
        score = _similarity(upload_fp, _fingerprint(ref_path))
        matches.append({
            "profile": profile,
            "confidence": round(score, 3),
            "method": "authorized_reference_image",
            "verification": "AUTHORIZED DIRECTORY MATCH - HUMAN CONFIRMATION REQUIRED",
        })

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return {
        "scope": "Nepal authorized directory only",
        "notice": "Results come only from enrolled consent-based profiles. No fake/demo identities are generated.",
        "uploaded_image": f"/uploads/{stored_upload}",
        "matches": matches[:5],
    }
