"""
Logging Configuration Module for Student Performance Analysis System.
Provides dual file logging (app.log, error.log), global crash exception hooks,
and real-time streaming for parallel monitor terminal.
"""

import sys
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
APP_LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"


class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that safely encodes characters on Windows console without crashing."""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            safe_msg = msg.encode("ascii", errors="backslashreplace").decode("ascii")
            self.stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Catches any uncaught exception across the entire application,
    logs it to error.log and stdout/stderr with detailed traceback.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_traceback = "".join(tb_lines)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    crash_header = (
        f"\n{'='*75}\n"
        f"[CRITICAL APPLICATION CRASH] {timestamp}\n"
        f"Exception Type  : {exc_type.__name__}\n"
        f"Exception Value : {exc_value}\n"
        f"{'='*75}\n"
        f"{full_traceback}"
        f"{'='*75}\n"
    )

    # 1. Print directly to stderr
    sys.stderr.write(crash_header)
    sys.stderr.flush()

    # 2. Append to error.log
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(crash_header)
        with open(APP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(crash_header)
    except Exception as io_err:
        sys.stderr.write(f"[LOG ERROR] Cannot write crash log to disk: {io_err}\n")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Sets up centralized logging for the whole project.
    Writes all events to logs/app.log, errors to logs/error.log,
    and streams to standard output for live terminal monitoring.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to prevent duplicate lines
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Formatter for file logs
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Formatter for console stream
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    # 1. App Log Handler (All levels from INFO up)
    app_handler = logging.FileHandler(APP_LOG_FILE, mode="a", encoding="utf-8")
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(file_formatter)
    root_logger.addHandler(app_handler)

    # 2. Error Log Handler (WARNING, ERROR, CRITICAL only)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, mode="a", encoding="utf-8")
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # 3. Safe Console Stream Handler
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Install global exception handler
    sys.excepthook = _global_exception_handler

    logger = logging.getLogger("student_analysis")
    logger.info("Logging initialized. App log: %s | Error log: %s", APP_LOG_FILE, ERROR_LOG_FILE)
    return logger
