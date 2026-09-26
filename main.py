"""
Main Application Entry Point for Student Performance Analysis Desktop System.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Ensure root directory is in sys.path
root_path = Path(__file__).resolve().parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
