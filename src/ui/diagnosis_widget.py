"""
Student Diagnosis & Missing Data Warning Panel Widget.
Provides student-level missing data inspection, 3-tier severity warnings (Critical, Warning, Info),
prediction confidence score calculation, and actionable pedagogical recommendations.
Complies strictly with R-ETH-01 (uses "có nguy cơ", never "sẽ rớt").
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QGroupBox,
    QProgressBar, QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt
import pandas as pd

from src.core.missing_detector import MissingDetector, MissingField
from src.core.whatif_engine import WhatIfEngine
from src.core.data_loader import DataLoader


class DiagnosisWidget(QWidget):
    """
    Panel widget for diagnosing individual student data health and prediction confidence.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.missing_detector = MissingDetector()
        self.whatif_engine = WhatIfEngine()
        self.students_df = pd.DataFrame()
        self.current_student = {}

        self.init_ui()
        self.load_student_list()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header & Student Selector Row
        top_layout = QHBoxLayout()
        title = QLabel("Báo Cáo Chẩn Đoán Dữ Liệu & Độ Tin Cậy Sinh Viên")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        sel_lbl = QLabel("Chọn Sinh Viên:")
        sel_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold;")
        top_layout.addWidget(sel_lbl)

        self.combo_students = QComboBox()
        self.combo_students.setMinimumWidth(280)
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
        self.combo_students.currentIndexChanged.connect(self.on_student_changed)
        top_layout.addWidget(self.combo_students)

        main_layout.addLayout(top_layout)

        # Scrollable Content Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(16)
        scroll.setWidget(container)

        main_layout.addWidget(scroll)

    def load_student_list(self):
        """Loads student records into dropdown combo box."""
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
            self.on_student_changed(0)

    def on_student_changed(self, index: int):
        """Handles student selection change."""
        if self.students_df.empty or index < 0:
            return

        ma_sv = self.combo_students.currentData()
        matches = self.students_df[self.students_df["ma_sv"].astype(str) == str(ma_sv)]
        if matches.empty:
            return

        self.current_student = matches.iloc[0].to_dict()
        self.render_diagnosis()

    def render_diagnosis(self):
        """Renders diagnostic report cards for selected student."""
        # Clear previous items
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        st = self.current_student
        predicted_score = self.whatif_engine.predict_score(st)
        risk_label, risk_color = self.whatif_engine.predict_risk(predicted_score)

        missing_fields = self.missing_detector.detect_for_student(st)
        confidence = self.missing_detector.calculate_confidence_penalty(missing_fields)

        # 1. Student Profile Summary Card
        card_profile = QFrame()
        card_profile.setStyleSheet("QFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px; }")
        layout_prof = QHBoxLayout(card_profile)

        info_text = f"""
            <div style='color: #f8fafc; font-size: 14px;'>
                <b style='font-size: 16px;'>👤 {st.get('ho_ten', 'N/A')}</b> (Mã SV: <span style='color: #38bdf8;'>{st.get('ma_sv', 'N/A')}</span>)<br>
                <span>Ngành: <b>{st.get('nganh_hoc', 'N/A')}</b> | Quê quán: {st.get('que_quan', 'N/A')}</span><br>
                <span>Điểm dự đoán tổng kết: <b style='color: #f59e0b; font-size: 15px;'>{predicted_score:.2f} điểm</b></span>
            </div>
        """
        lbl_info = QLabel(info_text)
        layout_prof.addWidget(lbl_info)
        layout_prof.addStretch()

        # Risk badge
        lbl_risk = QLabel(f"Mức nguy cơ: {risk_label}")
        lbl_risk.setStyleSheet(f"background-color: {risk_color}; color: white; font-weight: bold; font-size: 13px; padding: 8px 16px; border-radius: 6px;")
        layout_prof.addWidget(lbl_risk)

        self.content_layout.addWidget(card_profile)

        # 2. Prediction Confidence Score Bar
        group_conf = QGroupBox("📊 ĐỘ TIN CẬY DỰ ĐOÁN (PREDICTION CONFIDENCE SCORE)")
        group_conf.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_conf = QVBoxLayout(group_conf)

        conf_bar = QProgressBar()
        conf_bar.setValue(int(confidence))
        conf_bar.setFormat(f"Độ tin cậy: {confidence:.1f}%")
        conf_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if confidence >= 80:
            bar_color = "#10b981"
        elif confidence >= 60:
            bar_color = "#f59e0b"
        else:
            bar_color = "#ef4444"

        conf_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #475569;
                border-radius: 6px;
                background-color: #0f172a;
                color: white;
                font-weight: bold;
                height: 24px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 5px;
            }}
        """)
        layout_conf.addWidget(conf_bar)

        if confidence < 100:
            lbl_conf_note = QLabel(f"• Độ tin cậy giảm {100 - confidence:.1f}% do thiếu hoặc suy giảm các chỉ số dữ liệu đầu vào.")
            lbl_conf_note.setStyleSheet("color: #cbd5e1; font-size: 12px; margin-top: 4px;")
            layout_conf.addWidget(lbl_conf_note)

        self.content_layout.addWidget(group_conf)

        # 3. Categorized Missing Data Warnings (Critical, Warning, Info)
        group_warn = QGroupBox("⚠️ CẢNH BÁO DỮ LIỆU KHUYẾT THIẾU & BẤT THƯỜNG")
        group_warn.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_warn = QVBoxLayout(group_warn)

        if not missing_fields:
            lbl_clean = QLabel("Dữ liệu sinh viên đầy đủ 100%. Không phát hiện trường bị thiếu hay bất thường.")
            lbl_clean.setStyleSheet("color: #34d399; font-size: 13px; font-weight: bold;")
            layout_warn.addWidget(lbl_clean)
        else:
            # Group by severity
            crits = [m for m in missing_fields if m.severity == "critical"]
            warns = [m for m in missing_fields if m.severity == "warning"]
            infos = [m for m in missing_fields if m.severity == "info"]

            if crits:
                lbl_c_header = QLabel(f"🔴 NGHIÊM TRỌNG ({len(crits)} trường):")
                lbl_c_header.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")
                layout_warn.addWidget(lbl_c_header)
                for item in crits:
                    lbl = QLabel(f"   • <b>{item.display_name}</b>: {item.reason}<br>&nbsp;&nbsp;&nbsp;&nbsp;➔ <i>Khuyến nghị: {item.suggestion}</i>")
                    lbl.setStyleSheet("color: #fca5a5; font-size: 12px; margin-bottom: 6px;")
                    layout_warn.addWidget(lbl)

            if warns:
                lbl_w_header = QLabel(f"🟠 CẢNH BÁO ({len(warns)} trường):")
                lbl_w_header.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 13px; margin-top: 6px;")
                layout_warn.addWidget(lbl_w_header)
                for item in warns:
                    lbl = QLabel(f"   • <b>{item.display_name}</b>: {item.reason}<br>&nbsp;&nbsp;&nbsp;&nbsp;➔ <i>Khuyến nghị: {item.suggestion}</i>")
                    lbl.setStyleSheet("color: #fcd34d; font-size: 12px; margin-bottom: 6px;")
                    layout_warn.addWidget(lbl)

            if infos:
                lbl_i_header = QLabel(f"🟡 THÔNG TIN BỔ SUNG ({len(infos)} trường):")
                lbl_i_header.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px; margin-top: 6px;")
                layout_warn.addWidget(lbl_i_header)
                for item in infos:
                    lbl = QLabel(f"   • <b>{item.display_name}</b>: {item.reason}<br>&nbsp;&nbsp;&nbsp;&nbsp;➔ <i>Khuyến nghị: {item.suggestion}</i>")
                    lbl.setStyleSheet("color: #93c5fd; font-size: 12px; margin-bottom: 6px;")
                    layout_warn.addWidget(lbl)

        self.content_layout.addWidget(group_warn)

        # 4. Actionable Pedagogical Intervention Recommendations
        group_rec = QGroupBox("💡 HÀNH ĐỘNG CAN THIỆP & TƯ VẤN KHUYẾN NGHỊ FOR GIẢNG VIÊN")
        group_rec.setStyleSheet("QGroupBox { font-weight: bold; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; padding-top: 16px; background-color: #1e293b; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }")
        layout_rec = QVBoxLayout(group_rec)

        recommendations = []
        if missing_fields:
            recommendations.append("Ưu tiên thu thập bổ sung điểm số các bài kiểm tra còn thiếu để cập nhật độ tin cậy dự báo.")

        if predicted_score < 5.0:
            recommendations.append("Hỗ trợ đăng ký lớp học phụ đạo môn và sắp xếp sinh viên hỗ trợ học tập cặp đôi (Peer Tutoring).")
            recommendations.append("Gửi thông báo nhắc nhở chuyên cần và liên hệ cố vấn học tập lớp để phối hợp theo dõi.")
        elif predicted_score < 6.5:
            recommendations.append("Động viên sinh viên gia tăng thời lượng học tập LMS và làm lại các bài tập trắc nghiệm ôn luyện.")
        else:
            recommendations.append("Duy trì phong độ học tập hiện tại, khuyến khích tham gia các bài tập nhóm nâng cao.")

        for i, rec in enumerate(recommendations, 1):
            lbl = QLabel(f"{i}. {rec}")
            lbl.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4;")
            layout_rec.addWidget(lbl)

        lbl_disclaimer = QLabel("\n*Lưu ý: Hệ thống cung cấp cảnh báo tự động hỗ trợ giảng viên tham khảo. Quyết định can thiệp cuối cùng thuộc về giảng viên.*")
        lbl_disclaimer.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout_rec.addWidget(lbl_disclaimer)

        self.content_layout.addWidget(group_rec)
