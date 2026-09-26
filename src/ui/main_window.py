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

from src.ui.upload_widget import UploadWidget
from src.ui.chart_widget import ChartWidget
from src.ui.analysis_widget import AnalysisWidget
from src.ui.insight_widget import InsightWidget
from src.ui.report_widget import ReportWidget


class MainWindow(QMainWindow):
    """Main Application Window hosting Sidebar Navigation and Page Stack."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Phân tích & Dự đoán Kết quả Học tập Sinh viên")
        self.resize(1300, 820)
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

        app_title = QLabel("QUẢN LÝ & DỰ BÁO HỌC VỤ")
        app_title.setObjectName("appTitle")
        sidebar_layout.addWidget(app_title)

        # Navigation Buttons (Clean of all emojis)
        self.btn_upload = QPushButton("1. Dữ liệu & Ingest")
        self.btn_charts = QPushButton("2. Tùy chọn Biểu đồ EDA")
        self.btn_analysis = QPushButton("3. Dự báo & Huấn luyện ML")
        self.btn_insights = QPushButton("4. Tư vấn Can thiệp & What-If")
        self.btn_reports = QPushButton("5. Xuất Báo cáo Tổng hợp")

        self.nav_buttons = [
            self.btn_upload,
            self.btn_charts,
            self.btn_analysis,
            self.btn_insights,
            self.btn_reports,
        ]

        for i, btn in enumerate(self.nav_buttons):
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        footer_label = QLabel("Phiên bản 1.0.0 | Offline System")
        footer_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 12px;")
        sidebar_layout.addWidget(footer_label)

        main_layout.addWidget(sidebar)

        # 2. Main Content Area (StackedWidget)
        self.stacked_widget = QStackedWidget()

        self.upload_page = UploadWidget()
        self.chart_page = ChartWidget()
        self.analysis_page = AnalysisWidget()
        self.insight_page = InsightWidget()
        self.report_page = ReportWidget()

        self.stacked_widget.addWidget(self.upload_page)
        self.stacked_widget.addWidget(self.chart_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.insight_page)
        self.stacked_widget.addWidget(self.report_page)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # 3. Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Hệ thống Phân tích Kết quả Học tập — Cơ sở dữ liệu PostgreSQL đã kết nối.")

        self.switch_page(0)

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
