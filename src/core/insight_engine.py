"""
Insight Engine Module for generating deep, multi-dimensional pedagogical advice and What-If simulation.
Strictly adheres to Ethical Rules R-ETH-01 and R-ETH-03.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import joblib
import numpy as np
import pandas as pd

from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor


class InsightEngine:
    """Generates personalized student intervention advice and What-If scenarios."""

    ETHICAL_DISCLAIMER = (
        "Lưu ý: Hệ thống cung cấp dự báo và khuyến nghị tự động mang tính chất tham khảo sư phạm. "
        "Giảng viên phụ trách là người đưa ra quyết định tư vấn và hỗ trợ chính thức cho sinh viên."
    )

    RISK_LEVEL_LABELS = {
        1: "Rất thấp",
        2: "Thấp",
        3: "Trung bình",
        4: "Cao",
    }

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            models_dir = Path(__file__).resolve().parents[2] / "models"
        
        self.models_dir = models_dir
        self.preprocessor: Optional[DataPreprocessor] = None
        self.reg_model = None
        self.cls_model = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads trained ML models and preprocessor from disk."""
        preprocessor_path = self.models_dir / "preprocessor.pkl"
        reg_path = self.models_dir / "ridge_regression_model.pkl"
        cls_path = self.models_dir / "risk_classifier_model.pkl"

        if preprocessor_path.exists():
            self.preprocessor = joblib.load(preprocessor_path)
        if reg_path.exists():
            self.reg_model = joblib.load(reg_path)
        if cls_path.exists():
            self.cls_model = joblib.load(cls_path)

    def generate_student_advice(self, student_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates deep, multi-dimensional pedagogical intervention recommendations.

        Args:
            student_row: Dictionary of student attributes.

        Returns:
            Dict[str, Any]: Detailed risk diagnosis and 4-pillar intervention plan.
        """
        advice_adviser: List[str] = []
        advice_academic: List[str] = []
        advice_lms: List[str] = []
        advice_mental: List[str] = []
        root_causes: List[str] = []

        chuyen_can = float(student_row.get("chuyen_can", 100.0))
        nop_bai = float(student_row.get("nop_bai_dung_han", 100.0))
        diem_gk = float(student_row.get("diem_gk", 10.0))
        stress = int(student_row.get("muc_do_stress", 1))
        dong_luc = int(student_row.get("dong_luc_hoc", 5))
        lam_them = str(student_row.get("di_lam_them", "Không"))

        # Root Cause & Advice Generation
        if chuyen_can < 60.0:
            root_causes.append(f"Tỷ lệ điểm danh trên lớp rất thấp ({chuyen_can:.1f}%), đối mặt với nguy cơ cấm thi cuối kỳ.")
            advice_adviser.append("Cố vấn học tập gặp trực tiếp sinh viên trong tuần này để ký cam kết đi học đầy đủ các buổi còn lại.")
            advice_academic.append("Yêu cầu sinh viên chép lại bài giảng và hoàn thành bản tóm tắt kiến thức của các buổi vắng.")

        if nop_bai < 60.0:
            root_causes.append(f"Tỷ lệ nộp bài tập đúng hạn thấp ({nop_bai:.1f}%), thiếu tính kỷ luật học tập.")
            advice_lms.append("Đặt nhắc lịch deadline tự động trên hệ thống LMS và giao mốc hoàn thành bài tập bù trước 48 giờ.")

        if diem_gk < 5.0:
            root_causes.append(f"Điểm kiểm tra giữa kỳ chưa đạt chuẩn ({diem_gk:.1f}/10 điểm), bị hổng kiến thức nền tảng.")
            advice_academic.append("Phân công 1 sinh viên trong nhóm học tập xuất sắc hỗ trợ phụ đạo 1-1 các chủ đề giữa kỳ còn yếu.")
            advice_academic.append("Cung cấp bộ bài tập ôn luyện bổ trợ có đáp án chi tiết để sinh viên tự rèn luyện tại nhà.")

        if stress >= 4:
            root_causes.append("Mức độ áp lực tâm lý và căng thẳng ở ngưỡng cao (Mức 4-5).")
            advice_mental.append("Chuyển thông tin sinh viên tới Trung tâm Tư vấn Tâm lý Học đường để nhận trợ giúp chuyên môn.")

        if dong_luc <= 2:
            root_causes.append("Động lực và định hướng học tập chưa cao (Mức 1-2).")
            advice_adviser.append("Tư vấn định hướng nghề nghiệp, trao đổi về cơ hội việc làm chuyên ngành để khơi dậy mục tiêu học tập.")

        if lam_them == ">= 20h/tuần":
            root_causes.append("Thời gian làm thêm ngoài giờ nhiều (từ 20 giờ/tuần trở lên) ảnh hưởng tới quỹ thời gian tự học.")
            advice_mental.append("Tư vấn sinh viên cân đối thời gian giữa làm thêm và ưu tiên cho mục tiêu hoàn thành học phần.")

        if not advice_academic and not advice_adviser:
            advice_academic.append("Sinh viên duy trì thái độ học tập và kết quả tốt. Khuyến khích tham gia nghiên cứu khoa học hoặc trợ giảng.")

        risk_level_str = str(student_row.get("nguy_co_hoc_vu", "Thấp"))

        combined_advice = advice_adviser + advice_academic + advice_lms + advice_mental

        return {
            "ma_sv": student_row.get("ma_sv"),
            "ho_ten": student_row.get("ho_ten"),
            "nganh_hoc": student_row.get("nganh_hoc"),
            "nguy_co_hoc_vu": risk_level_str,
            "nguyen_nhan": root_causes,
            "khuyen_nghi_hanh_dong": combined_advice,
            "can_thiep_co_van": advice_adviser,
            "can_thiep_chuyen_mon": advice_academic,
            "can_thiep_lms": advice_lms,
            "can_thiep_tam_ly": advice_mental,
            "disclaimer": self.ETHICAL_DISCLAIMER,
        }

    def simulate_what_if(
        self, student_df: pd.DataFrame, chuyen_can_delta: float = 0.0, diem_gk_delta: float = 0.0
    ) -> Dict[str, Any]:
        """
        Simulates what-if scenario by modifying metrics and predicting changes.

        Args:
            student_df: Single-row DataFrame of student data.
            chuyen_can_delta: Proposed change in attendance %.
            diem_gk_delta: Proposed change in midterm score.

        Returns:
            Dict[str, Any]: Comparison of original vs simulated prediction.
        """
        if self.preprocessor is None or self.reg_model is None or self.cls_model is None:
            raise RuntimeError("ML Models not loaded properly.")

        # Baseline prediction
        fe_orig = FeatureEngineer.create_features(student_df)
        X_orig, _, _ = self.preprocessor.prepare_features(fe_orig)
        X_tr_orig = self.preprocessor.transform(X_orig)

        orig_score = float(self.reg_model.predict(X_tr_orig)[0])
        orig_risk_code = int(self.cls_model.predict(X_tr_orig)[0])
        orig_risk_label = self.RISK_LEVEL_LABELS.get(orig_risk_code, "Thấp")

        # Simulated prediction
        sim_df = student_df.copy()
        if "chuyen_can" in sim_df.columns:
            sim_df["chuyen_can"] = np.clip(sim_df["chuyen_can"] + chuyen_can_delta, 0.0, 100.0)
        if "diem_gk" in sim_df.columns:
            sim_df["diem_gk"] = np.clip(sim_df["diem_gk"] + diem_gk_delta, 0.0, 10.0)

        fe_sim = FeatureEngineer.create_features(sim_df)
        X_sim, _, _ = self.preprocessor.prepare_features(fe_sim)
        X_tr_sim = self.preprocessor.transform(X_sim)

        sim_score = float(self.reg_model.predict(X_tr_sim)[0])
        sim_risk_code = int(self.cls_model.predict(X_tr_sim)[0])
        sim_risk_label = self.RISK_LEVEL_LABELS.get(sim_risk_code, "Thấp")

        return {
            "diem_cu": round(orig_score, 2),
            "diem_moi": round(sim_score, 2),
            "chenh_lech_diem": round(sim_score - orig_score, 2),
            "nguy_co_cu": orig_risk_label,
            "nguy_co_moi": sim_risk_label,
            "cai_thien_nguy_co": orig_risk_label != sim_risk_label,
            "disclaimer": self.ETHICAL_DISCLAIMER,
        }
