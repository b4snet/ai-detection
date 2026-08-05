"""SENTINEL AI - full intelligence pipeline.

    IMAGE INPUT -> Vision -> Entity Recognition -> OSINT Retrieval
    -> Knowledge Graph -> AI Analysis -> Dashboard payload

Run inside a background thread so the API responds instantly and the
frontend can stream progress via the activity log.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.core.logging import log
from backend.intelligence import graph as graph_mod
from backend.intelligence import llm, osint as osint_mod
from backend.intelligence.entity_extractor import extract_profiles
from backend.intelligence.report import export_json, generate_pdf
from backend.vision.analyzer import analyze_image


def run_pipeline(
    analysis_id: int, image_path: str, filename: str,
    search_terms: List[str] | None = None,
) -> Dict[str, Any]:
    """Execute the complete pipeline and return an AnalysisResponse dict."""
    log("info", f"=== PIPELINE START analysis={analysis_id} file={filename} ===",
        analysis_id)
    terms = search_terms or _default_terms(filename)

    # 1) COMPUTER VISION
    log("info", "STAGE 1/6 Computer vision processing...", analysis_id)
    vision = analyze_image(image_path)

    # 2) ENTITY RECOGNITION
    log("info", "STAGE 2/6 Entity recognition...", analysis_id)
    top_query = _top_query(terms, vision)
    entities = extract_profiles(vision, terms, top_query)

    # 3) OSINT RETRIEVAL
    log("info", f"STAGE 3/6 OSINT retrieval (query='{top_query}')...", analysis_id)
    sources = osint_mod.search_all(top_query, limit=8)
    timeline = osint_mod.enrich_timeline(top_query, limit=6)

    # 4) KNOWLEDGE GRAPH
    log("info", "STAGE 4/6 Knowledge graph construction...", analysis_id)
    graph = graph_mod.build_graph(entities, sources, timeline, analysis_id)

    # 5) AI ANALYSIS
    log("info", "STAGE 5/6 AI report generation...", analysis_id)
    context = {
        "vision_summary": vision,
        "osint_findings": sources,
        "entities": [
            {"name": e["name"], "entity_type": e["entity_type"],
             "confidence": e["confidence"]}
            for e in entities
        ],
    }
    intelligence = llm.analyze_findings(context)

    # 6) REPORT EXPORT
    log("info", "STAGE 6/6 Exporting intelligence report...", analysis_id)
    result = {
        "id": analysis_id,
        "filename": filename,
        "status": "complete",
        "created_at": vision.get("timestamp", ""),
        "timestamp": vision.get("timestamp", ""),
        "confidence": intelligence.get("confidence", 0.0),
        "verification": intelligence.get("verification", "PENDING HUMAN REVIEW"),
        "summary": intelligence.get("overview", ""),
        "image_metadata": {
            "width": vision.get("width"),
            "height": vision.get("height"),
            "format": vision.get("format"),
            "camera_make": vision.get("camera_make"),
            "camera_model": vision.get("camera_model"),
            "taken_at": vision.get("taken_at"),
            "gps": vision.get("gps", {}),
        },
        "vision": vision,
        "intelligence": intelligence,
        "entities": entities,
        "sources": sources,
        "timeline": timeline,
        "graph": graph,
        "report_path": "",
        "processing_log": [],
    }
    report_path = generate_pdf(result, analysis_id)
    json_path = export_json(result, analysis_id)
    result["report_path"] = report_path

    log("info",
        f"=== PIPELINE COMPLETE analysis={analysis_id} "
        f"confidence={intelligence['confidence']:.0%} "
        f"entities={len(entities)} sources={len(sources)} ===",
        analysis_id)
    return result


# ------------------------------------------------------------------ helpers ---
def _default_terms(filename: str) -> List[str]:
    import re

    stem = re.sub(r"\.[^.]+$", "", filename or "")
    words = re.findall(r"[A-Za-z]{3,}", stem.replace("_", " "))
    return words[:3] or ["image", "evidence"]


def _top_query(terms: List[str], vision: Dict[str, Any] | None = None) -> str:
    # Prefer an entity-looking phrase from visible OCR text.
    if vision:
        import re

        for frag in vision.get("text", {}).get("fragments", []):
            m = re.search(r"\b([A-Z][A-Z0-9]{3,}(?:\s[A-Z0-9]{2,}){0,3})\b", frag)
            if m:
                word = m.group(1)
                if re.search(r"[A-Z]{3,}", word):
                    return word.replace(" ", " ")
    for t in terms:
        if len(t) >= 4:
            return t
    return terms[0] if terms else "image analysis"
