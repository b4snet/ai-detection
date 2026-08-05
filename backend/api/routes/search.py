"""SENTINEL AI - entity / event / location search endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import or_

from backend.database.session import get_db
from backend.intelligence import osint as osint_mod

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/osint")
def search_osint(q: str = Query(..., min_length=2), limit: int = 10):
    """Search public sources for an entity, event or location."""
    findings = osint_mod.search_all(q, limit=limit)
    timeline = osint_mod.enrich_timeline(q, limit=6)
    return {"query": q, "results": findings, "timeline": timeline}


@router.get("/entities")
def search_entities(q: str = Query(..., min_length=2)):
    """Search previously analyzed entities in the local store."""
    from sqlalchemy import func

    from backend.database.session import get_session_factory
    from backend.models.entities import Entity

    with get_session_factory()() as session:
        rows = (
            session.query(Entity)
            .filter(
                or_(
                    Entity.name.ilike(f"%{q}%"),
                    Entity.entity_type.ilike(f"%{q}%"),
                )
            )
            .order_by(func.count(Entity.id).desc())
            .limit(25)
            .all()
        )
        return {
            "query": q,
            "results": [
                {
                    "id": e.id,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "confidence": e.confidence or 0.0,
                    "public_mentions": e.public_mentions or 0,
                    "verification": e.verification or "PENDING HUMAN REVIEW",
                }
                for e in rows
            ],
        }
