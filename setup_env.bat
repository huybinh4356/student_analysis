@echo off
chcp 65001 > nul
title Setup Environment - Student Analysis

echo ==================================================================
echo   ONE-CLICK ENVIRONMENT AND DEPENDENCY INSTALLATION SCRIPT
echo ==================================================================
echo.

cd /d "%~dp0"

echo [1/3] Creating virtual environment (.venv)...
python -m venv .venv

echo [2/3] Installing all required Python libraries...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install pandas numpy openpyxl sqlalchemy "psycopg[binary]" psycopg2-binary scikit-learn xgboost matplotlib pyqt6 python-dotenv alembic joblib statsmodels pytest

echo [3/3] Exporting requirements.txt...
.venv\Scripts\pip.exe freeze > requirements.txt

echo.
echo ==================================================================
echo   SETUP COMPLETE! Double-click run_app.bat to launch application.
echo ==================================================================
pause
