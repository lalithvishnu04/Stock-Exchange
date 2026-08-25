@echo off
setlocal EnableDelayedExpansion
title Stock Market Advisor - First-Time Setup
color 0A

echo.
echo ==========================================
echo  Stock Market Advisor - First-Time Setup
echo ==========================================
echo.

REM ── Step 1: Check Python ──────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found.

REM ── Step 2: Create .env if missing ───────────────────────────
if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy ".env.example" ".env" >nul
    echo [OK] .env created.
) else (
    echo [OK] .env already exists.
)

REM ── Step 3: Create Python virtual environment ────────────────
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

REM ── Step 4: Install Python dependencies ──────────────────────
echo [INFO] Installing Python packages (this takes 2-3 minutes first time)...
call venv\Scripts\activate.bat
pip install -r backend\requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)
echo [OK] Python packages installed.

REM ── Step 5: Build React frontend (requires Node.js) ──────────
where node >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARN] Node.js not found - frontend will not be built.
    echo        You can still use the API at http://localhost:8000/api/docs
    echo        To get the full dashboard, install Node.js from https://nodejs.org
    echo        Then run this setup script again.
    echo.
) else (
    echo [INFO] Building React frontend...
    cd frontend
    call npm install --silent
    call npm run build
    if errorlevel 1 (
        echo [WARN] Frontend build failed - check errors above.
    ) else (
        echo [OK] Frontend built successfully.
    )
    cd ..
)

echo.
echo ==========================================
echo  Setup complete!
echo  Run  run.bat  to start the dashboard.
echo ==========================================
echo.
pause
