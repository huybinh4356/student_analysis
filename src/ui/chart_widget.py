"""
Custom Interactive Chart Builder Widget.
Allows users to select variables, chart types (Bar, Pie, Histogram, Scatter), and metrics.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.core.data_loader import DataLoader


class ChartWidget(QWidget):
    """Custom Interactive Chart Generator Widget."""

    # Friendly Display Names mapping to DataFrame columns
    COLUMN_MAP = {
        "Giới tính": "gioi_tinh",
        "Ngành học": "nganh_hoc",
        "Quê quán": "que_quan",
        "Hoàn cảnh kinh tế": "hoan_canh_kt",
        "Đi làm thêm": "di_lam_them",
        "Mức tương tác": "muc_tuong_tac",
        "Mức độ Stress": "muc_do_stress",
        "Động lực học tập": "dong_luc_hoc",
        "Nguy cơ học vụ": "nguy_co_hoc_vu",
        "Điểm THPT": "diem_thpt",
        "Điểm Giữa kỳ": "diem_gk",
        "Chuyên cần (%)": "chuyen_can",
        "Nộp bài đúng hạn (%)": "nop_bai_dung_han",
        "Điểm Tổng kết": "diem_tong_ket",
    }

    METRIC_MAP = {
        "Đếm số lượng sinh viên": "count",
        "Tính điểm Giữa kỳ trung bình": "diem_gk",
        "Tính điểm Tổng kết trung bình": "diem_tong_ket",
        "Tính tỷ lệ Chuyên cần trung bình": "chuyen_can",
    }

    def __init__(self):
        super().__init__()
        self.df = DataLoader.load_data()
        self.init_ui()

    def reload_data(self):
        """Reloads student dataset from PostgreSQL and updates active chart."""
        self.df = DataLoader.load_data()
        self.update_chart()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QVBoxLayout()
        title = QLabel("Tùy chỉnh Biểu đồ & Thống kê Tương tác")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Lựa chọn loại dữ liệu, dạng biểu đồ và chỉ số cần phân tích để khởi tạo đồ thị.")
        subtitle.setObjectName("sectionSubtitle")

        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Control Panel Group Box (Selection Controls)
        group_controls = QGroupBox("Cấu hình Biểu đồ")
        grid = QGridLayout(group_controls)

        # 1. Feature / Column Selector
        lbl_var1 = QLabel("1. Biến dữ liệu cần xem:")
        self.cbo_var1 = QComboBox()
        self.cbo_var1.addItems(list(self.COLUMN_MAP.keys()))
        self.cbo_var1.currentIndexChanged.connect(self.update_chart)

        grid.addWidget(lbl_var1, 0, 0)
        grid.addWidget(self.cbo_var1, 0, 1)

        # 2. Chart Type Selector
        lbl_type = QLabel("2. Dạng biểu đồ:")
        self.cbo_chart_type = QComboBox()
        self.cbo_chart_type.addItems([
            "Biểu đồ Cột (Bar Chart)",
            "Biểu đồ Tròn (Pie Chart)",
            "Biểu đồ Tần số (Histogram)",
            "Biểu đồ Phân tán (Scatter Plot)"
        ])
        self.cbo_chart_type.currentIndexChanged.connect(self.on_chart_type_changed)

        grid.addWidget(lbl_type, 0, 2)
        grid.addWidget(self.cbo_chart_type, 0, 3)

        # 3. Metric Aggregation Selector
        lbl_metric = QLabel("3. Chỉ số đo lường:")
        self.cbo_metric = QComboBox()
        self.cbo_metric.addItems(list(self.METRIC_MAP.keys()))
        self.cbo_metric.currentIndexChanged.connect(self.update_chart)

        grid.addWidget(lbl_metric, 1, 0)
        grid.addWidget(self.cbo_metric, 1, 1)

        # 4. Second Variable (For Scatter Plot)
        lbl_var2 = QLabel("4. Biến so sánh (Dành cho Scatter):")
        self.cbo_var2 = QComboBox()
        self.cbo_var2.addItems(list(self.COLUMN_MAP.keys()))
        self.cbo_var2.setCurrentText("Điểm Tổng kết")
        self.cbo_var2.setEnabled(False)
        self.cbo_var2.currentIndexChanged.connect(self.update_chart)

        grid.addWidget(lbl_var2, 1, 2)
        grid.addWidget(self.cbo_var2, 1, 3)

        layout.addWidget(group_controls)

        # Matplotlib Figure Canvas
        self.figure = Figure(figsize=(10, 5.5), facecolor="#1c2541")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.update_chart()

    def on_chart_type_changed(self):
        """Enables/disables second variable selector depending on chart type."""
        chart_type = self.cbo_chart_type.currentText()
        is_scatter = "Scatter" in chart_type
        self.cbo_var2.setEnabled(is_scatter)
        self.cbo_metric.setEnabled(not is_scatter and "Histogram" not in chart_type)
        self.update_chart()

    def update_chart(self):
        """Renders the selected chart dynamically based on user controls."""
        self.figure.clear()
        if self.df.empty:
            self.df = DataLoader.load_from_db()
            if self.df.empty:
                return

        col1_name = self.cbo_var1.currentText()
        col1 = self.COLUMN_MAP.get(col1_name)
        chart_type = self.cbo_chart_type.currentText()
        metric_name = self.cbo_metric.currentText()
        metric_col = self.METRIC_MAP.get(metric_name)

        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#0b132b")
        ax.tick_params(colors="#f8fafc", labelsize=10)
        for spine in ax.spines.values():
            spine.set_color("#3a506b")

        palette = ["#48cae4", "#0077b6", "#5bc0be", "#90e0ef", "#00b4d8", "#023e8a"]

        try:
            if "Biểu đồ Tròn" in chart_type:
                counts = self.df[col1].value_counts()
                wedges, texts, autotexts = ax.pie(
                    counts.values,
                    labels=counts.index,
                    autopct="%1.1f%%",
                    colors=palette[:len(counts)],
                    startangle=140,
                    textprops=dict(color="#f8fafc", fontsize=11)
                )
                for autotext in autotexts:
                    autotext.set_color("#0b132b")
                    autotext.set_weight("bold")

                ax.set_title(f"Tỷ lệ Phân bố theo {col1_name}", color="#48cae4", fontsize=14, fontweight="bold", pad=15)

            elif "Biểu đồ Tần số" in chart_type:
                if not pd.api.types.is_numeric_dtype(self.df[col1]):
                    ax.text(0.5, 0.5, "Vui lòng chọn biến số (Định lượng) cho Biểu đồ Tần số.",
                            color="#e74c3c", ha="center", va="center", fontsize=12, transform=ax.transAxes)
                else:
                    ax.hist(self.df[col1].dropna(), bins=15, color="#0077b6", edgecolor="#3a506b", alpha=0.85)
                    ax.set_title(f"Biểu đồ Tần số Phân bố của {col1_name}", color="#48cae4", fontsize=14, fontweight="bold", pad=15)
                    ax.set_xlabel(col1_name, color="#f8fafc")
                    ax.set_ylabel("Số lượng sinh viên", color="#f8fafc")

            elif "Biểu đồ Phân tán" in chart_type:
                col2_name = self.cbo_var2.currentText()
                col2 = self.COLUMN_MAP.get(col2_name)

                if not (pd.api.types.is_numeric_dtype(self.df[col1]) and pd.api.types.is_numeric_dtype(self.df[col2])):
                    ax.text(0.5, 0.5, "Vui lòng chọn 2 biến số (Định lượng) cho Biểu đồ Phân tán.",
                            color="#e74c3c", ha="center", va="center", fontsize=12, transform=ax.transAxes)
                else:
                    ax.scatter(self.df[col1], self.df[col2], color="#48cae4", alpha=0.6, edgecolors="none", s=35)
                    ax.set_title(f"Biểu đồ Phân tán: {col1_name} vs {col2_name}", color="#48cae4", fontsize=14, fontweight="bold", pad=15)
                    ax.set_xlabel(col1_name, color="#f8fafc")
                    ax.set_ylabel(col2_name, color="#f8fafc")

            else:  # Biểu đồ Cột (Bar Chart)
                if metric_col == "count":
                    series = self.df[col1].value_counts()
                    ylabel = "Số lượng sinh viên"
                else:
                    series = self.df.groupby(col1)[metric_col].mean()
                    ylabel = metric_name

                bars = ax.bar(series.index.astype(str), series.values, color="#0077b6", edgecolor="#3a506b", width=0.5)
                ax.set_title(f"Biểu đồ Cột: {col1_name} ({metric_name})", color="#48cae4", fontsize=14, fontweight="bold", pad=15)
                ax.set_ylabel(ylabel, color="#f8fafc")
                plt.setp(ax.get_xticklabels(), rotation=20, ha="right", color="#f8fafc")

                for bar in bars:
                    height = bar.get_height()
                    val_str = f"{height:.1f}" if metric_col != "count" else f"{int(height)}"
                    ax.annotate(val_str,
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha="center", va="bottom", color="#f8fafc", fontweight="bold")

            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            ax.clear()
            ax.text(0.5, 0.5, f"Không thể vẽ biểu đồ: {str(e)}", color="#f87171", ha="center", va="center", transform=ax.transAxes)
            self.canvas.draw()
