"""SENTINEL AI - report download endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import crud
from backend.database.session import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{analysis_id}/pdf")
def download_pdf(analysis_id: int, db: Session = Depends(get_db)):
    analysis = crud.get_analysis_row(db, analysis_id)
    if analysis is None:
        raise HTTPException(404, "Analysis not found")
    if not analysis.report_path:
        raise HTTPException(404, "Report not generated yet")
    path = Path(analysis.report_path)
    if not path.exists():
        raise HTTPException(404, "Report file missing on disk")
    return FileResponse(
        str(path),
        media_type="application/pdf",
        filename=f"sentinel_report_{analysis_id}.pdf",
    )


@router.get("/{analysis_id}/json")
def download_json(analysis_id: int, db: Session = Depends(get_db)):
    analysis = crud.get_analysis_row(db, analysis_id)
    if analysis is None:
        raise HTTPException(404, "Analysis not found")
    path = settings.reports / f"sentinel_report_{analysis_id}.json"
    if not path.exists():
        raise HTTPException(404, "JSON snapshot not generated yet")
    return FileResponse(
        str(path),
        media_type="application/json",
        filename=f"sentinel_report_{analysis_id}.json",
    )
