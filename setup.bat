@echo off
setlocal
REM ============================================================
REM  SENTINEL AI - One-time environment setup (Windows)
REM ============================================================
echo [SENTINEL] Creating Python virtual environment...
python -m venv .venv
if errorlevel 1 goto :fail

echo [SENTINEL] Installing backend dependencies...
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [SENTINEL] Installing optional AI/vision stack (YOLO, EasyOCR, OpenCV)...
call .venv\Scripts\python.exe -m pip install -r requirements-optional.txt
if errorlevel 1 echo [SENTINEL] Optional stack skipped (core platform still works)

echo [SENTINEL] Installing frontend dependencies...
pushd frontend
call npm install
popd
if errorlevel 1 goto :fail

echo [SENTINEL] Pre-downloading AI models...
call .venv\Scripts\python.exe scripts\download_models.py

echo.
echo [SENTINEL] Setup complete. Start the platform with:
echo     python run.py
echo.
echo [SENTINEL] Optional: pull a local LLM for richer reports:
echo     ollama pull qwen2.5:7b
goto :eof

:fail
echo [SENTINEL] Setup FAILED. Check the error above.
exit /b 1
