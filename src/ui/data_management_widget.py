"""
Data Management Container Widget.
Combines UploadWidget (Excel file input & PostgreSQL table preview)
and DataHealthWidget (Dataset quality health assessment) into Tab 1.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from src.ui.upload_widget import UploadWidget
from src.ui.data_health_widget import DataHealthWidget


class DataManagementWidget(QWidget):
    """Container widget hosting Data Upload and Dataset Health sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #0f172a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #cbd5e1;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)

        self.upload_widget = UploadWidget()
        self.health_widget = DataHealthWidget()

        self.tabs.addTab(self.upload_widget, "📁 Tải File Excel Mới & CSDL PostgreSQL")
        self.tabs.addTab(self.health_widget, "📊 Báo Cáo Sức Khỏe Dữ Liệu Dataset")

        layout.addWidget(self.tabs)
