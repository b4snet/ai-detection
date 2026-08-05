"""Consent-based digital footprint audit endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.intelligence.footprint import run_audit

router = APIRouter(prefix="/api/footprint", tags=["digital-footprint"])


class FootprintRequest(BaseModel):
    name: Optional[str] = Field(default="", max_length=160)
    email: Optional[str] = Field(default="", max_length=160)
    username: Optional[str] = Field(default="", max_length=80)
    domain: Optional[str] = Field(default="", max_length=120)
    known_location: Optional[str] = Field(default="", max_length=120)
    purpose: str = Field(..., min_length=8, max_length=300)
    consent: bool = False


@router.post("/audit")
def footprint_audit(payload: FootprintRequest):
    supplied = [payload.name, payload.email, payload.username, payload.domain]
    if not any(str(v or "").strip() for v in supplied):
        raise HTTPException(status_code=400, detail="Provide at least one identifier: name, email, username, or domain.")
    try:
        return run_audit(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
