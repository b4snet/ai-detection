"""SENTINEL AI - shared API dependencies."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from backend.core.logging import now_iso
from backend.database.session import get_db  # re-export


def analysis_to_response(analysis: Any) -> Dict[str, Any]:
    """Convert an ORM Analysis + relations into the AnalysisResponse dict."""
    vision = analysis.vision_result or {}
    intel = analysis.intelligence_result or {}

    entities = [
        {
            "id": e.id,
            "name": e.name,
            "entity_type": e.entity_type,
            "confidence": e.confidence or 0.0,
            "description": e.description or "",
            "aliases": e.aliases or [],
            "public_mentions": e.public_mentions or 0,
            "verification": e.verification or "PENDING HUMAN REVIEW",
            "associated_sources": [
                {
                    "title": s.title,
                    "url": s.url,
                    "source": s.source_type,
                    "source_type": s.source_type,
                    "published_at": s.published_at,
                    "relevance": s.relevance or 0.0,
                }
                for s in analysis.sources if s.entity_id == e.id
            ],
            "timeline": e.timeline or [],
            "risk_indicators": e.risk_indicators or [],
        }
        for e in analysis.entities
    ]

    sources = [
        {
            "title": s.title,
            "source": s.source_type,
            "url": s.url,
            "source_type": s.source_type,
            "published_at": s.published_at,
            "snippet": s.snippet or "",
            "relevance": s.relevance or 0.0,
            "verified": s.verified or "UNVERIFIED",
        }
        for s in analysis.sources if s.entity_id is None
    ]

    timeline = [
        {
            "date": t.date,
            "title": t.title,
            "event_type": t.event_type,
            "detail": t.detail or "",
        }
        for t in analysis.timeline
    ]

    edges = [
        {
            "source": e.source,
            "target": e.target,
            "relation": e.relation,
            "weight": e.weight or 1.0,
        }
        for e in analysis.graph_edges
    ] if hasattr(analysis, "graph_edges") else []

    return {
        "id": analysis.id,
        "filename": analysis.filename or "",
        "image_url": f"/uploads/{Path(analysis.image_path).name}"
        if analysis.image_path else "",
        "status": analysis.status or "complete",
        "created_at": analysis.created_at.isoformat() if analysis.created_at else now_iso(),
        "timestamp": vision.get("timestamp") or now_iso(),
        "confidence": analysis.confidence or 0.0,
        "verification": analysis.verification or "PENDING HUMAN REVIEW",
        "summary": analysis.summary or "",
        "image_metadata": analysis.image_metadata or {},
        "vision": vision,
        "intelligence": {
            "overview": intel.get("overview", ""),
            "key_entities": intel.get("key_entities", []),
            "key_observations": intel.get("key_observations", []),
            "risk_assessment": intel.get("risk_assessment", ""),
            "recommendation": intel.get("recommendation", ""),
            "confidence": intel.get("confidence", analysis.confidence or 0.0),
            "verification": intel.get("verification", "PENDING HUMAN REVIEW"),
        },
        "entities": entities,
        "sources": sources,
        "timeline": timeline,
        "graph": {"nodes": [], "edges": edges},
        "report_path": analysis.report_path or "",
        "processing_log": [],
    }
