@echo off
chcp 65001 > nul
title Student Analysis -- Live Log & Error Monitor
cd /d "%~dp0"

if not exist "logs" (
    mkdir logs
)

echo Khoi dong terminal giam sat log & chan doan loi...
.venv\Scripts\python.exe scripts\log_monitor.py

pause
