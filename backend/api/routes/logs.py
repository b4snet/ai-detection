"""SENTINEL AI - activity log endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.session import get_db
from backend.models.schemas import LogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/", response_model=list[LogEntry])
def get_logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = crud.recent_logs(db, limit=limit)
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "level": r.level,
            "message": r.message,
            "analysis_id": r.analysis_id,
        }
        for r in rows
    ]
