"""SENTINEL AI - OSINT retrieval engine.

Collects publicly available information from:

  * Wikipedia REST API        (no key, reliable)
  * GDELT news API            (free, real-time global news graph)
  * Simulated demonstration   (bundled fictional dataset used when the
                               pipeline has no live key / for demos)

Every finding carries: source, source_type, published_at, relevance,
and an explicit verification status. Findings are evidence, never
conclusions.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from backend.config import settings
from backend.core.logging import log

_CACHE_DIR = settings.data / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)


# ------------------------------------------------------------------ cache ----
_NETWORK_BLOCKED_UNTIL = 0.0  # circuit breaker: skip live sources briefly


def _network_allowed() -> bool:
    return time.time() >= _NETWORK_BLOCKED_UNTIL


def _block_network(seconds: int = 60) -> None:
    global _NETWORK_BLOCKED_UNTIL
    _NETWORK_BLOCKED_UNTIL = time.time() + seconds
    log("warning", f"Live OSINT sources temporarily suspended ({seconds}s) "
                   "after repeated failures")


def _cache_key(kind: str, query: str) -> str:
    return hashlib.md5(f"{kind}:{query}".encode()).hexdigest()[:16]


def _cache_get(kind: str, query: str) -> Optional[List[Dict[str, Any]]]:
    path = _CACHE_DIR / f"{kind}_{_cache_key(kind, query)}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("ts", 0) < data.get("ttl", settings.cache_age_hours * 3600):
            return data.get("items")
    except Exception:
        pass
    return None


def _cache_set(kind: str, query: str, items: List[Dict[str, Any]]) -> None:
    """Cache any result, including empty ones (negative caching).

    Empty results get a short TTL so transient network failures don't
    permanently poison the cache but repeated lookups stay fast.
    """
    path = _CACHE_DIR / f"{kind}_{_cache_key(kind, query)}.json"
    ttl = 1800 if not items else settings.cache_age_hours * 3600
    try:
        path.write_text(
            json.dumps(
                {"ts": time.time(), "ttl": ttl, "items": items},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


# --------------------------------------------------------------- sources -----
def _to_finding(
    title: str, source: str, url: str, source_type: str,
    published_at: str, snippet: str, relevance: float,
) -> Dict[str, Any]:
    return {
        "title": title,
        "source": source,
        "url": url,
        "source_type": source_type,
        "published_at": published_at,
        "snippet": snippet[:800],
        "relevance": round(relevance, 3),
        "verified": "UNVERIFIED",
        "fetched_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


def search_wikipedia(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    cached = _cache_get("wiki", query)
    if cached is not None:
        return cached
    items: List[Dict[str, Any]] = []
    if not _network_allowed():
        return items
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "format": "json",
            },
            timeout=4,
        )
        r.raise_for_status()
        for hit in r.json().get("query", {}).get("search", []):
            title = hit.get("title", "")
            page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            items.append(
                _to_finding(
                    title=f"Wikipedia: {title}",
                    source="Wikipedia (public)",
                    url=page_url,
                    source_type="public_db",
                    published_at="",
                    snippet=re.sub(r"<[^>]+>", "", hit.get("snippet", "")),
                    relevance=float(hit.get("score", 0)) / 1000.0,
                )
            )
    except Exception as exc:
        log("warning", f"Wikipedia search failed for '{query}': {exc}")
        if isinstance(exc, requests.exceptions.RequestException):
            _block_network()
    _cache_set("wiki", query, items)
    return items


def search_gdelt(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    cached = _cache_get("gdelt", query)
    if cached is not None:
        return cached
    items: List[Dict[str, Any]] = []
    if not settings.gdelt_enabled or not _network_allowed():
        return items
    try:
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": f'"{query}"',
                "mode": "artlist",
                "maxrecords": limit,
                "format": "json",
                "timespan": "5y",
            },
            timeout=5,
        )
        r.raise_for_status()
        for art in r.json().get("articles", []):
            items.append(
                _to_finding(
                    title=art.get("title", "Untitled"),
                    source=art.get("domain", "news"),
                    url=art.get("url", ""),
                    source_type="news",
                    published_at=art.get("seendate", "")[:8],
                    snippet=art.get("snippet", ""),
                    relevance=0.5,
                )
            )
    except Exception as exc:
        log("warning", f"GDELT search failed for '{query}': {exc}")
        if isinstance(exc, requests.exceptions.RequestException):
            _block_network()
    _cache_set("gdelt", query, items)
    return items


def _load_simulated() -> Dict[str, Any]:
    try:
        entities = json.loads(
            (settings.data / "entities.json").read_text(encoding="utf-8")
        )
        articles = json.loads(
            (settings.data / "articles.json").read_text(encoding="utf-8")
        )
        events = json.loads(
            (settings.data / "events.json").read_text(encoding="utf-8")
        )
        return {"entities": entities, "articles": articles, "events": events}
    except Exception:
        return {"entities": [], "articles": [], "events": []}


def search_simulated(query: str) -> List[Dict[str, Any]]:
    """Match bundled fictional demo records against the query terms."""
    data = _load_simulated()
    q = query.lower()
    articles = data.get("articles", [])
    entities = data.get("entities", [])

    seed_terms = [query]
    for ent in entities:
        if ent.get("name", "").lower() in q or any(
            t in q for t in ent.get("seed_terms", [])
        ):
            seed_terms.extend(ent.get("seed_terms", []))

    items: List[Dict[str, Any]] = []
    for art in articles:
        blob = (
            art.get("title", "") + " " + art.get("snippet", "")
        ).lower()
        score = 0.0
        for term in seed_terms:
            if term.lower() in blob:
                score += 0.35
        art_entities = [e.lower() for e in art.get("entities", [])]
        for term in seed_terms:
            if term.lower() in art_entities:
                score += 0.2
        if score > 0:
            items.append(
                _to_finding(
                    title=art["title"],
                    source=f"{art['source']} [SIMULATED]",
                    url=art["url"],
                    source_type=art["source_type"],
                    published_at=art["published_at"],
                    snippet=art["snippet"],
                    relevance=min(1.0, score + art.get("relevance", 0.5) / 3),
                )
            )
    items.sort(key=lambda i: i["relevance"], reverse=True)
    return items


# ----------------------------------------------------------------- public -----
def search_all(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Search all enabled sources, deduped by URL, ranked by relevance."""
    findings: List[Dict[str, Any]] = []

    if settings.osint_enabled:
        findings += search_wikipedia(query, limit=min(limit, 4))
        findings += search_gdelt(query, limit=min(limit, 5))

    simulated = search_simulated(query)
    findings += simulated

    if not findings and not settings.osint_enabled:
        log("info", "OSINT disabled - returning simulated references")

    # dedupe + sort
    seen = set()
    deduped = []
    for f in findings:
        key = f.get("url") or f.get("title")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)
    deduped.sort(key=lambda f: f["relevance"], reverse=True)
    return deduped[:limit]


def enrich_timeline(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Extract dated findings into timeline events."""
    findings = search_all(query, limit=limit * 2)
    timeline = []
    for f in findings:
        date = f.get("published_at", "")
        if date and re.match(r"^\d{4}", str(date)):
            timeline.append(
                {
                    "date": str(date)[:7],
                    "title": f.get("title", ""),
                    "event_type": f.get("source_type", "reference"),
                    "detail": f.get("snippet", "")[:200],
                }
            )
    # ensure newest-first
    timeline.sort(key=lambda t: t["date"], reverse=True)
    return timeline[:limit]
