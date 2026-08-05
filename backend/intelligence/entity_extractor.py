"""SENTINEL AI - entity extraction & profile assembly.

Turns raw vision + OCR + OSINT evidence into structured EntityProfile
objects. Uses the local LLM when reachable; otherwise a conservative
rule-based extractor. Entities are descriptive records with confidence,
sources and a verification flag - they never assert intent.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.core.logging import log
from backend.intelligence import llm
from backend.intelligence import osint as osint_mod

_ALIAS_HINTS = re.compile(r"\b(aka|alias|known as|a\.k\.a\.)\s+([A-Za-z0-9 ._-]+)", re.I)


def extract_profiles(
    vision: Dict[str, Any], search_terms: List[str], top_query: str
) -> List[Dict[str, Any]]:
    """Build EntityProfile dicts from vision + OSINT."""
    profiles: List[Dict[str, Any]] = []

    # 1) Faces -> anonymous person-of-interest placeholder (never named)
    faces = vision.get("faces", {})
    if faces.get("detected") and faces.get("count", 0) > 0:
        profiles.append(
            {
                "name": "UNIDENTIFIED PERSON(S) - subject of image",
                "entity_type": "person",
                "confidence": float(faces.get("confidence", 0.5)),
                "description": (
                    "Human presence detected in image. SENTINEL does NOT "
                    "identify or name individuals autonomously. Identity "
                    "confirmation requires authorized human analysis."
                ),
                "aliases": [],
                "public_mentions": 0,
                "verification": "PENDING HUMAN REVIEW",
                "associated_sources": [],
                "timeline": [],
                "risk_indicators": [
                    {
                        "indicator": "Face presence detected",
                        "severity": "informational",
                        "note": "No identity asserted automatically",
                    }
                ],
            }
        )

    # 2) Vehicles
    for v in vision.get("vehicles", []):
        profiles.append(
            {
                "name": f"Vehicle: {v['label'].capitalize()}",
                "entity_type": "vehicle",
                "confidence": float(v.get("confidence", 0.5)),
                "description": (
                    f"{v['label'].capitalize()} detected with "
                    f"{v['confidence']:.0%} confidence."
                ),
                "aliases": [],
                "public_mentions": 0,
                "verification": "PENDING HUMAN REVIEW",
                "associated_sources": [],
                "timeline": [],
                "risk_indicators": [],
            }
        )

    # 3) Plates / credential text -> potential entity handles
    plates = vision.get("plates", [])
    for plate in plates:
        profiles.append(
            {
                "name": f"Plate marker '{plate}'",
                "entity_type": "vehicle",
                "confidence": 0.6,
                "description": (
                    "License-plate-like text captured by OCR. Requires "
                    "authorized registry lookup - NOT performed here."
                ),
                "aliases": [],
                "public_mentions": 0,
                "verification": "PENDING HUMAN REVIEW",
                "associated_sources": [],
                "timeline": [],
                "risk_indicators": [],
            }
        )

    # 4) OSINT-driven entity discovery via LLM
    text = _text_blob(vision)
    if text:
        for raw in llm.extract_entities(text)[:5]:
            profiles.append(
                {
                    "name": raw.get("name", ""),
                    "entity_type": raw.get("entity_type", "person"),
                    "confidence": float(raw.get("confidence", 0.4)),
                    "description": raw.get("context", ""),
                    "aliases": _aliases_from(text, raw.get("name", "")),
                    "public_mentions": 0,
                    "verification": "PENDING HUMAN REVIEW",
                    "associated_sources": [],
                    "timeline": [],
                    "risk_indicators": [],
                }
            )

        # 4b) Heuristic fallback from visible OCR text (no LLM required)
        for ent in _heuristic_entities(text):
            if ent["name"].lower() not in {p["name"].lower() for p in profiles}:
                profiles.append(ent)

    # 5) Enrich each profile with OSINT sources + timeline (parallel)
    from concurrent.futures import ThreadPoolExecutor

    def _run(prof):
        _enrich(prof, search_terms, top_query)
        return prof

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(profiles)))) as ex:
        profiles = list(ex.map(_run, profiles))

    # dedupe by normalized name
    seen = set()
    out = []
    for p in profiles:
        key = p["name"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


# ------------------------------------------------------------------ helpers ---
def _text_blob(vision: Dict[str, Any]) -> str:
    parts = []
    for frag in vision.get("text", {}).get("fragments", []):
        parts.append(frag)
    for clue in vision.get("location", {}).get("clues", []):
        parts.append(clue)
    for note in vision.get("notes", []):
        parts.append(note)
    return " | ".join(parts)


def _heuristic_entities(text: str) -> List[Dict[str, Any]]:
    """Extract candidate entities from visible OCR text without an LLM.

    Strategy:
      * match known demo seed terms (bundled fictional dataset)
      * capture long ALL-CAPS phrases (signage / organization names)
      * capture 'X - TERMINAL', 'LOGISTICS', 'MONITOR' style patterns
    """
    profiles: List[Dict[str, Any]] = []
    seen: set[str] = set()
    lower = text.lower()

    # 1) known demo seed terms
    data = osint_mod._load_simulated()
    for ent in data.get("entities", []):
        for term in ent.get("seed_terms", []):
            if term.lower() in lower and term.lower() not in seen:
                seen.add(term.lower())
                profiles.append(
                    {
                        "name": ent.get("name", term.capitalize()),
                        "entity_type": ent.get("entity_type", "person"),
                        "confidence": 0.6,
                        "description": ent.get("description", ""),
                        "aliases": ent.get("aliases", []),
                        "public_mentions": 0,
                        "verification": "PENDING HUMAN REVIEW",
                        "associated_sources": [],
                        "timeline": [],
                        "risk_indicators": [
                            {
                                "indicator": "Visible text entity",
                                "severity": "informational",
                                "note": "Matched text visible in image",
                            }
                        ],
                    }
                )

    # 2) ALL-CAPS word sequences (>=2 tokens or a single meaningful word)
    for m in re.finditer(r"\b([A-Z][A-Z0-9&\. ]{5,60})\b", text):
        phrase = m.group(1).strip()
        # skip if mostly a plate or timestamp-like pattern
        if re.search(r"\d{3,}", phrase) and not re.search(r"[A-Z]{3,}", phrase):
            continue
        key = phrase.lower()
        if key in seen or len(phrase) < 5:
            continue
        seen.add(key)
        profiles.append(
            {
                "name": phrase.title(),
                "entity_type": _guess_type(phrase),
                "confidence": 0.5,
                "description": (
                    f"Text phrase visible in image: '{phrase}'. Candidate "
                    "organization / signage identifier. Human verification required."
                ),
                "aliases": [],
                "public_mentions": 0,
                "verification": "PENDING HUMAN REVIEW",
                "associated_sources": [],
                "timeline": [],
                "risk_indicators": [],
            }
        )
        if len(profiles) >= 6:
            break
    return profiles


def _guess_type(phrase: str) -> str:
    p = phrase.lower()
    if any(w in p for w in ("logistics", "terminal", "industries", "corp", "inc", "ltd", "co")):
        return "organization"
    if any(w in p for w in ("street", "road", "avenue", "district", "port", "terminal")):
        return "location"
    return "organization"


def _aliases_from(text: str, name: str) -> List[str]:
    aliases = []
    for m in _ALIAS_HINTS.finditer(text):
        a = m.group(2).strip()
        if a and a.lower() != name.lower():
            aliases.append(a)
    return list(dict.fromkeys(aliases))[:5]


def _clean_search(name: str) -> str:
    """Turn a profile label into a sensible search query."""
    s = name
    # Strip quoting / prefixes used by the profile builder.
    s = re.sub(r"^Synthetic (Subject|Org)\s*'", "", s)
    s = s.replace("'", "")
    s = re.sub(r"^(Vehicle|Plate marker|UNIDENTIFIED)\s*[: ]", "", s)
    if s.startswith("Plate marker"):
        s = re.sub(r"[^A-Z0-9]", "", s)
    s = s.strip()
    if len(s) < 2:
        return ""
    # Keep only first ~4 meaningful tokens.
    return " ".join(s.split()[:4])


def _enrich(prof: Dict[str, Any], search_terms: List[str], top_query: str) -> None:
    """Attach OSINT findings + timeline + mention counts to a profile."""
    search = _clean_search(prof["name"])

    if not search:
        # Anonymous profile: still surface generic reference search.
        findings = osint_mod.search_all(top_query, limit=3)
    else:
        findings = osint_mod.search_all(search, limit=5)

    prof["associated_sources"] = [
        {
            "title": f.get("title"),
            "url": f.get("url"),
            "source": f.get("source"),
            "source_type": f.get("source_type"),
            "published_at": f.get("published_at"),
            "relevance": f.get("relevance"),
        }
        for f in findings
    ]
    prof["public_mentions"] = len(findings)

    prof["timeline"] = osint_mod.enrich_timeline(search, limit=4) if search else []

    if prof["public_mentions"] > 0:
        prof["risk_indicators"].append(
            {
                "indicator": f"Public-source references found ({prof['public_mentions']})",
                "severity": "informational",
                "note": "References are evidence of public presence, not culpability",
            }
        )
    # Update confidence with evidence.
    base = prof["confidence"]
    prof["confidence"] = round(min(0.95, base + 0.05 * prof["public_mentions"]), 3)
    log("info", f"Entity profile assembled: {prof['name']} "
                f"(mentions={prof['public_mentions']})")
