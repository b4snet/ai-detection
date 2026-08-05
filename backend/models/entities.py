"""SENTINEL AI - SQLAlchemy ORM models.

Persistent stores:
  * analyses      - one row per uploaded image / analysis job
  * entities      - recognized persons / vehicles / orgs / locations
  * sources       - OSINT articles & public references
  * timeline_events - dated events extracted during analysis
  * graph_edges   - knowledge-graph relationships
  * activity_logs - terminal-style system log
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    filename = Column(String(512))
    image_path = Column(String(1024))
    created_at = Column(DateTime, default=_utcnow)
    status = Column(String(32), default="queued")  # queued|processing|complete|error
    summary = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    verification = Column(String(64), default="PENDING HUMAN REVIEW")
    image_metadata = Column(JSON, default=dict)
    vision_result = Column(JSON, default=dict)
    intelligence_result = Column(JSON, default=dict)
    report_path = Column(String(1024), default="")

    entities = relationship(
        "Entity", back_populates="analysis", cascade="all, delete-orphan"
    )
    sources = relationship(
        "Source", back_populates="analysis", cascade="all, delete-orphan"
    )
    timeline = relationship(
        "TimelineEvent", back_populates="analysis", cascade="all, delete-orphan"
    )
    graph_edges = relationship(
        "GraphEdge", back_populates="analysis", cascade="all, delete-orphan"
    )


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    name = Column(String(512), index=True)
    entity_type = Column(String(64))  # person|vehicle|organization|location|object
    confidence = Column(Float, default=0.0)
    description = Column(Text, default="")
    public_mentions = Column(Integer, default=0)
    verification = Column(String(64), default="PENDING HUMAN REVIEW")
    aliases = Column(JSON, default=list)
    attributes = Column(JSON, default=dict)
    timeline = Column(JSON, default=list)
    risk_indicators = Column(JSON, default=list)
    created_at = Column(DateTime, default=_utcnow)

    analysis = relationship("Analysis", back_populates="entities")
    sources = relationship("Source", back_populates="entity")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    title = Column(String(1024))
    url = Column(String(2048))
    source_type = Column(String(64))  # news|government|academic|public_db|social
    published_at = Column(String(64), default="")
    snippet = Column(Text, default="")
    verified = Column(String(64), default="UNVERIFIED")
    relevance = Column(Float, default=0.0)

    analysis = relationship("Analysis", back_populates="sources")
    entity = relationship("Entity", back_populates="sources")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    date = Column(String(32))
    title = Column(String(512))
    event_type = Column(String(64))
    detail = Column(Text, default="")

    analysis = relationship("Analysis", back_populates="timeline")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    source = Column(String(512))
    target = Column(String(512))
    relation = Column(String(128))
    weight = Column(Float, default=1.0)

    analysis = relationship("Analysis", back_populates="graph_edges")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String(64))
    level = Column(String(16))
    message = Column(String(2048))
    analysis_id = Column(Integer, nullable=True, index=True)
