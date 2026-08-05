"""SENTINEL AI - seed the database with a demo intelligence product.

Runs the full pipeline against the bundled fictional sample image so the
dashboard has content immediately after setup.

    python scripts/seed_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import settings  # noqa: E402
from backend.core.logging import log  # noqa: E402
from backend.database import crud  # noqa: E402
from backend.database.session import create_tables, get_session_factory  # noqa: E402
from backend.intelligence.analyzer import run_pipeline  # noqa: E402


def main() -> int:
    create_tables()
    sample = settings.data / "sample_demo_incident.jpg"
    if not sample.exists():
        log("error", "Sample image not found - run from project root")
        return 1

    factory = get_session_factory()
    with factory() as session:
        analysis = crud.create_analysis(session, sample.name, str(sample))
        aid = analysis.id
        log("info", f"Seeding demo analysis #{aid} ...")
        result = run_pipeline(aid, str(sample), sample.name)
        crud.persist_full_result(session, analysis, result)
        log("info", f"Demo analysis #{aid} ready - open the dashboard to view it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
