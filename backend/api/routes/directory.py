"""Authorized Nepal directory image matching endpoint."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.intelligence.directory_matcher import match_authorized, save_upload

router = APIRouter(prefix="/api/directory", tags=["authorized-directory"])


@router.post("/match")
async def match_directory(file: UploadFile = File(...)):
    try:
        content = await file.read()
        stored = save_upload(content, file.filename or "upload.jpg")
        return match_authorized(stored)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
