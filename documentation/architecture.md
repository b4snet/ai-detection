# SENTINEL AI — Architecture

## 1. System Overview

SENTINEL AI is a modular, local-first OSINT & image-intelligence platform. The backend is a
Python FastAPI service; the frontend is a React/Vite SPA. All AI is on-device (Ollama optional)
with a deterministic fallback, and the database is SQLite-by-default / PostgreSQL-capable.

```
┌────────────────────────────┐          ┌─────────────────────────────────────────┐
│       React SPA (5173)     │  /api    │        FastAPI backend (8000)           │
│  Dashboard / Upload /      │◀────────▶│  /status  /analysis  /search  /logs     │
│  Analysis / Search / Logs  │          │  /reports /uploads (static)             │
└────────────┬───────────────┘          └──────┬────────────────────────┬─────────┘
             │ polling (5s)                     │ background thread      │
             ▼                                   ▼                        ▼
┌──────────────────────┐          ┌──────────────────────┐   ┌──────────────────────┐
│ SentinelContext       │          │ intelligence/         │   │ database/            │
│ status + logs + list  │          │ analyzer.py (pipeline)│   │ SQLAlchemy ORM       │
└──────────────────────┘          └───┬──────────┬────────┘   │ SQLite / PostgreSQL  │
                                      │          │            └──────────────────────┘
                     ┌────────────────┴──┐   ┌───┴─────────────────┐
                     │ vision/           │   │ intelligence/       │
                     │ metadata.py       │   │ llm.py (Ollama)     │
                     │ detector.py       │   │ osint.py (Wiki/     │
                     │   (YOLO+OpenCV)   │   │  GDELT/simulated)   │
                     │ ocr.py (EasyOCR)  │   │ entity_extractor.py │
                     │ analyzer.py       │   │ graph.py (NetworkX) │
                     └───────────────────┘   │ report.py (PDF)    │
                                             └─────────────────────┘
```

## 2. Intelligence Pipeline (backend/intelligence/analyzer.py)

`run_pipeline()` executes six stages in a daemon thread so uploads return instantly:

1. **Computer Vision** — `vision/analyzer.py::analyze_image`
   - Pillow metadata + EXIF/GPS, dominant colors
   - YOLOv8n object/vehicle/person detection
   - Face-presence (Haar cascades on OpenCV <5, YOLO person fallback on 5+)
   - EasyOCR text, license-plate + credential pattern matching
   - Scene & location-clue synthesis
2. **Entity Recognition** — `intelligence/entity_extractor.py`
   - Faces → anonymous subject placeholder (never named)
   - Vehicles, plates, and heuristic OCR entities (ALL-CAPS phrases, demo seed terms)
   - Optional LLM extraction when Ollama is online
   - Parallel OSINT enrichment per entity (ThreadPoolExecutor)
3. **OSINT Retrieval** — `intelligence/osint.py`
   - Wikipedia REST API, GDELT doc API (both optional, circuit-broken on failure)
   - Bundled fictional dataset (`backend/sample_data/*.json`) — always available
   - On-disk JSON cache with positive + negative TTLs
4. **Knowledge Graph** — `intelligence/graph.py`
   - NetworkX graph: `entity --mentioned in--> source --reports--> event`
   - Serialized as `{nodes, edges}` for the frontend force-directed renderer
5. **AI Analysis** — `intelligence/llm.py`
   - Ollama `/api/generate` with strict system prompt (no accusation rules)
   - Structured JSON reports parsed with regex fallback
   - Fully deterministic template fallback when Ollama is unreachable
6. **Report Export** — `intelligence/report.py`
   - PDF (reportlab) + JSON snapshot written to `reports/`

## 3. Data Model (backend/models/entities.py)

| Table | Purpose |
|---|---|
| `analyses` | One row per uploaded image + pipeline result JSON blobs |
| `entities` | Persons / vehicles / orgs / locations with confidence + verification |
| `sources` | OSINT articles / references linked to analyses & entities |
| `timeline_events` | Dated events extracted during analysis |
| `graph_edges` | Knowledge-graph relationships |
| `activity_logs` | Terminal-style operations feed (also written by `core/logging.py`) |

## 4. Frontend

- **State:** `SentinelContext` polls `/status`, `/logs`, `/analysis/` every 5 s.
- **Visualization:** Three.js particle/globe background (`Starfield`); 2D canvas
  force-directed knowledge graph with pan/zoom/hover/click (`KnowledgeGraph`).
- **Pages:** Dashboard, Upload/Scan (progress animation + live feed), Analysis (full report),
  Search (OSINT + entity index), Logs.
- **Style:** Tailwind dark military/cyber theme — black + neon green, scanlines, CRT glow,
  corner frames, JetBrains Mono.

## 5. Configuration

`backend/config.py` reads `.env` via pydantic-settings. Key toggles: `SIMULATION_MODE`,
`VISION_ENABLED`, `OSINT_ENABLED`, `OLLAMA_*`, `GDELT_ENABLED`, `DATABASE_URL`.

## 6. Graceful Degradation

Every heavy dependency is lazily imported and wrapped. Missing modules are reported in the
status/capabilities endpoints and downgrade behavior:
- no YOLO/OpenCV/EasyOCR → Pillow metadata + heuristics (simulation)
- no Ollama → template AI engine (`ai_mode = degraded|simulation`)
- no internet → fictional demo OSINT dataset + negative-cache circuit breaker
- no reportlab → PDF step skipped, JSON always written

## 7. Security & Ethics Guards

- Prompt-level and post-processing guardrails prohibit person classification.
- License plates are surfaced as markers only; registry matching is never automatic.
- All outputs carry `confidence`, `verification: PENDING HUMAN REVIEW`, timestamps, sources.
- Reports include an explicit legal notice and analyst-review requirement.
