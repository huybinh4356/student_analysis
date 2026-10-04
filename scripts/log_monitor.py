"""
Realtime Log & Error Monitoring Terminal for Student Analysis Platform.
Runs in a parallel console window, streaming all application logs, warnings,
and critical crash tracebacks in real-time.

Usage:
    python scripts/log_monitor.py
"""

from __future__ import annotations
import sys
import os
import time
from pathlib import Path

# Enable VT100 terminal escape sequences on Windows
if sys.platform == "win32":
    os.system("")

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT_DIR / "logs"
APP_LOG = LOGS_DIR / "app.log"
ERROR_LOG = LOGS_DIR / "error.log"

# ANSI Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{'='*75}{RESET}")
    print(f"{BOLD}{WHITE}  HE THONG GIAM SAT LOG & CHAN DOAN LOI -- STUDENT ANALYSIS PLATFORM{RESET}")
    print(f"{CYAN}{'='*75}{RESET}")
    print(f"  Thu muc goc : {ROOT_DIR}")
    print(f"  Tep Log Tong: {APP_LOG}")
    print(f"  Tep Log Loi : {ERROR_LOG}")
    print(f"  Trang thai  : {GREEN}[DANG HOAT DONG - SAN SANG LANG NGHE]{RESET}")
    print(f"  Luu y       : Cua so nay doc lap voi giao dien va se giu nguyen khi co loi.")
    print(f"{CYAN}{'-'*75}{RESET}\n")
    sys.stdout.flush()


def format_log_line(line: str) -> str:
    """Formats and colors log lines according to severity level."""
    stripped = line.rstrip()
    if not stripped:
        return ""

    if "[CRITICAL" in stripped or "[CRASH" in stripped or "Traceback (most recent call last)" in stripped:
        return f"{BOLD}{RED}{stripped}{RESET}"
    elif "[ERROR" in stripped or "Error:" in stripped or "Exception:" in stripped:
        return f"{RED}{stripped}{RESET}"
    elif "[WARNING" in stripped or "[WARN" in stripped:
        return f"{YELLOW}{stripped}{RESET}"
    elif "[INFO" in stripped:
        return f"{WHITE}{stripped}{RESET}"
    elif "[DEBUG" in stripped:
        return f"\033[90m{stripped}{RESET}"
    else:
        return stripped


def tail_logs():
    """Follows app.log and error.log continuously in real-time."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not APP_LOG.exists():
        APP_LOG.touch()
    if not ERROR_LOG.exists():
        ERROR_LOG.touch()

    # Open app.log and seek to beginning of today or current tail
    with open(APP_LOG, "r", encoding="utf-8", errors="replace") as f_app:
        # Read initial recent lines if any exist
        existing_lines = f_app.readlines()
        if existing_lines:
            recent_lines = existing_lines[-40:] if len(existing_lines) > 40 else existing_lines
            print(f"{YELLOW}[LOG LICH SU] ----------------------------------------------------{RESET}")
            for l in recent_lines:
                fmt = format_log_line(l)
                if fmt:
                    print(fmt)
            print(f"{YELLOW}[LOG REALTIME] ---------------------------------------------------{RESET}\n")
            sys.stdout.flush()

        # Stream new lines continuously
        while True:
            line = f_app.readline()
            if line:
                formatted = format_log_line(line)
                if formatted:
                    print(formatted)
                    sys.stdout.flush()
            else:
                time.sleep(0.2)


def main():
    if sys.platform == "win32":
        # Set console window title
        os.system("title Student Analysis -- Live Log & Error Monitor")

    print_banner()

    try:
        tail_logs()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[INFO] Da dung tien trinh giam sat log theo yeu cau nguoi dung.{RESET}")
        print("Nhan Enter de thoat cua so...")
        sys.stdout.flush()
        try:
            input()
        except Exception:
            pass


if __name__ == "__main__":
    main()
