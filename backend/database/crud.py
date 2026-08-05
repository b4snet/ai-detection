"""SENTINEL AI - database persistence helpers."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.core.logging import log, now_iso
from backend.models.entities import (
    ActivityLog,
    Analysis,
    Entity,
    GraphEdge,
    Source,
    TimelineEvent,
)


def create_analysis(
    session: Session, filename: str, image_path: str
) -> Analysis:
    analysis = Analysis(
        filename=filename,
        image_path=image_path,
        status="queued",
        confidence=0.0,
        verification="PENDING HUMAN REVIEW",
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


def persist_full_result(
    session: Session,
    analysis: Analysis,
    result: Dict[str, Any],
) -> Analysis:
    """Write the complete pipeline result back to normalized tables."""
    vision = result.get("vision", {})
    intel = result.get("intelligence", {})
    entities = result.get("entities", [])
    sources = result.get("sources", [])
    timeline = result.get("timeline", [])
    graph = result.get("graph", {})

    analysis.status = result.get("status", "complete")
    analysis.summary = intel.get("overview", "")
    analysis.confidence = float(intel.get("confidence", 0.0))
    analysis.verification = intel.get("verification", "PENDING HUMAN REVIEW")
    analysis.image_metadata = {
        "width": vision.get("width"),
        "height": vision.get("height"),
        "format": vision.get("format"),
        "camera_make": vision.get("camera_make"),
        "camera_model": vision.get("camera_model"),
        "taken_at": vision.get("taken_at"),
        "gps": vision.get("gps", {}),
    }
    analysis.vision_result = vision
    analysis.intelligence_result = intel
    analysis.report_path = result.get("report_path", "")

    # Entities
    for e in entities:
        ent = Entity(
            analysis_id=analysis.id,
            name=e.get("name", ""),
            entity_type=e.get("entity_type", "entity"),
            confidence=float(e.get("confidence", 0.0)),
            description=e.get("description", ""),
            public_mentions=int(e.get("public_mentions", 0)),
            verification=e.get("verification", "PENDING HUMAN REVIEW"),
            aliases=e.get("aliases", []),
            attributes={},
            timeline=e.get("timeline", []),
            risk_indicators=e.get("risk_indicators", []),
        )
        session.add(ent)
        session.flush()
        for src in e.get("associated_sources", []):
            session.add(Source(
                analysis_id=analysis.id,
                entity_id=ent.id,
                title=src.get("title", ""),
                url=src.get("url", ""),
                source_type=src.get("source_type", "reference"),
                published_at=src.get("published_at", ""),
                snippet="",
                verified="UNVERIFIED",
                relevance=float(src.get("relevance", 0.0)),
            ))

    # Global sources
    for s in sources:
        session.add(Source(
            analysis_id=analysis.id,
            title=s.get("title", ""),
            url=s.get("url", ""),
            source_type=s.get("source_type", "reference"),
            published_at=s.get("published_at", ""),
            snippet=s.get("snippet", ""),
            verified=s.get("verified", "UNVERIFIED"),
            relevance=float(s.get("relevance", 0.0)),
        ))

    # Timeline
    for t in timeline:
        session.add(TimelineEvent(
            analysis_id=analysis.id,
            date=t.get("date", ""),
            title=t.get("title", ""),
            event_type=t.get("event_type", "reference"),
            detail=t.get("detail", ""),
        ))

    # Graph edges
    for edge in graph.get("edges", []):
        session.add(GraphEdge(
            analysis_id=analysis.id,
            source=edge.get("source", ""),
            target=edge.get("target", ""),
            relation=edge.get("relation", "related"),
            weight=float(edge.get("weight", 1.0)),
        ))

    session.commit()
    session.refresh(analysis)
    log("info", f"Analysis {analysis.id} persisted to database")
    return analysis


def get_analysis_row(session: Session, analysis_id: int) -> Optional[Analysis]:
    return session.get(Analysis, analysis_id)


def list_analyses(session: Session, limit: int = 50) -> List[Analysis]:
    return (
        session.query(Analysis)
        .order_by(Analysis.id.desc())
        .limit(limit)
        .all()
    )


def write_log_row(session: Session, message: str, level: str = "INFO",
                  analysis_id: Optional[int] = None) -> None:
    session.add(ActivityLog(
        timestamp=now_iso(), level=level.upper(), message=message,
        analysis_id=analysis_id,
    ))
    session.commit()


def recent_logs(session: Session, limit: int = 80) -> List[ActivityLog]:
    return (
        session.query(ActivityLog)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
        .all()
    )
