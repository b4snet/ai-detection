"""SENTINEL AI - FastAPI application entry point.

Run:  uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.core.logging import log
from backend.database.session import create_tables
from backend.models.entities import Base, GraphEdge  # noqa: F401  (register models)

from backend.api.routes import analysis, directory, footprint, logs, reports, search, status

app = FastAPI(
    title="SENTINEL AI",
    description=(
        "AI-powered Open Source Intelligence & Threat Analysis Platform. "
        "Responsible intelligence assistance - no autonomous classification."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(status.router)
app.include_router(analysis.router)
app.include_router(directory.router)
app.include_router(search.router)
app.include_router(footprint.router)
app.include_router(logs.router)
app.include_router(reports.router)

# Serve uploaded images for the frontend thumbnail view.
app.mount("/uploads", StaticFiles(directory=str(settings.uploads)), name="uploads")


@app.on_event("startup")
def _startup() -> None:
    create_tables()
    log("info", "SENTINEL AI backend online")
    log("info", f"Database: {settings.database_url}")
    log("info", f"Upload dir: {settings.uploads}")


@app.get("/")
def root():
    return {
        "system": "SENTINEL AI",
        "message": "Intelligence Operations Center API is online.",
        "docs": "/docs",
        "health": "/api/status",
    }
