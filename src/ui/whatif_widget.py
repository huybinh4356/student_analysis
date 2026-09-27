"""
Upgraded What-If Simulation Panel Widget (v2.0).
Features 7 interactive feature sliders, realtime Before/After comparison, colored deltas,
Matplotlib visual comparison bar chart, Sensitivity Analysis ranking chart, Goal-Oriented Reverse Solver,
and Scenario Manager for saving and comparing simulation options.
Enforces rules R-WHATIF-01 through R-WHATIF-08 and R-ETH-01.
"""

from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider,
    QGroupBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QMessageBox, QFrame, QDoubleSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
import pandas as pd

from src.core.whatif_engine import WhatIfEngine
from src.core.scenario_manager import ScenarioManager
from src.core.data_loader import DataLoader
from src.ui.charts.whatif_chart import WhatIfChartWidget
from src.ui.charts.sensitivity_chart import SensitivityChartWidget


class WhatIfWidget(QWidget):
    """
    Upgraded What-If simulation panel widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = WhatIfEngine()
        self.scenario_manager = ScenarioManager()
        self.students_df = pd.DataFrame()
        self.current_student = {}
        self.slider_controls: Dict[str, Dict[str, Any]] = {}

        self.init_ui()
        self.load_student_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Row: Title & Student Dropdown Selector
        top_layout = QHBoxLayout()
        title = QLabel("🔮 Mô Phỏng Giả Định Học Tập (What-If Simulation Engine)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        sel_lbl = QLabel("Chọn Sinh Viên:")
        sel_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        top_layout.addWidget(sel_lbl)

        self.combo_students = QComboBox()
        self.combo_students.setMinimumWidth(300)
        self.combo_students.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #3b82f6;
            }
        """)
        self.combo_students.currentIndexChanged.connect(self.on_student_selected)
        top_layout.addWidget(self.combo_students)

        main_layout.addLayout(top_layout)

        # Main Tabbed Interface
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
                padding: 8px 16px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)

        # Tab 1: ⚙️ Interactive Sliders & Realtime Simulation
        tab_sim = self._create_simulation_tab()
        self.tabs.addTab(tab_sim, "⚙️ Điều Chỉnh & Mô Phỏng")

        # Tab 2: 📈 Sensitivity Analysis (Độ Nhạy)
        tab_sens = self._create_sensitivity_tab()
        self.tabs.addTab(tab_sens, "📈 Phân Tích Độ Nhạy")

        # Tab 3: 🎯 Reverse What-If (Đạt Mục Tiêu)
        tab_rev = self._create_reverse_tab()
        self.tabs.addTab(tab_rev, "🎯 Reverse - Đạt Mục Tiêu")

        # Tab 4: 💾 Scenario Manager (Lưu & So Sánh)
        tab_scn = self._create_scenario_tab()
        self.tabs.addTab(tab_scn, "💾 Quản Lý Kịch Bản")

        main_layout.addWidget(self.tabs)

    def _create_simulation_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # LEFT COLUMN: 7 Sliders & Control Buttons
        left_box = QGroupBox("⚙️ ĐIỀU CHỈNH CHỈ SỐ HỌC TẬP (7 BIẾN ĐÒN BẨY)")
        left_box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        left_layout = QVBoxLayout(left_box)
        left_layout.setSpacing(10)

        scroll_sliders = QScrollArea()
        scroll_sliders.setWidgetResizable(True)
        scroll_sliders.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        sliders_container = QWidget()
        sliders_layout = QVBoxLayout(sliders_container)
        sliders_layout.setSpacing(12)

        for feat in WhatIfEngine.SLIDER_FEATURES:
            key = feat["key"]
            name = feat["name"]
            min_val = feat["min"]
            max_val = feat["max"]
            step = feat["step"]

            row_frame = QFrame()
            row_frame.setStyleSheet("QFrame { background-color: #0f172a; border-radius: 6px; padding: 8px; }")
            row_layout = QVBoxLayout(row_frame)
            row_layout.setSpacing(4)

            lbl_row = QHBoxLayout()
            lbl_title = QLabel(name)
            lbl_title.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 12px;")
            val_lbl = QLabel(f"{feat['default']}")
            val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")

            lbl_row.addWidget(lbl_title)
            lbl_row.addStretch()
            lbl_row.addWidget(val_lbl)
            row_layout.addLayout(lbl_row)

            slider = QSlider(Qt.Orientation.Horizontal)
            if isinstance(step, float) or step < 1:
                slider.setMinimum(int(min_val * 10))
                slider.setMaximum(int(max_val * 10))
                slider.setSingleStep(int(step * 10))
            else:
                slider.setMinimum(int(min_val))
                slider.setMaximum(int(max_val))
                slider.setSingleStep(int(step))

            slider.setValue(int(feat['default']))
            slider.valueChanged.connect(self.on_slider_changed)
            row_layout.addWidget(slider)

            sliders_layout.addWidget(row_frame)
            self.slider_controls[key] = {
                "slider": slider,
                "val_lbl": val_lbl,
                "is_float": isinstance(step, float) or step < 1,
                "feature": feat
            }

        scroll_sliders.setWidget(sliders_container)
        left_layout.addWidget(scroll_sliders)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        self.btn_reset = QPushButton("🔄 Reset Về Gốc")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setStyleSheet("QPushButton { background-color: #475569; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; } QPushButton:hover { background-color: #64748b; }")
        self.btn_reset.clicked.connect(self.reset_sliders_to_student_defaults)

        self.btn_save_scenario = QPushButton("💾 Lưu Kịch Bản")
        self.btn_save_scenario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_scenario.setStyleSheet("QPushButton { background-color: #10b981; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; } QPushButton:hover { background-color: #059669; }")
        self.btn_save_scenario.clicked.connect(self.save_current_scenario)

        btn_row.addWidget(self.btn_reset)
        btn_row.addWidget(self.btn_save_scenario)
        left_layout.addLayout(btn_row)

        layout.addWidget(left_box, stretch=4)

        # RIGHT COLUMN: Before/After Cards, Delta Badge, Chart, and Dynamic Advice
        right_box = QGroupBox("📊 KẾT QUẢ MÔ PHỎNG DỰ BÁO")
        right_box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)

        # Side-by-side Before/After Cards
        cards_row = QHBoxLayout()
        
        # Before Card
        self.card_before = QFrame()
        self.card_before.setStyleSheet("QFrame { background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; }")
        b_layout = QVBoxLayout(self.card_before)
        b_lbl = QLabel("TRƯỚC THAY ĐỔI")
        b_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.lbl_score_before = QLabel("7.00 điểm")
        self.lbl_score_before.setStyleSheet("color: #cbd5e1; font-size: 18px; font-weight: bold;")
        self.lbl_risk_before = QLabel("Nguy cơ: Thấp")
        self.lbl_risk_before.setStyleSheet("color: #94a3b8; font-size: 11px;")
        b_layout.addWidget(b_lbl)
        b_layout.addWidget(self.lbl_score_before)
        b_layout.addWidget(self.lbl_risk_before)
        cards_row.addWidget(self.card_before)

        # Delta Badge
        self.lbl_delta = QLabel("Δ 0.00 điểm")
        self.lbl_delta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_delta.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; font-size: 13px; padding: 6px 12px; border-radius: 16px;")
        cards_row.addWidget(self.lbl_delta)

        # After Card
        self.card_after = QFrame()
        self.card_after.setStyleSheet("QFrame { background-color: #0f172a; border: 1px solid #10b981; border-radius: 8px; padding: 10px; }")
        a_layout = QVBoxLayout(self.card_after)
        a_lbl = QLabel("SAU THAY ĐỔI")
        a_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.lbl_score_after = QLabel("7.00 điểm")
        self.lbl_score_after.setStyleSheet("color: #10b981; font-size: 18px; font-weight: bold;")
        self.lbl_risk_after = QLabel("Nguy cơ: Thấp")
        self.lbl_risk_after.setStyleSheet("color: #34d399; font-size: 11px;")
        a_layout.addWidget(a_lbl)
        a_layout.addWidget(self.lbl_score_after)
        a_layout.addWidget(self.lbl_risk_after)
        cards_row.addWidget(self.card_after)

        right_layout.addLayout(cards_row)

        # Visual Bar Comparison Chart Widget
        self.chart_widget = WhatIfChartWidget()
        right_layout.addWidget(self.chart_widget, stretch=1)

        # Dynamic Advice Text Box
        self.txt_advice = QTextEdit()
        self.txt_advice.setReadOnly(True)
        self.txt_advice.setMaximumHeight(110)
        self.txt_advice.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        right_layout.addWidget(self.txt_advice)

        layout.addWidget(right_box, stretch=5)
        return widget

    def _create_sensitivity_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Ranking Table
        left_box = QGroupBox("📋 BẢNG XẾP HẠNG TÁC ĐỘNG (SENSITIVITY RANKING)")
        left_box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        l_layout = QVBoxLayout(left_box)

        self.table_sens = QTableWidget()
        self.table_sens.setColumnCount(4)
        self.table_sens.setHorizontalHeaderLabels(["Hạng", "Biến Đòn Bẩy", "Độ Nhạy (+Δ)", "Mức Độ"])
        self.table_sens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_sens.setStyleSheet("QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; border: none; } QHeaderView::section { background-color: #1e293b; color: #cbd5e1; font-weight: bold; padding: 6px; }")
        l_layout.addWidget(self.table_sens)

        layout.addWidget(left_box, stretch=4)

        # Horizontal Sensitivity Bar Chart
        right_box = QGroupBox("📊 BIỂU ĐỒ ĐỘ NHẠY BIẾN ĐÒN BẨY")
        right_box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        r_layout = QVBoxLayout(right_box)

        self.chart_sensitivity = SensitivityChartWidget()
        r_layout.addWidget(self.chart_sensitivity)

        layout.addWidget(right_box, stretch=5)
        return widget

    def _create_reverse_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        box = QGroupBox("🎯 REVERSE WHAT-IF: TÌM ĐIỀU KIỆN TỐI THIỂU ĐỂ ĐẠT MỤC TIÊU")
        box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(12)

        # Input Row
        inp_row = QHBoxLayout()
        inp_lbl = QLabel("Nhập Điểm Mục Tiêu Mong Muốn (Hệ 10):")
        inp_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px;")
        inp_row.addWidget(inp_lbl)

        self.spin_target = QDoubleSpinBox()
        self.spin_target.setRange(0.0, 10.0)
        self.spin_target.setSingleStep(0.1)
        self.spin_target.setValue(8.0)
        self.spin_target.setStyleSheet("QDoubleSpinBox { background-color: #0f172a; color: #f8fafc; font-size: 14px; font-weight: bold; padding: 6px 12px; border: 1px solid #475569; border-radius: 6px; }")
        inp_row.addWidget(self.spin_target)

        self.btn_calc_reverse = QPushButton("🚀 Tính Toán Phương Án Optimal")
        self.btn_calc_reverse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calc_reverse.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px; } QPushButton:hover { background-color: #2563eb; }")
        self.btn_calc_reverse.clicked.connect(self.run_reverse_whatif)
        inp_row.addWidget(self.btn_calc_reverse)
        inp_row.addStretch()

        box_layout.addLayout(inp_row)

        # Output Results Area
        self.txt_reverse_result = QTextEdit()
        self.txt_reverse_result.setReadOnly(True)
        self.txt_reverse_result.setStyleSheet("QTextEdit { background-color: #0f172a; color: #f8fafc; border: 1px solid #334155; border-radius: 6px; padding: 12px; font-size: 13px; line-height: 1.5; }")
        box_layout.addWidget(self.txt_reverse_result)

        layout.addWidget(box)
        return widget

    def _create_scenario_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        box = QGroupBox("💾 DANH SÁCH KỊCH BẢN ĐÃ LƯU")
        box.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        box_layout = QVBoxLayout(box)

        self.table_scenarios = QTableWidget()
        self.table_scenarios.setColumnCount(6)
        self.table_scenarios.setHorizontalHeaderLabels(["ID Kịch Bản", "Tên Kịch Bản", "Mã SV", "Điểm Gốc", "Điểm Mô Phỏng", "Thay Đổi (Δ)"])
        self.table_scenarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_scenarios.setStyleSheet("QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; border: none; } QHeaderView::section { background-color: #1e293b; color: #cbd5e1; font-weight: bold; padding: 6px; }")
        box_layout.addWidget(self.table_scenarios)

        layout.addWidget(box)
        return widget

    def load_student_data(self):
        """Loads student data into dropdown combo box."""
        try:
            loader = DataLoader()
            self.students_df = loader.load_data()
        except Exception:
            self.students_df = pd.DataFrame()

        self.combo_students.blockSignals(True)
        self.combo_students.clear()

        if not self.students_df.empty:
            for _, row in self.students_df.iterrows():
                ma_sv = str(row.get("ma_sv", ""))
                ho_ten = str(row.get("ho_ten", ""))
                nganh = str(row.get("nganh_hoc", ""))
                self.combo_students.addItem(f"{ma_sv} - {ho_ten} ({nganh})", ma_sv)

        self.combo_students.blockSignals(False)

        if not self.students_df.empty:
            self.on_student_selected(0)

    def on_student_selected(self, index: int):
        """Handles student selection change from dropdown."""
        if self.students_df.empty or index < 0:
            return

        ma_sv = self.combo_students.currentData()
        matches = self.students_df[self.students_df["ma_sv"].astype(str) == str(ma_sv)]
        if matches.empty:
            return

        self.current_student = matches.iloc[0].to_dict()
        self.reset_sliders_to_student_defaults()
        self.run_sensitivity_analysis()

    def reset_sliders_to_student_defaults(self):
        """R-WHATIF-01: Sets all sliders default to student's actual values from DB."""
        if not self.current_student:
            return

        for key, ctrl in self.slider_controls.items():
            feat = ctrl["feature"]
            val = self.current_student.get(key, feat["default"])
            try:
                val_float = float(val)
            except (ValueError, TypeError):
                val_float = float(feat["default"])

            slider = ctrl["slider"]
            slider.blockSignals(True)
            if ctrl["is_float"]:
                slider.setValue(int(val_float * 10))
            else:
                slider.setValue(int(val_float))
            slider.blockSignals(False)

            ctrl["val_lbl"].setText(f"{val_float:.1f}" if ctrl["is_float"] else f"{int(val_float)}")

        self.update_simulation_results()

    def on_slider_changed(self):
        """Handles realtime slider dragging (< 200ms update)."""
        # Update display label for each control
        for key, ctrl in self.slider_controls.items():
            slider = ctrl["slider"]
            val = slider.value() / 10.0 if ctrl["is_float"] else float(slider.value())
            ctrl["val_lbl"].setText(f"{val:.1f}" if ctrl["is_float"] else f"{int(val)}")

        self.update_simulation_results()

    def get_current_slider_changes(self) -> Dict[str, float]:
        """Reads current values from all 7 sliders."""
        changes = {}
        for key, ctrl in self.slider_controls.items():
            slider = ctrl["slider"]
            val = slider.value() / 10.0 if ctrl["is_float"] else float(slider.value())
            changes[key] = val
        return changes

    def update_simulation_results(self):
        """Calculates prediction for current slider values and updates cards, chart, & advice."""
        if not self.current_student:
            return

        orig_score = self.engine.predict_score(self.current_student)
        orig_risk, orig_color = self.engine.predict_risk(orig_score)

        changes = self.get_current_slider_changes()
        sim_score = self.engine.predict_score(self.current_student, changes)
        sim_risk, sim_color = self.engine.predict_risk(sim_score)

        delta = sim_score - orig_score

        # Update cards
        self.lbl_score_before.setText(f"{orig_score:.2f} điểm")
        self.lbl_risk_before.setText(f"Nguy cơ: {orig_risk}")

        self.lbl_score_after.setText(f"{sim_score:.2f} điểm")
        self.lbl_risk_after.setText(f"Nguy cơ: {sim_risk}")
        self.lbl_risk_after.setStyleSheet(f"color: {sim_color}; font-size: 11px;")

        # Update Delta badge
        if delta > 0.01:
            self.lbl_delta.setText(f"Δ +{delta:.2f} điểm 🟢")
            self.lbl_delta.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 6px 12px; border-radius: 16px;")
        elif delta < -0.01:
            self.lbl_delta.setText(f"Δ {delta:.2f} điểm 🔴")
            self.lbl_delta.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; font-size: 13px; padding: 6px 12px; border-radius: 16px;")
        else:
            self.lbl_delta.setText(f"Δ {delta:.2f} điểm ⚪")
            self.lbl_delta.setStyleSheet("background-color: #475569; color: white; font-weight: bold; font-size: 13px; padding: 6px 12px; border-radius: 16px;")

        # Update Chart
        self.chart_widget.update_chart(orig_score, sim_score)

        # Update Dynamic Advice
        advice = self.engine.generate_advice(self.current_student, changes, orig_score, sim_score)
        self.txt_advice.setMarkdown(advice)

    def run_sensitivity_analysis(self):
        """Runs sensitivity analysis ranking and updates ranking table & chart."""
        if not self.current_student:
            return

        sens_data = self.engine.sensitivity_analysis(self.current_student)

        # Update table
        self.table_sens.setRowCount(0)
        for i, item in enumerate(sens_data, 1):
            self.table_sens.insertRow(self.table_sens.rowCount())
            self.table_sens.setItem(self.table_sens.rowCount() - 1, 0, QTableWidgetItem(f"#{i}"))
            self.table_sens.setItem(self.table_sens.rowCount() - 1, 1, QTableWidgetItem(item["name"]))
            self.table_sens.setItem(self.table_sens.rowCount() - 1, 2, QTableWidgetItem(f"+{item['impact']:.2f}"))
            self.table_sens.setItem(self.table_sens.rowCount() - 1, 3, QTableWidgetItem(item["stars"]))

        # Update chart
        self.chart_sensitivity.update_chart(sens_data)

    def run_reverse_whatif(self):
        """Executes goal-oriented reverse solver."""
        if not self.current_student:
            return

        target_score = self.spin_target.value()
        res = self.engine.reverse_whatif(self.current_student, target_score)

        lines = [
            f"<b>🎯 MỤC TIÊU ĐIỂM SỐ: <span style='color: #f59e0b;'>{target_score:.2f} điểm</span></b>",
            f"• Điểm hiện tại của sinh viên: <b>{res['current_score']:.2f} điểm</b>",
            f"• Điểm ước tính đạt được: <b><span style='color: #10b981;'>{res.get('achieved_score', res['current_score']):.2f} điểm</span></b>",
            f"• Trạng thái khả thi: <b>{'🟢 Khả thi' if res['achievable'] else '🟠 Cần nỗ lực tối đa'}</b>",
            f"<br><b>💡 PHƯƠNG ÁN ĐIỀU CHỈNH CHỈ SỐ TỐI THIỂU:</b>",
        ]

        if res["changes"]:
            for key, info in res["changes"].items():
                lines.append(f"   • <b>{info['name']}</b>: Tăng từ <code>{info['from']}</code> ➔ <code>{info['to']}</code> (<span style='color: #38bdf8;'>+{info['increase']}</span>)")
        else:
            lines.append("   • Không cần thay đổi chỉ số nào.")

        lines.append(f"\n<i>{res['message']}</i>")
        self.txt_reverse_result.setHtml("<br>".join(lines))

    def save_current_scenario(self):
        """Saves current simulation scenario to ScenarioManager."""
        if not self.current_student:
            return

        ma_sv = str(self.current_student.get("ma_sv", "SV"))
        ho_ten = str(self.current_student.get("ho_ten", "Sinh viên"))
        orig_score = self.engine.predict_score(self.current_student)
        changes = self.get_current_slider_changes()
        sim_score = self.engine.predict_score(self.current_student, changes)
        advice = self.engine.generate_advice(self.current_student, changes, orig_score, sim_score)

        name = f"Kịch bản {ma_sv} (+{sim_score - orig_score:.2f})"
        scn = self.scenario_manager.save_scenario(name, ma_sv, ho_ten, orig_score, sim_score, changes, advice)

        self.update_scenarios_table()
        QMessageBox.information(self, "Lưu Thành Công", f"Đã lưu kịch bản {scn.id} vào danh sách so sánh!")

    def update_scenarios_table(self):
        """Refreshes scenario comparison table."""
        scenarios = self.scenario_manager.get_all_scenarios()
        self.table_scenarios.setRowCount(0)

        for s in scenarios:
            row = self.table_scenarios.rowCount()
            self.table_scenarios.insertRow(row)
            self.table_scenarios.setItem(row, 0, QTableWidgetItem(s.id))
            self.table_scenarios.setItem(row, 1, QTableWidgetItem(s.name))
            self.table_scenarios.setItem(row, 2, QTableWidgetItem(s.student_id))
            self.table_scenarios.setItem(row, 3, QTableWidgetItem(f"{s.original_score:.2f}"))
            self.table_scenarios.setItem(row, 4, QTableWidgetItem(f"{s.simulated_score:.2f}"))
            self.table_scenarios.setItem(row, 5, QTableWidgetItem(f"{s.delta:+.2f}"))
