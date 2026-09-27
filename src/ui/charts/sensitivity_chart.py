"""
Sensitivity Analysis Ranking Horizontal Bar Chart Widget.
Renders feature sensitivity impact magnitudes.
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SensitivityChartWidget(QWidget):
    """
    Renders horizontal bar charts ranking top features by sensitivity impact.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(5, 3.5), facecolor="#1e293b")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._set_dark_style()

    def _set_dark_style(self):
        """Applies dark theme layout to matplotlib axis."""
        self.ax.set_facecolor("#0f172a")
        self.ax.tick_params(colors="#cbd5e1", labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color("#334155")
        self.ax.xaxis.grid(True, linestyle="--", alpha=0.3, color="#475569")
        self.ax.set_axisbelow(True)

    def update_chart(self, sensitivity_data: List[Dict[str, Any]]):
        """
        Updates horizontal bar chart with sensitivity impact ranking.

        Args:
            sensitivity_data: List of feature impact dictionaries.
        """
        self.ax.clear()
        self._set_dark_style()

        if not sensitivity_data:
            self.canvas.draw()
            return

        # Reverse list so top feature displays at top of horizontal plot
        items = list(reversed(sensitivity_data[:6]))
        names = [item["name"] for item in items]
        impacts = [item["impact"] for item in items]

        colors = ["#3b82f6" if imp >= 0 else "#ef4444" for imp in impacts]

        bars = self.ax.barh(names, impacts, color=colors, height=0.55, edgecolor="#1e293b")

        for bar in bars:
            width = bar.get_width()
            offset = 0.02 if width >= 0 else -0.05
            ha = "left" if width >= 0 else "right"
            self.ax.text(
                width + offset,
                bar.get_y() + bar.get_height() / 2.0,
                f"{width:+.2f}",
                va="center",
                ha=ha,
                color="#f8fafc",
                fontsize=8,
                fontweight="bold",
            )

        self.ax.set_xlabel("Mức thay đổi điểm số khi tăng chỉ số (+10% / +1 điểm)", color="#94a3b8", fontsize=8)
        self.ax.set_title("Phân Tích Độ Nhạy Các Biến Đòn Bẩy", color="#f8fafc", fontsize=10, fontweight="bold", pad=10)

        self.figure.tight_layout()
        self.canvas.draw()
