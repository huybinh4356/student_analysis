@echo off
chcp 65001 > nul
title Auto-Setup & Launch - Student Performance Analysis System

echo ==================================================================
echo   STUDENT PERFORMANCE ANALYSIS AND PREDICTION SYSTEM
echo   Zero-Setup Auto Launcher for New Cloned Projects
echo ==================================================================
echo.

cd /d "%~dp0"

REM 1. Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please download and install Python 3.11+ from https://www.python.org/
    echo Remember to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM 2. Check and copy .env file
if not exist ".env" (
    echo [SETUP] File .env not found. Copying from .env.example...
    copy .env.example .env > nul
    echo [SETUP] File .env created.
)

REM 3. Check virtual environment .venv
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Virtual environment .venv not found. Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment .venv.
        pause
        exit /b 1
    )
    echo [SETUP] Installing required libraries from requirements.txt...
    .venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    .venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please check network connection.
        pause
        exit /b 1
    )
    echo [SETUP] All dependencies installed successfully.
) else (
    echo [OK] Virtual environment .venv is ready.
)

REM 4. Check Docker installation and start PostgreSQL container
docker --version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker is not installed or not running.
    echo Please install and start Docker Desktop to enable PostgreSQL database.
) else (
    echo [SETUP] Starting Docker Container PostgreSQL (student_db)...
    docker compose up -d > nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Could not start Docker container. Please launch Docker Desktop.
    ) else (
        echo [OK] Docker Container student_db is running on port 5433.
    )
)

REM 5. Ingest student data into PostgreSQL
echo [SETUP] Syncing student dataset into PostgreSQL Database...
.venv\Scripts\python.exe -m src.db.ingest > nul 2>&1
echo [OK] Database synced.

REM 6. Train Machine Learning Models if artifacts are missing
if not exist "models\ridge_regression_model.pkl" (
    echo [SETUP] Training Machine Learning models for the first time...
    .venv\Scripts\python.exe scripts/train_models.py > nul 2>&1
    echo [OK] Models trained and saved to models/ directory.
)

echo.
echo ==================================================================
echo   LAUNCHING DESKTOP APPLICATION...
echo ==================================================================
echo.

start "" ".venv\Scripts\python.exe" main.py
exit /b 0
