"""SENTINEL AI - pre-download AI models for offline demo readiness.

Downloads:
  1. YOLOv8n weights -> ai_models/yolov8n.pt
  2. EasyOCR detection + recognition models (into user cache)
  3. (optional) an Ollama LLM via `ollama pull` when Ollama is running

Usage:
    python scripts/download_models.py
    python scripts/download_models.py --llm qwen2.5:7b
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import settings  # noqa: E402
from backend.core.logging import log  # noqa: E402


def download_yolo() -> None:
    log("info", "Downloading YOLOv8n weights...")
    try:
        from ultralytics import YOLO

        dest = settings.models / "yolov8n.pt"
        if dest.exists():
            log("info", f"YOLO weights already present: {dest}")
            return
        model = YOLO("yolov8n.pt")
        model.export  # noqa - ensure model built
        cwd = Path.cwd() / "yolov8n.pt"
        if cwd.exists():
            cwd.replace(dest)
        log("info", f"YOLO weights stored at {dest}")
    except Exception as exc:
        log("warning", f"YOLO download failed: {exc}")


def warm_ocr() -> None:
    log("info", "Warming EasyOCR models (one-time download)...")
    try:
        from backend.vision.ocr import _get_reader

        reader = _get_reader()
        if reader:
            log("info", "EasyOCR reader ready")
    except Exception as exc:
        log("warning", f"EasyOCR warm-up failed: {exc}")


def pull_llm(model: str) -> None:
    import shutil
    import subprocess

    ollama = shutil.which("ollama")
    if not ollama:
        log("warning", "ollama CLI not found on PATH - skipping LLM pull")
        return
    log("info", f"ollama pull {model} (may take minutes)...")
    subprocess.run([ollama, "pull", model], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", default="", help="Ollama model to pull, e.g. qwen2.5:7b")
    args = parser.parse_args()

    download_yolo()
    warm_ocr()
    if args.llm:
        pull_llm(args.llm)

    log("info", "Model preparation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
