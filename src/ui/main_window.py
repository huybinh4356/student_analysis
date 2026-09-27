"""
Main Window container for Student Performance Analysis Desktop Application.
Clean, professional corporate interface without casual icons or emojis.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QFrame
)
from PyQt6.QtCore import Qt

from src.ui.data_management_widget import DataManagementWidget
from src.ui.chart_widget import ChartWidget
from src.ui.analysis_widget import AnalysisWidget
from src.ui.diagnosis_widget import DiagnosisWidget
from src.ui.whatif_widget import WhatIfWidget
from src.ui.report_widget import ReportWidget


class MainWindow(QMainWindow):
    """Main Application Window hosting Sidebar Navigation and Page Stack."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Phân tích & Dự đoán Kết quả Học tập Sinh viên v2.0")
        self.resize(1350, 850)
        self.init_ui()
        self.load_stylesheet()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Panel
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        app_title = QLabel("QUẢN LÝ & DỰ BÁO HỌC VỤ v2.0")
        app_title.setObjectName("appTitle")
        sidebar_layout.addWidget(app_title)

        # Navigation Buttons (Clean corporate design)
        self.btn_data = QPushButton("1. Dữ Liệu & Ingest CSDL")
        self.btn_charts = QPushButton("2. Tùy Chọn Biểu Đồ EDA")
        self.btn_analysis = QPushButton("3. Dự Báo ML & Nguy Cơ")
        self.btn_diagnosis = QPushButton("4. Chẩn Đoán & Missing Data")
        self.btn_whatif = QPushButton("5. Mô Phỏng What-If v2.0")
        self.btn_reports = QPushButton("6. Xuất Báo Cáo Tổng Hợp")

        self.nav_buttons = [
            self.btn_data,
            self.btn_charts,
            self.btn_analysis,
            self.btn_diagnosis,
            self.btn_whatif,
            self.btn_reports,
        ]

        for i, btn in enumerate(self.nav_buttons):
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        footer_label = QLabel("Phiên bản v2.0 | Offline System")
        footer_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 12px;")
        sidebar_layout.addWidget(footer_label)

        main_layout.addWidget(sidebar)

        # 2. Main Content Area (StackedWidget)
        self.stacked_widget = QStackedWidget()

        self.data_page = DataManagementWidget()
        self.chart_page = ChartWidget()
        self.analysis_page = AnalysisWidget()
        self.diagnosis_page = DiagnosisWidget()
        self.whatif_page = WhatIfWidget()
        self.report_page = ReportWidget()

        self.stacked_widget.addWidget(self.data_page)
        self.stacked_widget.addWidget(self.chart_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.diagnosis_page)
        self.stacked_widget.addWidget(self.whatif_page)
        self.stacked_widget.addWidget(self.report_page)

        # Connect data upload signal to trigger app-wide refresh
        if hasattr(self.data_page, "upload_widget"):
            self.data_page.upload_widget.data_reloaded.connect(self.on_data_reloaded)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # 3. Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Hệ thống Phân tích Kết quả Học tập v2.0 — CSDL PostgreSQL đã kết nối thành công.")

        self.switch_page(0)

    def on_data_reloaded(self):
        """Refreshes all pages in the application whenever a new dataset is uploaded into PostgreSQL."""
        try:
            # 1. Refresh Data Health page
            if hasattr(self.data_page, "health_widget"):
                self.data_page.health_widget.load_data()

            # 2. Refresh Chart page
            if hasattr(self.chart_page, "reload_data"):
                self.chart_page.reload_data()

            # 3. Retrain/Refresh ML Analysis page
            if hasattr(self.analysis_page, "train_all_models"):
                self.analysis_page.train_all_models()

            # 4. Refresh Diagnosis page student list
            if hasattr(self.diagnosis_page, "load_student_list"):
                self.diagnosis_page.load_student_list()

            # 5. Refresh What-If page student list
            if hasattr(self.whatif_page, "load_student_data"):
                self.whatif_page.load_student_data()

            self.statusBar().showMessage("Đã đồng bộ và phân tích lại toàn bộ CSDL sinh viên mới!")
        except Exception:
            pass

    def switch_page(self, index: int):
        """Switches the active page in QStackedWidget."""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        self.stacked_widget.setCurrentIndex(index)

    def load_stylesheet(self):
        """Loads styles.qss stylesheet."""
        qss_path = Path(__file__).resolve().parent / "styles.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

