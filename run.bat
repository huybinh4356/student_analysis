@echo off
chcp 65001 > nul
title Student Performance Analysis System v3.0

cd /d "%~dp0"

echo ==================================================================
echo   STUDENT PERFORMANCE ANALYSIS SYSTEM v3.0 (ONE-CLICK LAUNCHER)
echo ==================================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chưa được cài đặt hoặc chưa thêm vào PATH!
    pause
    exit /b 1
)

REM 2. Check Virtualenv
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Tạo môi trường ảo .venv...
    python -m venv .venv
    echo [INFO] Cài đặt dependencies...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    if exist "requirements.txt" (
        .venv\Scripts\python.exe -m pip install -r requirements.txt
    )
)

REM 3. Check .env
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Tạo file cấu hình .env từ .env.example...
        copy .env.example .env > nul
    )
)

REM 4. Check Docker (Graceful fallback if Docker is not started)
docker --version >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Khởi động Docker container PostgreSQL (nếu chưa chạy)...
    docker compose up -d >nul 2>&1
) else (
    echo [INFO] Docker không sẵn sàng — ứng dụng sẽ tự động dùng chế độ Excel fallback.
)

REM 5. Ensure logs directory exists
if not exist "logs" (
    mkdir logs
)

REM 6. Launch Parallel Log & Error Monitor Terminal
echo [INFO] Khoi dong cua so Terminal giam sat Log & Chan doan loi song song...
start "Student Analysis -- Live Log & Error Monitor" cmd /k "chcp 65001 >nul && .venv\Scripts\python.exe scripts\log_monitor.py"

REM 7. Launch application
echo.
echo [INFO] Dang khoi dong giao dien PyQt6...
.venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo.
    echo ==================================================================
    echo [ERROR] Ung dung khong the khoi dong hoac da dung dot ngot voi loi!
    echo Chi tiet nguyen nhan duoc ghi nhan day du tai:
    echo   1. Cua so Terminal 'Live Log & Error Monitor' dang chay song song
    echo   2. Tep nhat ky loi: logs\error.log
    echo ==================================================================
    echo.
    pause
)
