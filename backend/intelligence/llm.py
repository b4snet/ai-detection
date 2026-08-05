"""SENTINEL AI - local LLM bridge (Ollama) with deterministic fallback.

Design goal: the intelligence engine MUST work with or without a model
server. When Ollama is unreachable the fallback produces structured,
rule-based analysis so the hackathon demo is never broken.

Ethical guardrails are enforced at the prompt layer and post-processed:
the model is instructed to describe, never to accuse or classify any
individual as a threat.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import requests

from backend.config import settings
from backend.core.logging import log

_SYSTEM_PROMPT = (
    "You are SENTINEL AI, an intelligence analysis ASSISTANT for "
    "authorized security research. RULES: (1) NEVER label, accuse, or "
    "classify any person as a criminal, terrorist, anti-national or threat. "
    "(2) Only report facts, sources, confidence and indicators. "
    "(3) Always recommend human analyst review. "
    "(4) Note data provenance and verification status. "
    "(5) If information is insufficient, say so explicitly."
)

_ollama_status: Optional[bool] = None


# ------------------------------------------------------------- connectivity ---
def ollama_online() -> bool:
    """Cache a lightweight health check against the Ollama server."""
    global _ollama_status
    if _ollama_status is not None:
        return _ollama_status
    try:
        r = requests.get(
            f"{settings.ollama_host}/api/tags", timeout=2,
        )
        _ollama_status = r.status_code == 200
    except Exception:
        _ollama_status = False
    if not _ollama_status:
        log("warning", "Ollama unreachable - using deterministic fallback AI")
    else:
        log("info", f"Ollama connected: {settings.ollama_host}")
    return _ollama_status


def available_models() -> List[str]:
    try:
        r = requests.get(
            f"{settings.ollama_host}/api/tags", timeout=2,
        )
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


# --------------------------------------------------------------- generation ---
def _generate(
    prompt: str, *, model: Optional[str] = None, max_tokens: int = 1024,
    temperature: float = 0.3, system: str = _SYSTEM_PROMPT,
) -> Optional[str]:
    if not ollama_online():
        return None
    payload = {
        "model": model or settings.ollama_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    try:
        r = requests.post(
            f"{settings.ollama_host}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout,
        )
        if r.status_code == 200:
            return r.json().get("response", "")
    except Exception as exc:
        log("warning", f"Ollama generate failed: {exc}")
    return None


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


# ------------------------------------------------------------- intelligence ---
def ai_mode() -> str:
    return "local" if ollama_online() else (
        "simulation" if _force_simulation() else "degraded"
    )


def _force_simulation() -> bool:
    return settings.simulation_mode == "on"


def analyze_findings(context: Dict[str, Any]) -> Dict[str, Any]:
    """Produce the intelligence summary for an analysis.

    context: {vision_summary, osint_findings, entities}
    Returns a ReportSummary-shaped dict.
    """
    if _force_simulation():
        return _fallback_analysis(context)

    prompt = _build_analysis_prompt(context)
    text = _generate(prompt, max_tokens=700, temperature=0.3)
    if not text:
        return _fallback_analysis(context)

    # Best-effort structured parse; fall back to LLM prose otherwise.
    parsed = _extract_json(text)
    if parsed:
        return _normalize_summary(parsed, context)
    return {
        "overview": text.strip(),
        "key_entities": _entities_from_context(context),
        "key_observations": _observations_from_context(context),
        "risk_assessment": "INDICATORS ONLY - no autonomous classification",
        "recommendation": "Forward to human analyst for verification.",
        "confidence": _confidence_from_context(context),
        "verification": "PENDING HUMAN REVIEW",
    }


def extract_entities(text: str) -> List[Dict[str, Any]]:
    """Extract named entities (persons/orgs/locations/events)."""
    if _force_simulation() or not text.strip():
        return []

    prompt = (
        "From the following intelligence data, list named entities. "
        "Return STRICT JSON: {\"entities\": [{\"name\": str, "
        "\"entity_type\": \"person|organization|location|vehicle|object\", "
        "\"confidence\": 0-1, \"context\": str}]}. "
        "Exclude trivial words. Data:\n\n" + text[:6000]
    )
    resp = _generate(prompt, max_tokens=600, temperature=0.1)
    if not resp:
        return []
    parsed = _extract_json(resp)
    if parsed:
        return parsed.get("entities", [])
    return []


def summarize(text: str) -> str:
    if not text.strip():
        return ""
    if _force_simulation():
        return _fallback_summarize(text)
    resp = _generate(
        "Summarize in <= 3 sentences: " + text[:3000],
        max_tokens=180, temperature=0.2,
    )
    if resp:
        return resp.strip()
    return _fallback_summarize(text)


def classify_location(text: str) -> List[str]:
    if not text.strip():
        return []
    if _force_simulation():
        return []
    resp = _generate(
        "From this text return STRICT JSON {\"locations\":[names]}. "
        "Only real place names. Text: " + text[:2000],
        max_tokens=200, temperature=0.1,
    )
    if not resp:
        return []
    parsed = _extract_json(resp)
    if parsed:
        return parsed.get("locations", [])
    return []


# --------------------------------------------------------------- fallback -----
def _build_analysis_prompt(context: Dict[str, Any]) -> str:
    return (
        "You are generating an intelligence report on UPLOADED IMAGE content. "
        "Do NOT accuse anyone. Summarize the following in JSON with keys: "
        "overview, key_entities, key_observations, risk_assessment, "
        "recommendation. "
        f"VISION: {json.dumps(context.get('vision_summary', {}))}\n"
        f"OSINT: {json.dumps(context.get('osint_findings', []))}\n"
        f"ENTITIES: {json.dumps(context.get('entities', []))}\n"
    )


def _normalize_summary(
    parsed: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "overview": str(
            parsed.get("overview") or parsed.get("summary") or ""
        ),
        "key_entities": parsed.get("key_entities") or _entities_from_context(context),
        "key_observations": parsed.get("key_observations")
        or _observations_from_context(context),
        "risk_assessment": str(
            parsed.get("risk_assessment")
            or "INDICATORS ONLY - no autonomous classification performed"
        ),
        "recommendation": str(
            parsed.get("recommendation")
            or "Human analyst review required before any operational use."
        ),
        "confidence": float(
            parsed.get("confidence", _confidence_from_context(context))
        ),
        "verification": "PENDING HUMAN REVIEW",
    }


def _entities_from_context(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for e in context.get("entities", []):
        out.append({"name": e.get("name"), "type": e.get("entity_type"),
                    "confidence": e.get("confidence", 0.0)})
    return out


def _observations_from_context(context: Dict[str, Any]) -> List[str]:
    obs = []
    vs = context.get("vision_summary", {})
    if vs.get("faces", {}).get("detected"):
        obs.append(
            f"Face presence detected ({vs['faces']['count']} person(s)) - "
            "identity NOT confirmed"
        )
    for v in vs.get("vehicles", []):
        obs.append(
            f"Vehicle detected: {v['label']} (conf {v['confidence']:.0%})"
        )
    if vs.get("text", {}).get("found"):
        obs.append(f"Visible text extracted ({len(vs['text']['fragments'])} fragments)")
    if vs.get("plates"):
        obs.append(f"Plate-like text captured: {', '.join(vs['plates'])}")
    if context.get("osint_findings"):
        obs.append(
            f"{len(context['osint_findings'])} public-source references retrieved"
        )
    if not obs:
        obs.append("No strong autonomous indicators - low-evidence image")
    return obs


def _confidence_from_context(context: Dict[str, Any]) -> float:
    score = 0.15
    vs = context.get("vision_summary", {})
    if vs.get("faces", {}).get("detected"):
        score += 0.15
    if vs.get("vehicles"):
        score += 0.15
    if vs.get("text", {}).get("found"):
        score += 0.15
    if vs.get("plates"):
        score += 0.10
    if context.get("osint_findings"):
        score += 0.20
    if vs.get("location", {}).get("geohints"):
        score += 0.10
    return round(min(0.95, score), 3)


def _fallback_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    vs = context.get("vision_summary", {})
    obs = _observations_from_context(context)
    conf = _confidence_from_context(context)

    overview = (
        "Automated image intelligence assessment completed. "
        f"{vs.get('persons', 0)} person(s), {len(vs.get('vehicles', []))} "
        f"vehicle(s), {len(vs.get('objects', []))} object(s) and "
        f"{len(vs.get('text', {}).get('fragments', []))} text fragment(s) "
        "recorded from the uploaded image. "
    )
    if vs.get("location", {}).get("geohints"):
        overview += "Embedded GPS metadata provides a geospatial anchor. "
    overview += (
        "These are EVIDENCE INDICATORS only. SENTINEL does not and cannot "
        "determine the identity, intent or classification of any person "
        "depicted; a human analyst must perform verification."
    )

    return {
        "overview": overview,
        "key_entities": _entities_from_context(context),
        "key_observations": obs,
        "risk_assessment": (
            "NO AUTONOMOUS CLASSIFICATION PERFORMED. Indicator-only output; "
            "elevated evidence density but zero legal or threat conclusions."
        ),
        "recommendation": (
            "Refer to a qualified human analyst. Compare against authorized "
            "databases. Respect privacy laws and data provenance."
        ),
        "confidence": conf,
        "verification": "PENDING HUMAN REVIEW",
    }


def _fallback_summarize(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        if s and len(s) > 30:
            out.append(s)
        if len(out) >= 2:
            break
    return " ".join(out) if out else (text[:240] + "..." if text else "")
