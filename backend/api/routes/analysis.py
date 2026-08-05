"""SENTINEL AI - analysis endpoints (upload, run, fetch, list).

Upload is async: returns immediately with an analysis id, then the
pipeline runs in a background thread. The frontend polls
GET /api/analysis/{id} and reads the live activity log.
"""
from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from backend.config import settings
from backend.core.logging import log
from backend.database import crud
from backend.database.session import get_db
from backend.intelligence.analyzer import run_pipeline
from backend.models.schemas import AnalysisListEntry

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def _validate_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not _validate_image(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use jpg/png/webp/bmp/tiff.",
        )

    # Save file safely
    ext = Path(file.filename).suffix.lower()
    stored_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
    dest = settings.uploads / stored_name
    with dest.open("wb") as fh:
        while chunk := await file.read(1024 * 1024):
            fh.write(chunk)

    analysis = crud.create_analysis(db, file.filename or stored_name, str(dest))
    log("info", f"IMAGE UPLOADED: {file.filename} -> analysis {analysis.id}",
        analysis.id)

    # Async processing with a thread (BackgroundTasks runs after response
    # only in some servers; a dedicated thread is deterministic).
    t = threading.Thread(
        target=_process, args=(analysis.id, str(dest), file.filename or stored_name),
        daemon=True,
    )
    t.start()

    return {"id": analysis.id, "status": "queued", "filename": file.filename}


def _process(analysis_id: int, image_path: str, filename: str) -> None:
    from backend.database.session import get_session_factory

    factory = get_session_factory()
    with factory() as session:
        analysis = crud.get_analysis_row(session, analysis_id)
        if analysis is None:
            return
        analysis.status = "processing"
        session.commit()

        try:
            result = run_pipeline(analysis_id, image_path, filename)
            crud.persist_full_result(session, analysis, result)
        except Exception as exc:  # pipeline must never crash the server
            log("error", f"Pipeline failed for {analysis_id}: {exc}", analysis_id)
            analysis.status = "error"
            session.commit()


@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int, db: Session = Depends(get_db)
) -> dict:
    analysis = crud.get_analysis_row(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    from backend.api.deps import analysis_to_response

    payload = analysis_to_response(analysis)
    # Rebuild graph nodes from stored edges + entity rows.
    from backend.intelligence.graph import _safe_id

    entities = payload["entities"]
    edges = payload["graph"]["edges"]
    nodes = [
        {
            "id": _safe_id(e["name"], "E"),
            "label": e["name"],
            "node_type": e["entity_type"],
            "size": 1.0 + 0.6 * float(e["confidence"]),
            "date": "",
        }
        for e in entities
    ]
    node_ids = {n["id"] for n in nodes}
    for ed in edges:
        if ed["source"] not in node_ids:
            nodes.append({
                "id": ed["source"], "label": _label_from_id(ed["source"]),
                "node_type": "source", "size": 1.0, "date": "",
            })
            node_ids.add(ed["source"])
        if ed["target"] not in node_ids:
            nodes.append({
                "id": ed["target"], "label": _label_from_id(ed["target"]),
                "node_type": "event", "size": 1.0, "date": "",
            })
            node_ids.add(ed["target"])
    payload["graph"]["nodes"] = nodes
    return payload


def _label_from_id(nid: str, n: int = 40) -> str:
    """Reconstruct a readable label from a stored safe-id."""
    import re

    rest = nid
    if "_" in rest:
        rest = rest.split("_", 1)[1]
    rest = re.sub(r"_\d+$", "", rest)
    label = rest.replace("_", " ").strip()
    if len(label) > n:
        label = label[: n - 1] + "…"
    return label or nid


@router.get("/", response_model=List[AnalysisListEntry])
def list_analyses(db: Session = Depends(get_db)):
    rows = crud.list_analyses(db, limit=50)
    return [
        {
            "id": a.id,
            "filename": a.filename or "",
            "status": a.status or "",
            "created_at": a.created_at.isoformat() if a.created_at else "",
            "confidence": a.confidence or 0.0,
            "summary": (a.summary or "")[:180],
            "verification": a.verification or "PENDING HUMAN REVIEW",
        }
        for a in rows
    ]
