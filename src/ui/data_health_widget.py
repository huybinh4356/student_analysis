"""
Dataset Health Assessment Panel Widget for Upload Tab.
Displays data completeness, invalid range warnings, IQR outliers, and overall health status.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QScrollArea,
    QProgressBar, QFrame, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt
import pandas as pd

from src.core.dataset_health import DatasetHealthChecker
from src.core.data_loader import DataLoader


class DataHealthWidget(QWidget):
    """
    Panel widget for inspecting dataset quality, missing values, duplicates, and invalid range values.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.health_checker = DatasetHealthChecker()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header Title & Refresh Button
        header_layout = QHBoxLayout()
        title_label = QLabel("Báo Cáo Sức Khỏe Dữ Liệu (Dataset Health Assessment)")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("Kiểm Tra Lại Dữ Liệu")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_refresh.clicked.connect(self.load_data)
        header_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(header_layout)

        # Scrollable Content Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(16)
        scroll.setWidget(container)

        main_layout.addWidget(scroll)

    def load_data(self):
        """Loads DataFrame from PostgreSQL or Excel data loader and runs health checks."""
        # Clear previous UI items
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            df = DataLoader.load_data()
        except Exception as e:
            err_label = QLabel(f"Không thể đọc CSDL hoặc file dữ liệu: {str(e)}")
            err_label.setStyleSheet("color: #ef4444; font-size: 14px;")
            self.content_layout.addWidget(err_label)
            return

        report = self.health_checker.check(df)
        self.render_health_report(report)

    def render_health_report(self, report: dict):
        """Renders health assessment dashboard from health check report dictionary."""
        # 1. Summary Cards Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        status_text = report["overall_status"].upper()
        if report["overall_status"] == "good":
            status_color = "#10b981"
            status_bg = "#064e3b"
            badge = "ĐẠT CHUẨN (GOOD)"
        elif report["overall_status"] == "warning":
            status_color = "#f59e0b"
            status_bg = "#78350f"
            badge = "CẦN CHÚ Ý (WARNING)"
        else:
            status_color = "#ef4444"
            status_bg = "#7f1d1d"
            badge = "NGHIÊM TRỌNG (CRITICAL)"

        card1 = self._create_summary_card("TRẠNG THÁI TỔNG THỂ", badge, status_color, status_bg)
        card2 = self._create_summary_card("QUY MÔ DỮ LIỆU", f"{report['total_rows']:,} dòng | {report['total_cols']} cột", "#38bdf8", "#0c4a6e")
        card3 = self._create_summary_card("DÒNG TRÙNG LẶP", f"{report['duplicate_rows']} dòng", "#a855f7" if report['duplicate_rows'] > 0 else "#64748b", "#3b0764" if report['duplicate_rows'] > 0 else "#1e293b")
        card4 = self._create_summary_card("CỘT BỊ KHUYẾT", f"{len(report['missing_summary'])} cột", "#f97316" if report['missing_summary'] else "#10b981", "#7c2d12" if report['missing_summary'] else "#064e3b")

        cards_layout.addWidget(card1, 1)
        cards_layout.addWidget(card2, 1)
        cards_layout.addWidget(card3, 1)
        cards_layout.addWidget(card4, 1)
        self.content_layout.addLayout(cards_layout)

        # 2. Missing Data Group
        group_missing = QGroupBox("Chi Tiết Dữ Liệu Bị Khuyết (Missing Summary)")
        group_missing.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_missing = QVBoxLayout(group_missing)

        if report["missing_summary"]:
            for col, info in report["missing_summary"].items():
                row_lbl = QLabel(f"• <b>{col}</b>: Thiếu {info['count']} bản ghi ({info['percentage']}%)")
                row_lbl.setStyleSheet("color: #fca5a5; font-size: 13px;")
                layout_missing.addWidget(row_lbl)
        else:
            no_miss = QLabel("Không có cột nào bị thiếu dữ liệu.")
            no_miss.setStyleSheet("color: #34d399; font-size: 13px;")
            layout_missing.addWidget(no_miss)

        self.content_layout.addWidget(group_missing)

        # 3. Invalid Values & Outliers Row
        row_invalid = QHBoxLayout()
        row_invalid.setSpacing(12)
        
        # Invalid values group
        group_inv = QGroupBox("Kiểm Tra Giá Trị Ngoài Khoảng (Out-of-bound Values)")
        group_inv.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_inv = QVBoxLayout(group_inv)

        if report["invalid_values"]:
            for col, info in report["invalid_values"].items():
                lbl = QLabel(f"• <b>{col}</b>: {info['count']} giá trị nằm ngoài khoảng [{info['expected_range'][0]}, {info['expected_range'][1]}] (Tìm thấy min={info['min_found']}, max={info['max_found']})")
                lbl.setStyleSheet("color: #fcd34d; font-size: 12px;")
                layout_inv.addWidget(lbl)
        else:
            ok_inv = QLabel("Tất cả chỉ số đều nằm trong khoảng quy chuẩn [0, 10].")
            ok_inv.setStyleSheet("color: #34d399; font-size: 12px;")
            layout_inv.addWidget(ok_inv)
        
        row_invalid.addWidget(group_inv, 1)

        # Outliers group
        group_out = QGroupBox("Phát Hiện Điểm Ngoại Lệ (Outliers IQR Method)")
        group_out.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_out = QVBoxLayout(group_out)

        if report["outlier_summary"]:
            for col, info in report["outlier_summary"].items():
                lbl = QLabel(f"• <b>{col}</b>: {info['count']} bản ghi ngoại lệ ({info['percentage']}%) ngoài khoảng IQR [{info['lower_bound']}, {info['upper_bound']}]")
                lbl.setStyleSheet("color: #93c5fd; font-size: 12px;")
                layout_out.addWidget(lbl)
        else:
            ok_out = QLabel("Không phát hiện điểm ngoại lệ bất thường.")
            ok_out.setStyleSheet("color: #34d399; font-size: 12px;")
            layout_out.addWidget(ok_out)

        row_invalid.addWidget(group_out, 1)
        self.content_layout.addLayout(row_invalid)

        # 4. Actionable Recommendations Group
        group_rec = QGroupBox("Khuyến Nghị Cải Thiện Chất Lượng Dữ Liệu")
        group_rec.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_rec = QVBoxLayout(group_rec)

        for i, rec in enumerate(report["recommendations"], 1):
            lbl = QLabel(f"{i}. {rec}")
            lbl.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
            layout_rec.addWidget(lbl)

        self.content_layout.addWidget(group_rec)

    def _create_summary_card(self, title: str, val: str, color: str, bg_color: str) -> QFrame:
        """Creates a styled summary card frame."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold;")

        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        return frame
