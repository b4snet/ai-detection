"""SENTINEL AI - structured logging.

Emits both console (terminal-style) and SQLite log rows used by the
frontend "SYSTEM LOG" panel.
"""
from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from typing import Optional

# ------------------------------------------------------------------ setup ----
_LOGGER = logging.getLogger("sentinel")
_LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("[SENTINEL] %(asctime)s %(levelname)s %(message)s")
    )
    _LOGGER.addHandler(_handler)

def log(level: str, message: str, analysis_id: Optional[int] = None) -> None:
    """Write a log line to the console AND the DB log table."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    getattr(_LOGGER, level.lower(), _LOGGER.info)(message)

    try:
        from sqlalchemy import text

        from backend.database.session import get_db_engine

        engine = get_db_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO activity_logs (timestamp, level, message, analysis_id) "
                    "VALUES (:ts, :level, :message, :analysis_id)"
                ),
                {"ts": ts, "level": level.upper(), "message": message,
                 "analysis_id": analysis_id},
            )
    except Exception:  # logging must never break the app
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def epoch_ms() -> int:
    return int(time.time() * 1000)
