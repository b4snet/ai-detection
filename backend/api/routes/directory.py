"""Authorized Nepal directory enrollment and matching endpoints."""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.intelligence.directory_matcher import enroll_profile, load_profiles, match_authorized, save_upload

router = APIRouter(prefix="/api/directory", tags=["authorized-directory"])


@router.get("/profiles")
def profiles():
    return {"profiles": load_profiles()}


@router.post("/enroll")
async def enroll(
    image: UploadFile = File(...),
    name: str = Form(...),
    city: str = Form(""),
    district: str = Form(""),
    province: str = Form(""),
    facebook: str = Form(""),
    instagram: str = Form(""),
    linkedin: str = Form(""),
    website: str = Form(""),
    notes: str = Form(""),
):
    try:
        row = enroll_profile(
            {
                "name": name,
                "city": city,
                "district": district,
                "province": province,
                "notes": notes,
                "public_socials": {
                    "facebook": facebook,
                    "instagram": instagram,
                    "linkedin": linkedin,
                    "website": website,
                },
            },
            await image.read(),
            image.filename or "reference.jpg",
        )
        return {"profile": row}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/match")
async def match_directory(file: UploadFile = File(...)):
    try:
        content = await file.read()
        stored = save_upload(content, file.filename or "upload.jpg")
        return match_authorized(stored)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
