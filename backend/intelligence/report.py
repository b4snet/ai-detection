"""SENTINEL AI - intelligence report generator.

Produces a downloadable PDF (reportlab) plus a JSON snapshot of every
analysis. Both are stamped with confidence, sources, timestamps,
verification status and a human-review notice.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.config import settings
from backend.core.logging import log

_GREEN = colors.HexColor("#00ff88")
_DARK = colors.HexColor("#0a0f0a")
_GREY = colors.HexColor("#22aa66")
_RED = colors.HexColor("#ff3355")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("H1", parent=s["Heading1"], textColor=_GREEN,
                         fontSize=20, spaceAfter=6))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=_GREEN,
                         fontSize=13, spaceBefore=10, spaceAfter=4))
    s.add(ParagraphStyle("Small", parent=s["BodyText"], fontSize=8,
                         textColor=_GREY))
    s.add(ParagraphStyle("Red", parent=s["BodyText"], fontSize=9,
                         textColor=_RED))
    return s


def generate_pdf(analysis: Dict[str, Any], analysis_id: int) -> str:
    """Write reports/sentinel_report_{id}.pdf and return its path."""
    styles = _styles()
    out_path = settings.reports / f"sentinel_report_{analysis_id}.pdf"

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"SENTINEL AI Report {analysis_id}",
    )
    story: list = []

    story.append(Paragraph("SENTINEL AI", styles["H1"]))
    story.append(Paragraph("INTELLIGENCE ASSESSMENT REPORT", styles["H2"]))
    story.append(Paragraph(
        f"Report ID: {analysis_id}  |  Generated: "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles["Small"],
    ))
    story.append(HRFlowable(color=_GREEN, thickness=1.5))
    story.append(Paragraph(
        "CLASSIFICATION: UNCLASSIFIED // DEMONSTRATION PURPOSES ONLY", styles["Red"],
    ))
    story.append(Paragraph(
        "LEGAL NOTICE: This report is an intelligence ASSISTANCE artifact. "
        "SENTINEL AI performs no autonomous identification, accusation or "
        "classification of any person. Every finding requires human analyst "
        "review before operational use.", styles["BodyText"],
    ))
    story.append(Spacer(1, 6))

    # Summary block
    story.append(Paragraph("1. EXECUTIVE SUMMARY", styles["H2"]))
    intel = analysis.get("intelligence", {})
    story.append(Paragraph(intel.get("overview") or "No summary.", styles["BodyText"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        f"Overall Confidence: {intel.get('confidence', 0):.0%}   |   "
        f"Verification: {intel.get('verification', 'PENDING HUMAN REVIEW')}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        "Risk assessment: " + (intel.get("risk_assessment") or "None"), styles["BodyText"],
    ))
    story.append(Paragraph(
        "Recommendation: " + (intel.get("recommendation") or "Human review."),
        styles["BodyText"],
    ))
    story.append(Spacer(1, 6))

    # Vision section
    story.append(Paragraph("2. VISUAL INTELLIGENCE", styles["H2"]))
    vision = analysis.get("vision", {})
    vision_rows = [
        ["Property", "Value"],
        ["Dimensions", f"{vision.get('width', 0)} x {vision.get('height', 0)} px"],
        ["Format", str(vision.get("format", ""))],
        ["Faces detected", f"{vision.get('faces', {}).get('count', 0)}"],
        ["Persons", f"{vision.get('persons', 0)}"],
        ["Vehicles", str(len(vision.get("vehicles", [])))],
        ["Objects", str(len(vision.get("objects", [])))],
        ["Text found", "YES" if vision.get("text", {}).get("found") else "NO"],
        ["Location clues",
         "YES" if vision.get("location", {}).get("found") else "NO"],
        ["GPS embedded", "YES" if vision.get("gps") else "NO"],
    ]
    t = Table(vision_rows, colWidths=[60 * mm, 105 * mm])
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, _GREEN),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

    text = vision.get("text", {})
    if text.get("found"):
        story.append(Paragraph("Extracted text fragments:", styles["BodyText"]))
        for frag in text.get("fragments", [])[:12]:
            story.append(Paragraph("&bull; " + frag, styles["Small"]))
    story.append(PageBreak())

    # Entities section
    story.append(Paragraph("3. ENTITY PROFILES", styles["H2"]))
    entities = analysis.get("entities", [])
    if not entities:
        story.append(Paragraph("No named entities extracted.", styles["BodyText"]))
    for e in entities:
        story.append(Paragraph(
            f"{e.get('name', '?')} "
            f"[{e.get('entity_type', 'entity')}] - conf {e.get('confidence', 0):.0%}",
            styles["BodyText"],
        ))
        story.append(Paragraph("Verification: " + e.get("verification", ""), styles["Small"]))
        if e.get("description"):
            story.append(Paragraph(e["description"], styles["Small"]))
        story.append(Spacer(1, 4))

    # Sources
    story.append(Paragraph("4. SOURCES & REFERENCES", styles["H2"]))
    sources = analysis.get("sources", [])
    if not sources:
        story.append(Paragraph("No public sources returned.", styles["BodyText"]))
    for s in sources:
        story.append(Paragraph(
            f"&bull; {s.get('title', '')} "
            f"({s.get('source_type', '')}, rel {s.get('relevance', 0):.0%})",
            styles["BodyText"],
        ))
        story.append(Paragraph(
            f"     URL: {s.get('url', '')}  |  {s.get('published_at', 'n/d')}",
            styles["Small"],
        ))

    # Timeline
    story.append(Paragraph("5. TIMELINE", styles["H2"]))
    for ev in analysis.get("timeline", []):
        story.append(Paragraph(
            f"&bull; [{ev.get('date', '')}] {ev.get('title', '')}",
            styles["BodyText"],
        ))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(color=_GREEN, thickness=1))
    story.append(Paragraph(
        "END OF REPORT - SENTINEL AI (responsible intelligence assistant)",
        styles["Small"],
    ))

    doc.build(story)
    log("info", f"PDF report generated: {out_path.name}")
    return str(out_path)


def export_json(analysis: Dict[str, Any], analysis_id: int) -> str:
    path = settings.reports / f"sentinel_report_{analysis_id}.json"
    path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)
