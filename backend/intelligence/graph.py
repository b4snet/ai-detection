"""SENTINEL AI - knowledge graph (NetworkX) + serialization.

Builds a relationship graph:
    ENTITY A --mentioned in--> SOURCE ARTICLE --reports--> EVENT
    ENTITY A --connected through--> ENTITY B

Exported as JSON nodes/edges for the Three.js / canvas frontend viz.
NetworkX keeps this dependency-free vs Neo4j (Neo4j optional).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import networkx as nx

from backend.core.logging import log


def build_graph(
    entities: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    timeline: List[Dict[str, Any]],
    analysis_id: int | str,
) -> Dict[str, Any]:
    """Return {nodes, edges} JSON-safe graph payload."""
    G = nx.Graph()

    # Entity nodes
    for ent in entities:
        eid = _safe_id(ent.get("name", "entity"), "E")
        G.add_node(
            eid,
            label=ent.get("name", "?"),
            node_type=ent.get("entity_type", "entity"),
            confidence=ent.get("confidence", 0.5),
        )
        for src in ent.get("associated_sources", []):
            sid = _safe_id(src.get("title", src.get("url", "source")), "S")
            G.add_node(sid, label=_short(src.get("title", "Source")),
                       node_type="source")
            G.add_edge(
                eid, sid, relation="mentioned in",
                weight=float(src.get("relevance", 0.5)),
            )

    # Source -> event links
    for ev in timeline:
        vid = _safe_id(ev.get("title", "event"), "V")
        G.add_node(vid, label=_short(ev.get("title", "Event")),
                   node_type="event", date=ev.get("date", ""))
        for src in sources:
            sid = _safe_id(src.get("title", src.get("url", "source")), "S")
            if G.has_node(sid):
                G.add_edge(
                    sid, vid, relation="reports",
                    weight=float(src.get("relevance", 0.5)),
                )

    # Cross-entity co-occurrence links
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            ei = entities[i].get("associated_sources", [])
            ej = entities[j].get("associated_sources", [])
            shared = {s.get("url") for s in ei} & {s.get("url") for s in ej}
            if shared:
                a = _safe_id(entities[i].get("name", "E"), "E")
                b = _safe_id(entities[j].get("name", "E"), "E")
                if G.has_node(a) and G.has_node(b):
                    G.add_edge(a, b, relation="connected through shared source",
                               weight=0.9)

    # If graph too small, add the analysis hub node for a nicer render.
    if G.number_of_nodes() >= 2:
        hub = f"A{analysis_id}"
        G.add_node(hub, label="IMAGE ANALYSIS", node_type="analysis")
        for node in list(G.nodes):
            if node != hub and G.nodes[node].get("node_type") == "entity":
                G.add_edge(hub, node, relation="identified in", weight=1.0)

    nodes = [
        {
            "id": n,
            "label": str(G.nodes[n].get("label", n)),
            "node_type": G.nodes[n].get("node_type", "entity"),
            "size": 1.0 + 0.6 * float(G.nodes[n].get("confidence", 0.5)),
            "date": G.nodes[n].get("date", ""),
        }
        for n in G.nodes
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "relation": G.edges[u, v].get("relation", "related"),
            "weight": float(G.edges[u, v].get("weight", 1.0)),
        }
        for u, v in G.edges
    ]
    log("info", f"Knowledge graph built: {len(nodes)} nodes, {len(edges)} edges")
    return {"nodes": nodes, "edges": edges}


def _safe_id(name: str, prefix: str) -> str:
    clean = "".join(ch if ch.isalnum() else "_" for ch in name)[:60]
    return f"{prefix}_{clean}_{abs(hash(clean)) % 10000}"


def _short(text: str, n: int = 42) -> str:
    return text if len(text) <= n else text[: n - 3] + "..."
