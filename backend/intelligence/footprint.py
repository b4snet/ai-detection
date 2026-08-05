"""Consent-based public digital footprint audit.

This module intentionally does not identify people from faces, scrape private data,
collect phone numbers, infer current/last-seen locations, or bypass platform access
controls. It only produces public-source search leads from identifiers supplied by
an authorized user.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import quote_plus

from backend.intelligence import osint

SAFE_NOTICE = (
    "Consent-based audit only. Results are public-source leads, not identity proof. "
    "Do not use for stalking, doxxing, harassment, or location tracking."
)

PLATFORMS = [
    {"name": "LinkedIn", "url": "https://www.linkedin.com/search/results/all/?keywords={q}", "type": "professional"},
    {"name": "GitHub", "url": "https://github.com/search?q={q}&type=users", "type": "developer"},
    {"name": "X / Twitter", "url": "https://twitter.com/search?q={q}&src=typed_query", "type": "social"},
    {"name": "Instagram", "url": "https://www.instagram.com/explore/search/keyword/?q={q}", "type": "social"},
    {"name": "Facebook", "url": "https://www.facebook.com/search/top?q={q}", "type": "social"},
    {"name": "Reddit", "url": "https://www.reddit.com/search/?q={q}", "type": "community"},
    {"name": "YouTube", "url": "https://www.youtube.com/results?search_query={q}", "type": "media"},
    {"name": "Google", "url": "https://www.google.com/search?q={q}", "type": "web_search"},
]


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())[:160]


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _handle_variants(username: str) -> List[str]:
    u = username.strip().lstrip("@")
    if not u:
        return []
    variants = [u]
    if "." in u or "_" in u:
        variants.append(u.replace(".", " ").replace("_", " "))
    return list(dict.fromkeys(variants))


def build_queries(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    name = _clean(payload.get("name"))
    email = _clean(payload.get("email"))
    username = _clean(payload.get("username"))
    domain = _clean(payload.get("domain"))
    location = _clean(payload.get("known_location"))

    queries: List[Dict[str, str]] = []
    if name:
        queries.append({"label": "name", "query": f'"{name}"'})
        if location:
            queries.append({"label": "name + provided location", "query": f'"{name}" "{location}"'})
    if email and _valid_email(email):
        queries.append({"label": "email", "query": f'"{email}"'})
        queries.append({"label": "email username", "query": email.split("@")[0]})
    if username:
        for v in _handle_variants(username):
            queries.append({"label": "username", "query": f'"{v}"'})
    if domain:
        queries.append({"label": "domain", "query": f'site:{domain} {name or username or email}'})

    seen = set()
    unique = []
    for q in queries:
        if q["query"] and q["query"] not in seen:
            seen.add(q["query"])
            unique.append(q)
    return unique[:8]


def platform_leads(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    name = _clean(payload.get("name"))
    email = _clean(payload.get("email"))
    username = _clean(payload.get("username"))
    terms = [t for t in [username.lstrip("@"), name, email] if t]
    q = quote_plus(" ".join(terms[:2]) or "digital footprint")
    return [
        {
            "platform": p["name"],
            "category": p["type"],
            "search_url": p["url"].format(q=q),
            "status": "manual_review_required",
        }
        for p in PLATFORMS
    ]


def run_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not payload.get("consent"):
        raise ValueError("Consent/authorization is required for a footprint audit.")

    queries = build_queries(payload)
    findings: List[Dict[str, Any]] = []
    for q in queries:
        for item in osint.search_all(q["query"], limit=5):
            item = dict(item)
            item["matched_query"] = q["label"]
            item["verification"] = "PUBLIC LEAD - HUMAN REVIEW REQUIRED"
            findings.append(item)

    seen = set()
    deduped = []
    for f in findings:
        key = f.get("url") or f.get("title")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)
    deduped.sort(key=lambda f: f.get("relevance", 0), reverse=True)

    identifiers = sum(1 for k in ["name", "email", "username", "domain", "known_location"] if _clean(payload.get(k)))
    confidence = min(0.9, 0.18 * identifiers + 0.04 * min(len(deduped), 10))

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notice": SAFE_NOTICE,
        "input_summary": {
            "name_supplied": bool(_clean(payload.get("name"))),
            "email_supplied": bool(_clean(payload.get("email"))),
            "username_supplied": bool(_clean(payload.get("username"))),
            "domain_supplied": bool(_clean(payload.get("domain"))),
            "known_location_supplied": bool(_clean(payload.get("known_location"))),
        },
        "queries": queries,
        "confidence": round(confidence, 2),
        "findings": deduped[:25],
        "platform_leads": platform_leads(payload),
        "guardrails": [
            "No face identification or biometric matching performed.",
            "No private account access, phone scraping, or current-location tracking.",
            "Locations are only user-provided context or public article references.",
            "Every result must be verified by a human before use.",
        ],
    }
