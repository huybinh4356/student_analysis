@echo off
chcp 65001 > nul
title Student Performance Analysis System

echo ==================================================================
echo   STUDENT PERFORMANCE ANALYSIS AND PREDICTION SYSTEM
echo ==================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating Python virtual environment .venv...
    python -m venv .venv
    echo Done.
) else (
    echo [1/4] Virtual environment .venv is ready.
)

echo [2/4] Checking dependencies in requirements.txt...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
.venv\Scripts\pip.exe install --quiet -r requirements.txt
echo Dependencies verified.

echo [3/4] Starting Docker Container PostgreSQL (student_db)...
docker compose up -d > nul 2>&1
echo Docker container status checked.

echo [4/4] Ingesting student data into PostgreSQL...
.venv\Scripts\python.exe -m src.db.ingest > nul 2>&1
echo Data ingestion completed.

echo.
echo ==================================================================
echo   LAUNCHING DESKTOP APPLICATION (PyQt6)...
echo ==================================================================
echo.

start "" ".venv\Scripts\python.exe" main.py
exit /b 0
