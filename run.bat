@echo off
chcp 65001 > nul
title Student Performance Analysis System

cd /d "%~dp0"

echo ==================================================================
echo   STUDENT PERFORMANCE ANALYSIS AND PREDICTION SYSTEM
echo ==================================================================
echo.
echo [INFO] Launching Desktop Application...
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Application encountered an error or exited unexpectedly.
    pause
)
