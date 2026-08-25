@echo off
setlocal EnableDelayedExpansion
title Stock Market Advisor
color 0A

echo.
echo ==========================================
echo  Stock Market Advisor
echo  http://localhost:8000
echo ==========================================
echo.

REM ── Check venv exists ────────────────────────────────────────
if not exist "venv" (
    echo [ERROR] Virtual environment not found.
    echo         Please run  setup.bat  first.
    echo.
    pause
    exit /b 1
)

REM ── Check .env exists in backend/ (where uvicorn runs from) ──
if not exist "backend\.env" (
    if exist ".env" (
        copy ".env" "backend\.env" >nul
        echo [INFO] .env copied to backend/.
    ) else if exist ".env.example" (
        copy ".env.example" "backend\.env" >nul
        echo [INFO] backend\.env created from template.
    ) else (
        echo [ERROR] No .env or .env.example found. Please create backend\.env
        pause
        exit /b 1
    )
)

REM ── Start the backend (serves API + React dashboard) ─────────
echo [INFO] Starting server...
echo [INFO] Open your browser at: http://localhost:8000
echo [INFO] Press Ctrl+C to stop.
echo.

call venv\Scripts\activate.bat
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
