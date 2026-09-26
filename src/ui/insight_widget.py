"""
Insight Widget providing student intervention recommendations and interactive What-If simulation.
Clean, professional corporate interface without emojis.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QSlider, QTextEdit, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt

from src.core.data_loader import DataLoader
from src.core.insight_engine import InsightEngine


class InsightWidget(QWidget):
    """Widget for browsing student intervention advice and running What-If scenario simulations."""

    def __init__(self):
        super().__init__()
        self.engine = InsightEngine()
        self.df = DataLoader.load_from_db()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        title = QLabel("Tư vấn Can thiệp Học vụ & Mô phỏng Giả định (What-If)")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        # Student Selector Dropdown
        lbl_select = QLabel("Chọn sinh viên cần phân tích:")
        lbl_select.setStyleSheet("font-weight: 600; font-size: 13px;")
        header.addWidget(lbl_select)

        self.cbo_student = QComboBox()
        self.cbo_student.setFixedWidth(300)
        self.cbo_student.currentIndexChanged.connect(self.on_student_changed)
        header.addWidget(self.cbo_student)

        layout.addLayout(header)

        # Main Split Layout
        content_layout = QHBoxLayout()

        # Left Panel: Advice & Diagnostic Intervention
        group_advice = QGroupBox("Báo cáo Chẩn đoán & Kế hoạch Can thiệp Sư phạm Chuyên sâu")
        advice_layout = QVBoxLayout(group_advice)

        self.txt_advice = QTextEdit()
        self.txt_advice.setReadOnly(True)
        self.txt_advice.setStyleSheet("background-color: #0b132b; color: #f8fafc; font-size: 13px; border: 1px solid #3a506b;")
        advice_layout.addWidget(self.txt_advice)

        content_layout.addWidget(group_advice, stretch=1)

        # Right Panel: Interactive What-If Simulator
        group_whatif = QGroupBox("Mô phỏng Giả định Tương tác (What-If Scenario)")
        whatif_layout = QVBoxLayout(group_whatif)

        grid_sliders = QGridLayout()

        # Attendance Change Slider
        lbl_cc = QLabel("Điều chỉnh Tăng Chuyên cần (%):")
        self.slider_cc = QSlider(Qt.Orientation.Horizontal)
        self.slider_cc.setRange(0, 30)
        self.slider_cc.setValue(0)
        self.lbl_cc_val = QLabel("+0.0%")
        self.lbl_cc_val.setStyleSheet("font-weight: bold; color: #48cae4;")
        self.slider_cc.valueChanged.connect(self.on_whatif_changed)

        grid_sliders.addWidget(lbl_cc, 0, 0)
        grid_sliders.addWidget(self.slider_cc, 0, 1)
        grid_sliders.addWidget(self.lbl_cc_val, 0, 2)

        # Midterm Score Change Slider
        lbl_gk = QLabel("Điều chỉnh Tăng Điểm Giữa Kỳ:")
        self.slider_gk = QSlider(Qt.Orientation.Horizontal)
        self.slider_gk.setRange(0, 30)
        self.slider_gk.setValue(0)
        self.lbl_gk_val = QLabel("+0.0 điểm")
        self.lbl_gk_val.setStyleSheet("font-weight: bold; color: #48cae4;")
        self.slider_gk.valueChanged.connect(self.on_whatif_changed)

        grid_sliders.addWidget(lbl_gk, 1, 0)
        grid_sliders.addWidget(self.slider_gk, 1, 1)
        grid_sliders.addWidget(self.lbl_gk_val, 1, 2)

        whatif_layout.addLayout(grid_sliders)

        # Simulation Results Card
        self.lbl_sim_result = QLabel("Kéo điều chỉnh thanh trượt phía trên để mô phỏng sự thay đổi điểm số và mức độ nguy cơ.")
        self.lbl_sim_result.setWordWrap(True)
        self.lbl_sim_result.setStyleSheet(
            "background-color: #0b132b; border: 1px solid #48cae4; border-radius: 6px; padding: 16px; font-size: 13px; color: #48cae4;"
        )
        whatif_layout.addWidget(self.lbl_sim_result)
        whatif_layout.addStretch()

        content_layout.addWidget(group_whatif, stretch=1)
        layout.addLayout(content_layout)

        self.populate_students()

    def populate_students(self):
        """Populates student selector combo box."""
        self.df = DataLoader.load_from_db()
        if self.df.empty:
            return

        self.cbo_student.blockSignals(True)
        self.cbo_student.clear()
        for _, row in self.df.iterrows():
            item_text = f"{row['ma_sv']} - {row['ho_ten']} (Nguy cơ: {row['nguy_co_hoc_vu']})"
            self.cbo_student.addItem(item_text, row['ma_sv'])
        self.cbo_student.blockSignals(False)

        if len(self.df) > 0:
            self.on_student_changed(0)

    def on_student_changed(self, index: int):
        """Triggers advice display when a student is selected."""
        if self.df.empty or index < 0:
            return

        student_row = self.df.iloc[index].to_dict()
        advice = self.engine.generate_student_advice(student_row)

        html = "<div style='font-family: Segoe UI, sans-serif;'>"
        html += f"<p><b>Mã sinh viên:</b> {advice['ma_sv']} | <b>Họ và tên:</b> {advice['ho_ten']}</p>"
        html += f"<p><b>Ngành học:</b> {advice.get('nganh_hoc', 'N/A')} | <b>Mức độ nguy cơ học vụ:</b> <span style='color: #f87171; font-weight: bold;'>{advice['nguy_co_hoc_vu']}</span></p><hr style='border: 1px solid #3a506b;'>"

        if advice['nguyen_nhan']:
            html += "<p><b>1. PHÂN TÍCH NGUYÊN NHÂN RỦI RO GỐC RỄ:</b></p><ul>"
            for cause in advice['nguyen_nhan']:
                html += f"<li style='color: #fbbf24;'>{cause}</li>"
            html += "</ul>"

        html += "<p><b>2. KẾ HOẠCH CAN THIỆP SƯ PHẠM CHI TIẾT:</b></p>"
        
        if advice['can_thiep_co_van']:
            html += "<p style='color: #48cae4;'><b>a) Công tác Cố vấn Học tập & Điểm danh:</b></p><ul>"
            for item in advice['can_thiep_co_van']:
                html += f"<li style='color: #5bc0be;'>{item}</li>"
            html += "</ul>"

        if advice['can_thiep_chuyen_mon']:
            html += "<p style='color: #48cae4;'><b>b) Hỗ trợ Chuyên môn & Phụ đạo Kiến thức:</b></p><ul>"
            for item in advice['can_thiep_chuyen_mon']:
                html += f"<li style='color: #5bc0be;'>{item}</li>"
            html += "</ul>"

        if advice['can_thiep_lms']:
            html += "<p style='color: #48cae4;'><b>c) Quản lý Kỷ luật Bài tập LMS:</b></p><ul>"
            for item in advice['can_thiep_lms']:
                html += f"<li style='color: #5bc0be;'>{item}</li>"
            html += "</ul>"

        if advice['can_thiep_tam_ly']:
            html += "<p style='color: #48cae4;'><b>d) Tư vấn Tâm lý & Cân đối Việc làm thêm:</b></p><ul>"
            for item in advice['can_thiep_tam_ly']:
                html += f"<li style='color: #5bc0be;'>{item}</li>"
            html += "</ul>"

        html += f"<br><p style='color: #94a3b8; font-size: 11px;'><i>{advice['disclaimer']}</i></p>"
        html += "</div>"

        self.txt_advice.setHtml(html)
        self.on_whatif_changed()

    def on_whatif_changed(self):
        """Computes and updates real-time What-If simulation."""
        idx = self.cbo_student.currentIndex()
        if self.df.empty or idx < 0:
            return

        cc_delta = float(self.slider_cc.value())
        gk_delta = float(self.slider_gk.value()) / 10.0

        self.lbl_cc_val.setText(f"+{cc_delta:.1f}%")
        self.lbl_gk_val.setText(f"+{gk_delta:.1f} điểm")

        student_df = self.df.iloc[[idx]]
        try:
            res = self.engine.simulate_what_if(student_df, chuyen_can_delta=cc_delta, diem_gk_delta=gk_delta)

            sim_html = "<div style='font-family: Segoe UI, sans-serif;'>"
            sim_html += "<b>KẾT QUẢ MÔ PHỎNG GIẢ ĐỊNH DỰ BÁO:</b><br><br>"
            sim_html += f"• Điểm tổng kết ban đầu: <b>{res['diem_cu']} điểm</b> ➔ Điểm dự báo mới: <b style='color:#5bc0be;'>{res['diem_moi']} điểm</b> "
            sim_html += f"(Mức tăng: <b style='color:#48cae4;'>+{res['chenh_lech_diem']} điểm</b>)<br>"
            sim_html += f"• Mức nguy cơ ban đầu: <b>{res['nguy_co_cu']}</b> ➔ Mức nguy cơ mới: <b style='color:#48cae4;'>{res['nguy_co_moi']}</b><br>"

            if res['cai_thien_nguy_co']:
                sim_html += "<br><span style='color:#5bc0be; font-weight:bold;'>Mức độ nguy cơ học vụ đã được cải thiện giảm xuống.</span>"

            sim_html += "</div>"
            self.lbl_sim_result.setText(sim_html)
        except Exception as e:
            self.lbl_sim_result.setText(f"Không thể tính toán mô phỏng: {str(e)}")
