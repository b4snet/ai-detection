"""SENTINEL AI - Pydantic API schemas.

These define the exact JSON contract between backend and frontend.
Every intelligence payload carries: confidence, sources, timestamp,
verification status, and a human-review flag.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------- status ----
class SystemStatus(BaseModel):
    system: str = "SENTINEL AI"
    status: str = "ONLINE"
    ai_engine: str = "ACTIVE"
    ai_mode: str = "local"  # local | degraded | simulation
    data_connection: str = "CONNECTED"
    ollama_online: bool = False
    model: str = ""
    vision_stack: str = ""
    last_update: str = ""
    analyses_count: int = 0
    entities_count: int = 0
    uptime_seconds: int = 0


class LogEntry(BaseModel):
    id: int
    timestamp: str
    level: str
    message: str
    analysis_id: Optional[int] = None


# ---------------------------------------------------------------- vision -----
class DetectedObject(BaseModel):
    label: str
    confidence: float
    bbox: List[int] = Field(default_factory=list)


class FaceInfo(BaseModel):
    detected: bool = False
    count: int = 0
    confidence: float = 0.0


class TextInfo(BaseModel):
    found: bool = False
    fragments: List[str] = Field(default_factory=list)


class LocationClue(BaseModel):
    found: bool = False
    clues: List[str] = Field(default_factory=list)
    geohints: List[str] = Field(default_factory=list)


class VisionAnalysis(BaseModel):
    timestamp: str = ""
    width: int = 0
    height: int = 0
    format: str = ""
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    taken_at: Optional[str] = None
    gps: Optional[Dict[str, float]] = None
    faces: FaceInfo = Field(default_factory=FaceInfo)
    persons: int = 0
    objects: List[DetectedObject] = Field(default_factory=list)
    vehicles: List[DetectedObject] = Field(default_factory=list)
    text: TextInfo = Field(default_factory=TextInfo)
    location: LocationClue = Field(default_factory=LocationClue)
    colors: List[str] = Field(default_factory=list)
    scene: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


# ----------------------------------------------------------- intelligence ----
class OSINTFinding(BaseModel):
    title: str
    source: str
    url: str
    source_type: str
    published_at: str
    snippet: str
    relevance: float
    verified: str = "UNVERIFIED"


class TimelineItem(BaseModel):
    date: str
    title: str
    event_type: str
    detail: str = ""


class EntityProfile(BaseModel):
    id: Optional[int] = None
    name: str
    entity_type: str
    confidence: float
    description: str = ""
    aliases: List[str] = Field(default_factory=list)
    public_mentions: int = 0
    verification: str = "PENDING HUMAN REVIEW"
    associated_sources: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[TimelineItem] = Field(default_factory=list)
    risk_indicators: List[Dict[str, Any]] = Field(default_factory=list)


# --------------------------------------------------------------- graph -------
class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    size: float = 1.0


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0


class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


# -------------------------------------------------------------- report -------
class ReportSummary(BaseModel):
    overview: str
    key_entities: List[Dict[str, Any]] = Field(default_factory=list)
    key_observations: List[str] = Field(default_factory=list)
    risk_assessment: str = "NO AUTONOMOUS CLASSIFICATION PERFORMED"
    recommendation: str = ""
    confidence: float = 0.0
    verification: str = "PENDING HUMAN REVIEW"


# ---------------------------------------------------------------- analysis ---
class AnalysisResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: str
    timestamp: str
    confidence: float
    verification: str
    summary: str
    image_metadata: Dict[str, Any] = Field(default_factory=dict)
    vision: VisionAnalysis = Field(default_factory=VisionAnalysis)
    intelligence: ReportSummary = Field(default_factory=ReportSummary)
    entities: List[EntityProfile] = Field(default_factory=list)
    sources: List[OSINTFinding] = Field(default_factory=list)
    timeline: List[TimelineItem] = Field(default_factory=list)
    graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    report_path: str = ""
    processing_log: List[str] = Field(default_factory=list)


class AnalysisListEntry(BaseModel):
    id: int
    filename: str
    status: str
    created_at: str
    confidence: float
    summary: str
    verification: str


class SearchResult(BaseModel):
    query: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
