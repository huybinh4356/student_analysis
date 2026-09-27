"""
Before vs After Comparison Bar Chart Widget for What-If Simulations.
Uses matplotlib Qt canvas to render clean, corporate dark mode visual bar comparison.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class WhatIfChartWidget(QWidget):
    """
    Renders Before vs After comparison bar charts for predicted student performance.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure dark theme setup
        self.figure = Figure(figsize=(5, 3.5), facecolor="#1e293b")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._set_dark_style()
        self.update_chart(7.0, 7.0)

    def _set_dark_style(self):
        """Applies dark corporate palette to matplotlib axis."""
        self.ax.set_facecolor("#0f172a")
        self.ax.tick_params(colors="#cbd5e1", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color("#334155")
        self.ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="#475569")
        self.ax.set_axisbelow(True)

    def update_chart(self, original_score: float, simulated_score: float):
        """
        Updates bar chart with original and simulated scores.

        Args:
            original_score: Original predicted grade.
            simulated_score: Simulated grade after feature adjustment.
        """
        self.ax.clear()
        self._set_dark_style()

        categories = ["Trước thay đổi", "Sau thay đổi"]
        values = [original_score, simulated_score]

        # Determine bar color based on delta
        delta = simulated_score - original_score
        if delta > 0.05:
            sim_color = "#10b981"  # Emerald green for increase
        elif delta < -0.05:
            sim_color = "#ef4444"  # Red for decrease
        else:
            sim_color = "#3b82f6"  # Blue for neutral

        colors = ["#64748b", sim_color]  # Slate grey for before

        bars = self.ax.bar(categories, values, color=colors, width=0.45, edgecolor="#1e293b", linewidth=1.5)

        # Add data label callouts on top of bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.25,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                color="#f8fafc",
                fontsize=10,
                fontweight="bold",
            )

        self.ax.set_ylim(0, 10.8)
        self.ax.set_ylabel("Điểm dự đoán (Hệ 10)", color="#94a3b8", fontsize=9)
        self.ax.set_title("So Sánh Điểm Tổng Kết Môn Học", color="#f8fafc", fontsize=11, fontweight="bold", pad=12)

        self.figure.tight_layout()
        self.canvas.draw()
