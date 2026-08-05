"""SENTINEL AI - one-command launcher.

Starts the FastAPI backend and the Vite frontend together and opens the
browser. Requires the venv (setup.bat) and `npm install` (frontend).

    python run.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

HOST = "127.0.0.1"
API_PORT = 8000
WEB_PORT = 5173


def is_port_open(port: int, host: str = HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def python_exe() -> str:
    local = ROOT / ".venv" / "Scripts" / "python.exe"
    if local.exists():
        return str(local)
    return sys.executable


def wait_for(port: int, timeout: int, label: str) -> None:
    print(f"[SENTINEL] waiting for {label} on :{port} ...")
    for _ in range(timeout * 2):
        if is_port_open(port):
            print(f"[SENTINEL] {label} ONLINE -> http://{HOST}:{port}")
            return
        time.sleep(0.5)
    print(f"[SENTINEL] WARNING: {label} did not report ready in {timeout}s")


def main() -> int:
    if not (ROOT / ".venv").exists():
        print("ERROR: virtualenv not found. Run setup.bat first.")
        return 1
    if not (FRONTEND / "node_modules").exists():
        print("ERROR: frontend deps missing. Run:  cd frontend && npm install")
        return 1

    procs = []

    # --- backend ---------------------------------------------------------
    if is_port_open(API_PORT):
        print(f"[SENTINEL] backend already running on :{API_PORT}")
    else:
        cmd = [
            python_exe(), "-m", "uvicorn", "backend.main:app",
            "--host", HOST, "--port", str(API_PORT),
        ]
        procs.append(subprocess.Popen(cmd, cwd=str(ROOT)))

    # --- frontend --------------------------------------------------------
    if is_port_open(WEB_PORT):
        print(f"[SENTINEL] frontend already running on :{WEB_PORT}")
    else:
        npm = "npm.cmd" if os.name == "nt" else "npm"
        front_proc = subprocess.Popen(
            [npm, "run", "dev"],
            cwd=str(FRONTEND),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt" else 0,
        )
        procs.append(front_proc)

    wait_for(API_PORT, 30, "API")
    wait_for(WEB_PORT, 30, "WEB UI")

    url = f"http://localhost:{WEB_PORT}"
    print(f"[SENTINEL] opening {url}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print("[SENTINEL] Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SENTINEL] shutting down...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
