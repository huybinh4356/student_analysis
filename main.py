"""
Main Application Entry Point for Student Performance Analysis Desktop System.
"""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_path = Path(__file__).resolve().parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from src.core.logging_config import setup_logging
logger = setup_logging()

try:
    from PyQt6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    def main():
        logger.info("Khoi tao giao dien PyQt6...")
        app = QApplication(sys.argv)
        logger.info("Khoi tao cua so chinh MainWindow...")
        window = MainWindow()
        window.show()
        logger.info("He thong da khoi dong thanh cong va san sang hoat dong.")
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()

except Exception as fatal_exc:
    logger.critical("LOI NGHIEM TRONG TRONG QUA TRINH KHOI DONG: %s", fatal_exc, exc_info=True)
    sys.exit(1)
