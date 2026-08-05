#!/usr/bin/env bash
# ============================================================
#  SENTINEL AI - One-time environment setup (macOS / Linux)
# ============================================================
set -e

echo "[SENTINEL] Creating Python virtual environment..."
python3 -m venv .venv

echo "[SENTINEL] Installing backend dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "[SENTINEL] Installing optional AI/vision stack..."
.venv/bin/python -m pip install -r requirements-optional.txt || echo "[SENTINEL] Optional stack skipped (core platform still works)"

echo "[SENTINEL] Installing frontend dependencies..."
(cd frontend && npm install)

echo "[SENTINEL] Pre-downloading AI models..."
.venv/bin/python scripts/download_models.py

echo
echo "[SENTINEL] Setup complete. Start the platform with:"
echo "    python run.py"
echo
echo "[SENTINEL] Optional: pull a local LLM for richer reports:"
echo "    ollama pull qwen2.5:7b"
