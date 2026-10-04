"""
Report Widget for configuring and generating automated PDF/HTML student performance reports.
Allows lecturers to dynamically select which sections to include in the exported report.
Clean corporate interface without ASCII divider lines or emojis.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QTextEdit, QCheckBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt

from src.core.data_loader import DataLoader
from src.core.schema_detector import SchemaDetector


class ReportWidget(QWidget):
    """Widget for exporting custom summary analysis and student intervention reports."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        header_text = QVBoxLayout()

        title = QLabel("Xuất Báo cáo Tùy chọn & Thống kê Tự động")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Tùy chọn chọn các mục nội dung cần thiết và xuất báo cáo dưới dạng PDF hoặc HTML.")
        subtitle.setObjectName("sectionSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        self.btn_export_html = QPushButton("Xuất Báo cáo HTML/PDF")
        self.btn_export_html.setObjectName("primary-btn")
        self.btn_export_html.clicked.connect(self.export_html_report)
        header.addWidget(self.btn_export_html)

        layout.addLayout(header)

        # Section Selector Checkboxes GroupBox
        group_select = QGroupBox("Tùy chọn Nội dung Báo cáo Xuất ra")
        grid_cb = QGridLayout(group_select)

        self.chk_summary = QCheckBox("1. Thống kê Tổng quan & Tỷ lệ Rủi ro Học vụ")
        self.chk_models = QCheckBox("2. Bảng So sánh Hiệu năng Mô hình Machine Learning")
        self.chk_high_risk = QCheckBox("3. Danh sách Sinh viên Nguy cơ Cao cần Can thiệp Gấp")
        self.chk_guidance = QCheckBox("4. Khuyến nghị & Lộ trình Can thiệp Sư phạm")

        self.checkboxes = [self.chk_summary, self.chk_models, self.chk_high_risk, self.chk_guidance]
        for idx, cb in enumerate(self.checkboxes):
            cb.setChecked(True)
            cb.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 500;")
            cb.stateChanged.connect(self.generate_preview)
            grid_cb.addWidget(cb, idx // 2, idx % 2)

        layout.addWidget(group_select)

        # HTML Preview Area
        lbl_preview = QLabel("Bản xem trước Báo cáo (Preview):")
        lbl_preview.setStyleSheet("font-weight: bold; color: #48cae4; font-size: 13px; margin-top: 6px;")
        layout.addWidget(lbl_preview)

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("background-color: #0b132b; color: #f8fafc; font-size: 13px; border: 1px solid #3a506b; padding: 12px;")
        layout.addWidget(self.txt_preview)

        self.generate_preview()

    def generate_preview(self):
        """Generates clean HTML summary report text preview without ASCII dividers."""
        try:
            df = DataLoader.load_from_db()
            if df.empty:
                self.txt_preview.setHtml("<p>Chưa có dữ liệu sinh viên trong Database.</p>")
                return

            html = "<div style='font-family: Segoe UI, sans-serif; color: #f8fafc; line-height: 1.5;'>"
            html += "<h2 style='color: #48cae4; text-align: center; margin-bottom: 4px;'>BÁO CÁO TỔNG HỢP KẾT QUẢ DỰ BÁO VÀ PHÂN TÍCH RỦI RO HỌC VỤ</h2>"
            html += f"<p style='text-align: center; color: #94a3b8; font-size: 12px;'>Hệ thống Phân tích Học phần Sinh viên | Tổng số bản ghi: {len(df):,} sinh viên</p><br>"

            # Section 1: Summary & Risk Proportions
            if self.chk_summary.isChecked():
                html += "<h3 style='color: #48cae4; border-bottom: 1px solid #3a506b; padding-bottom: 4px;'>1. Thống kê Tổng quan & Tỷ lệ Rủi ro Học vụ</h3>"
                html += f"<p>• Tổng số sinh viên theo dõi: <b>{len(df):,} sinh viên</b></p>"
                html += "<p>• Phân bố mức độ nguy cơ học vụ:</p><ul>"
                
                risk_counts = df['nguy_co_hoc_vu'].value_counts()
                for k in ["Rất thấp", "Thấp", "Trung bình", "Cao"]:
                    v = risk_counts.get(k, 0)
                    pct = (v / len(df)) * 100
                    color = "#f87171" if k == "Cao" else ("#fbbf24" if k == "Trung bình" else "#5bc0be")
                    html += f"<li>Mức <b style='color: {color};'>{k}</b>: {v} sinh viên ({pct:.1f}%)</li>"
                html += "</ul>"

                html += "<p>• Điểm số và tỷ lệ trung bình học phần:</p><ul>"
                html += f"<li>Điểm THPT Trung bình: <b>{df['diem_thpt'].mean():.2f} điểm</b></li>"
                html += f"<li>Điểm Giữa kỳ Trung bình: <b>{df['diem_gk'].mean():.2f} điểm</b></li>"
                html += f"<li>Tỷ lệ Chuyên cần Trung bình: <b>{df['chuyen_can'].mean():.2f}%</b></li>"
                html += f"<li>Điểm Tổng kết Thực tế TB: <b>{df['diem_tong_ket'].mean():.2f} điểm</b></li></ul>"

            # Section 2: ML Model Metrics (Dynamic from ModelRegistry - REPORT-001)
            if self.chk_models.isChecked():
                from src.core.model_registry import ModelRegistry
                reg_data = ModelRegistry().get_registry_data()
                reg_info = reg_data.get("regression", {})
                cls_info = reg_data.get("classification", {})

                html += "<h3 style='color: #48cae4; border-bottom: 1px solid #3a506b; padding-bottom: 4px;'>2. Bảng Hiệu năng Mô hình Machine Learning (Thực tế)</h3>"

                # Regression metrics
                if reg_info and "cv_metrics" in reg_info and "test_metrics" in reg_info:
                    reg_name = reg_info.get("model_name", "Regression Model")
                    reg_test = reg_info.get("test_metrics", {})
                    reg_cv = reg_info.get("cv_metrics", {})
                    cv_r2 = reg_cv.get("cv_r2_mean")
                    test_r2 = reg_test.get("r2")
                    test_mae = reg_test.get("mae")
                    test_rmse = reg_test.get("rmse")

                    if cv_r2 is not None and test_r2 is not None:
                        html += f"<p>• <b>Mô hình Hồi quy Điểm số ({reg_name})</b>: 5-Fold CV R² = <b>{cv_r2*100:.2f}%</b>, Test R² = <b>{test_r2*100:.2f}%</b>, Test MAE = <b>±{test_mae:.2f} điểm</b>, Test RMSE = <b>{test_rmse:.2f}</b>.</p>"
                    else:
                        html += "<p style='color: #fbbf24;'>• <i>Chưa có đầy đủ kết quả đánh giá mô hình Hồi quy từ artifact.</i></p>"
                else:
                    html += "<p style='color: #fbbf24;'>• <i>Chưa có kết quả đánh giá mô hình Hồi quy. Vui lòng thực hiện Huấn luyện Mô hình.</i></p>"

                # Classification metrics
                if cls_info and "cv_metrics" in cls_info and "test_metrics" in cls_info:
                    cls_name = cls_info.get("model_name", "Classifier Model")
                    cls_test = cls_info.get("test_metrics", {})
                    cls_cv = cls_info.get("cv_metrics", {})
                    cv_f1 = cls_cv.get("cv_f1_macro_mean")
                    test_acc = cls_test.get("accuracy")
                    test_f1 = cls_test.get("f1_macro")
                    recall_high = cls_test.get("recall_high_risk")

                    if cv_f1 is not None and test_acc is not None:
                        html += f"<p>• <b>Mô hình Phân loại Rủi ro ({cls_name})</b>: 5-Fold CV Macro F1 = <b>{cv_f1:.3f}</b>, Test Accuracy = <b>{test_acc*100:.1f}%</b>, Test Macro F1 = <b>{test_f1:.3f}</b>, Recall Nhóm Nguy cơ Cao = <b>{recall_high*100:.1f}%</b>.</p>"
                    else:
                        html += "<p style='color: #fbbf24;'>• <i>Chưa có đầy đủ kết quả đánh giá mô hình Phân loại từ artifact.</i></p>"
                else:
                    html += "<p style='color: #fbbf24;'>• <i>Chưa có kết quả đánh giá mô hình Phân loại. Vui lòng thực hiện Huấn luyện Mô hình.</i></p>"

            # Section 3: High Risk Student List
            if self.chk_high_risk.isChecked():
                html += "<h3 style='color: #48cae4; border-bottom: 1px solid #3a506b; padding-bottom: 4px;'>3. Danh sách Sinh viên Nguy cơ Cao cần Can thiệp Gấp</h3>"
                high_risk_df = df[df['nguy_co_hoc_vu'] == 'Cao'].head(10)
                if not high_risk_df.empty:
                    html += "<table border='1' cellspacing='0' cellpadding='6' style='border-color: #3a506b; width: 100%; text-align: center; color: #f8fafc;'>"
                    html += "<tr style='background-color: #1c2541; color: #48cae4;'><th>Mã SV</th><th>Họ và Tên</th><th>Ngành Học</th><th>Chuyên Cần</th><th>Điểm GK</th><th>Nguy Cơ</th></tr>"
                    for _, row in high_risk_df.iterrows():
                        html += f"<tr><td>{row['ma_sv']}</td><td>{row['ho_ten']}</td><td>{row['nganh_hoc']}</td><td>{row['chuyen_can']:.1f}%</td><td>{row['diem_gk']:.1f}</td><td style='color: #f87171; font-weight: bold;'>{row['nguy_co_hoc_vu']}</td></tr>"
                    html += "</table>"
                else:
                    html += "<p>Không có sinh viên thuộc nhóm nguy cơ Cao.</p>"

            # Section 4: Pedagogical Guidance
            if self.chk_guidance.isChecked():
                html += "<h3 style='color: #48cae4; border-bottom: 1px solid #3a506b; padding-bottom: 4px;'>4. Khuyến nghị Can thiệp Sư phạm Trọng tâm</h3>"
                html += "<ul>"
                html += f"<li>Tập trung cố vấn 1-1 cho nhóm {risk_counts.get('Cao', 0)} sinh viên có nguy cơ Cao để ký cam kết đi học.</li>"
                html += "<li>Tổ chức các buổi phụ đạo bài tập giữa kỳ trên LMS cho nhóm sinh viên có điểm giữa kỳ chưa đạt.</li>"
                html += "<li>Hỗ trợ tâm lý học đường cho sinh viên có chỉ số Stress ở ngưỡng cao (Mức 4-5).</li>"
                html += "</ul>"

            html += "<br><p style='color: #94a3b8; font-size: 11px; font-style: italic;'>Tuyên bố Đạo đức: Báo cáo này được tự động tổng hợp từ hệ thống Machine Learning hỗ trợ Giảng viên tham khảo ra quyết định sư phạm.</p>"
            html += "</div>"

            self.txt_preview.setHtml(html)
        except Exception as e:
            self.txt_preview.setHtml(f"<p style='color: #f87171;'>Lỗi tạo xem trước báo cáo: {str(e)}</p>")

    def export_html_report(self):
        """Exports report file to HTML/PDF format."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu Báo cáo", "Bao_Cao_Phan_Tich_Ket_Qua_Hoc_Tap.html", "HTML Files (*.html);;Text Files (*.txt)"
        )
        if not file_path:
            return

        try:
            with open(Path(file_path), "w", encoding="utf-8") as f:
                f.write(self.txt_preview.toHtml())

            QMessageBox.information(
                self, "Thành công", f"Đã xuất báo cáo tổng hợp thành công tại:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Xuất File", f"Không thể xuất báo cáo: {str(e)}")
