"""SENTINEL AI - system status + capability endpoints."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.session import get_db
from backend.intelligence import llm
from backend.models.schemas import SystemStatus
from backend.vision.detector import vision_stack

router = APIRouter(prefix="/api", tags=["status"])

_START = time.time()


@router.get("/status", response_model=SystemStatus)
def get_status(db: Session = Depends(get_db)) -> SystemStatus:
    from backend.models.entities import Analysis, Entity

    analyses = db.query(func.count(Analysis.id)).scalar() or 0
    entities = db.query(func.count(Entity.id)).scalar() or 0
    online = llm.ollama_online()

    return SystemStatus(
        status="ONLINE",
        ai_engine="ACTIVE" if online else "DEGRADED",
        ai_mode=llm.ai_mode(),
        data_connection="CONNECTED",
        ollama_online=online,
        model=settings.ollama_model if online else "deterministic fallback engine",
        vision_stack=", ".join(vision_stack()),
        last_update=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        analyses_count=int(analyses),
        entities_count=int(entities),
        uptime_seconds=int(time.time() - _START),
    )


@router.get("/capabilities")
def capabilities():
    return {
        "ollama_online": llm.ollama_online(),
        "ollama_host": settings.ollama_host,
        "models": llm.available_models(),
        "vision_stack": vision_stack(),
        "simulation_mode": settings.simulation_mode,
    }
