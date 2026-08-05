# SENTINEL AI

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/b4snet/ai-detection)

## AI-Powered Open Source Intelligence & Threat Analysis Platform

SENTINEL AI is a hackathon-grade intelligence **assistant** that uploads an image, runs a local
AI / computer-vision pipeline, retrieves publicly available information, builds a relationship
knowledge graph, and renders everything in a futuristic security-dashboard UI.

> **Responsible design promise:** SENTINEL **never** autonomously accuses, classifies, or labels
> any person as a criminal, terrorist, anti-national, or threat. It produces *evidence indicators,
> confidence scores, source lists, timestamps, and verification statuses* — and always demands
> human analyst review before any operational use. Identity matching uses simulated / authorized
> datasets only.

```
IMAGE INPUT ─▶ COMPUTER VISION ─▶ FEATURE EXTRACTION ─▶ ENTITY RECOGNITION
     ─▶ OSINT RETRIEVAL ─▶ KNOWLEDGE GRAPH ─▶ AI ANALYSIS ─▶ SECURITY DASHBOARD
```

---

## Live Demo

> **http://localhost:5173** — run the full pipeline on your machine: `python run.py`
> then open the web UI.

> **Hosted UI preview:** https://b4snet.github.io/find-the-person/
> (GitHub Pages build of the dashboard. The pipeline backend runs locally, so the hosted
> link shows the interface with a "backend offline" notice — start `python run.py` to connect
> it to live data.)

---

## Feature Highlights

| Module | What it does |
|---|---|
| **Image Intelligence** | YOLO object/vehicle/person detection, OpenCV face presence, EasyOCR text + license plates, EXIF/GPS metadata, dominant colors, scene & location clues |
| **OSINT Engine** | Wikipedia REST API, GDELT global news graph, plus a bundled *fictional* demo dataset — every finding tagged source/type/date/relevance/verification |
| **Local AI (Ollama)** | Report generation, entity extraction, summarization via Llama/Mistral/Gemma/Qwen — with a fully deterministic fallback engine when Ollama is offline |
| **Knowledge Graph** | NetworkX relationship graph (entities ↔ sources ↔ events) rendered as an interactive force-directed visualization |
| **Intelligence Reports** | Downloadable PDF + JSON reports with summary, evidence, sources, confidence, timeline, legal notice |
| **Real-time dashboard** | System status, live terminal log, processing animation, source timeline, entity profiles, entity/event/location search |
| **Zero cost** | Everything runs locally — no paid APIs required |

---

## Architecture

```
sentinel-ai/
│
├── backend/                  # Python + FastAPI
│   ├── api/routes/           # status, analysis, search, logs, reports
│   ├── core/                 # structured logging -> DB activity log
│   ├── database/             # SQLAlchemy (SQLite default, PostgreSQL ready)
│   ├── intelligence/         # LLM bridge, OSINT, entity extraction, graph, reports
│   ├── models/               # ORM models + API schemas
│   ├── vision/               # metadata, YOLO/OpenCV detector, OCR, pipeline
│   └── sample_data/          # fictional demo dataset + sample images
│
├── frontend/                 # React + Vite + Tailwind + Three.js
│   └── src/
│       ├── components/       # Starfield, KnowledgeGraph, Timeline, EntityCard...
│       ├── pages/            # Dashboard, Upload, Analysis, Search, Logs
│       ├── api/              # REST client
│       └── context/          # global status / log store (auto-refresh 5s)
│
├── ai_models/                # downloaded YOLO weights live here
├── database/                 # SQLite file
├── reports/                  # generated PDF/JSON reports
├── documentation/architecture.md
└── scripts/                  # model downloader, demo seeder
```

**Stack:** Python 3.11+ • FastAPI • SQLAlchemy • OpenCV • Ultralytics YOLO • EasyOCR •
NetworkX • reportlab • React 18 • Vite 5 • Tailwind CSS 3 • Three.js • Ollama (optional)

---

## Quick Start

### 1. Prerequisites
- Python 3.11 – 3.12 (3.13/3.14 may work; optional vision wheels lag behind)
- Node.js 18+
- (Recommended) [Ollama](https://ollama.com) running locally with a model:
  `ollama pull qwen2.5:7b`

### 2. One-time setup
**Windows**
```bat
setup.bat
```
**macOS / Linux**
```bash
chmod +x setup.sh && ./setup.sh
```

`setup.bat` creates a venv, installs `requirements.txt` (+ optional vision stack), installs
frontend deps, and pre-downloads YOLO/EasyOCR models.

> **No heavy models?** No problem — the platform auto-detects missing modules and runs in
> **simulation mode** (Pillow metadata + rule-based analysis + fictional OSINT dataset) so the
> hackathon demo always works. Install `requirements-optional.txt` to unlock full CV.

### 3. Run
```bash
python run.py
```
- Web UI → http://localhost:5173
- API docs → http://127.0.0.1:8000/docs

Or run separately:
```bash
# terminal 1
.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev
```

### 4. Seed a demo analysis (optional)
```bash
python scripts/seed_demo.py
```

---

## Usage Flow

1. **Dashboard** — live system status, AI engine state, recent analyses.
2. **Upload** — drag & drop an image (person / vehicle / object / document / screenshot /
   news image). Watch the multi-stage processing animation + live pipeline log.
3. **Analysis report** — evidence image, visual intelligence matrix, OCR output, detected
   objects, entities panel, AI assessment, relationship graph, source timeline, public sources,
   and PDF/JSON report download.
4. **Search** — query public sources (`/search/osint`) or the local entity index.
5. **System Log** — terminal-style operations feed.

**Demo tip:** upload `backend/sample_data/sample_demo_incident.jpg` — its visible signage
("NORTHLINE", "VEGA") links through the fictional dataset to timeline events and graph nodes.

---

## Environment variables (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./database/sentinel.db` | Swap to PostgreSQL anytime |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Local LLM endpoint |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Report/entity model |
| `SIMULATION_MODE` | `auto` | `auto` / `on` / `off` |
| `GDELT_ENABLED` | `true` | Live news retrieval toggle |
| `NEWSAPI_KEY` / `OPENCAGE_API_KEY` | empty | Optional free-tier integrations |

---

## Ethics & Responsible Use

- **Assistant, not enforcement.** Outputs are indicator-based intelligence with confidence,
  provenance, timestamps, and verification — never verdicts.
- **No autonomous identification.** Faces yield an *anonymous* subject placeholder.
  License plates are surfaced as markers but never registry-matched automatically.
- **Human-in-the-loop.** Every report requires analyst review before operational use.
- **Simulated matching.** Sensitive identity matching runs only against the bundled fictional
  dataset. Bring your own *authorized* data for production use.
- **Compliance.** Operators must respect applicable privacy, surveillance, and data-protection
  laws in their jurisdiction.

Intended for authorized security researchers, investigators, students, and CTF/hackathon
environments with lawful authorization to analyze the material involved.

---

## License
Hackathon / educational use. Open-source tools only — no paid services required.
