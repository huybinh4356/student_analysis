"""
What-If simulation engine for interactive student score prediction,
sensitivity analysis, reverse target solver, and dynamic action advice generation.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
import pandas as pd

from src.core.schema_detector import SchemaDetector


class WhatIfEngine:
    """
    Engine for real-time What-If scenario simulations, feature sensitivity ranking,
    and goal-oriented reverse solver.
    """

    SLIDER_FEATURES = [
        {"key": "chuyen_can", "name": "Chuyên Cần (%)", "min": 0, "max": 100, "step": 1, "default": 80},
        {"key": "nop_bai_dung_han", "name": "Nộp Bài Đúng Hạn (%)", "min": 0, "max": 100, "step": 1, "default": 85},
        {"key": "diem_gk", "name": "Điểm Giữa Kỳ (Hệ 10)", "min": 0.0, "max": 10.0, "step": 0.1, "default": 7.0},
        {"key": "diem_quiz", "name": "Điểm Quiz (Hệ 10)", "min": 0.0, "max": 10.0, "step": 0.1, "default": 6.5},
        {"key": "diem_bai_tap", "name": "Điểm Bài Tập (Hệ 10)", "min": 0.0, "max": 10.0, "step": 0.1, "default": 7.5},
        {"key": "lms_gio_truy_cap", "name": "Giờ Truy Cập LMS", "min": 0, "max": 300, "step": 1, "default": 50},
        {"key": "muc_do_stress", "name": "Mức Độ Stress (1-5)", "min": 1, "max": 5, "step": 1, "default": 2},
    ]

    def __init__(self, models_dir: Path = None):
        if models_dir is None:
            models_dir = Path(__file__).resolve().parents[2] / "models"

        self.models_dir = models_dir
        self.regression_model = None
        self.classifier_model = None
        self.preprocessor = None
        self.feature_names = None

        self._load_artifacts()

    def _load_artifacts(self):
        """Loads trained ML model artifacts from models directory."""
        reg_path = self.models_dir / "ridge_regression_model.pkl"
        cls_path = self.models_dir / "risk_classifier_model.pkl"
        prep_path = self.models_dir / "preprocessor.pkl"
        feat_path = self.models_dir / "feature_names.pkl"

        if reg_path.exists():
            self.regression_model = joblib.load(reg_path)
        if cls_path.exists():
            self.classifier_model = joblib.load(cls_path)
        if prep_path.exists():
            self.preprocessor = joblib.load(prep_path)
        if feat_path.exists():
            self.feature_names = joblib.load(feat_path)

    def _prepare_single_row_df(self, student_data: Dict[str, Any], changes: Dict[str, Any] = None) -> pd.DataFrame:
        """Prepares a single-row DataFrame with applied modifications."""
        data = student_data.copy()
        if changes:
            data.update(changes)

        df_single = pd.DataFrame([data])
        # Ensure all required features are present
        for col in SchemaDetector.NUMERIC_COLS:
            if col not in df_single.columns:
                df_single[col] = 5.0

        for col in SchemaDetector.NOMINAL_COLS:
            if col not in df_single.columns:
                df_single[col] = "Chưa rõ"

        for col, mapping in SchemaDetector.ORDINAL_MAPPINGS.items():
            if col not in df_single.columns:
                df_single[col] = "Trung bình"

        return df_single

    def predict_score(self, student_data: Dict[str, Any], changes: Dict[str, Any] = None) -> float:
        """
        Predicts final score given student data and applied feature changes.

        Args:
            student_data: Base student attributes.
            changes: Feature slider modifications.

        Returns:
            float: Predicted final score (0.0 to 10.0).
        """
        df_single = self._prepare_single_row_df(student_data, changes)

        if self.preprocessor is not None and self.regression_model is not None:
            try:
                X_trans = self.preprocessor.transform(df_single)
                pred = float(self.regression_model.predict(X_trans)[0])
                return round(float(np.clip(pred, 0.0, 10.0)), 2)
            except Exception:
                pass

        # Formula fallback if model loading fails
        gk = float(df_single.get("diem_gk", [7.0])[0] if isinstance(df_single.get("diem_gk"), pd.Series) else df_single.get("diem_gk", 7.0))
        qz = float(df_single.get("diem_quiz", [6.5])[0] if isinstance(df_single.get("diem_quiz"), pd.Series) else df_single.get("diem_quiz", 6.5))
        bt = float(df_single.get("diem_bai_tap", [7.5])[0] if isinstance(df_single.get("diem_bai_tap"), pd.Series) else df_single.get("diem_bai_tap", 7.5))
        cc = float(df_single.get("chuyen_can", [80])[0] if isinstance(df_single.get("chuyen_can"), pd.Series) else df_single.get("chuyen_can", 80))
        
        base_score = 0.4 * gk + 0.3 * qz + 0.3 * bt
        attendance_bonus = (cc - 80) * 0.01
        final_score = base_score + attendance_bonus
        return round(float(np.clip(final_score, 0.0, 10.0)), 2)

    def predict_risk(self, score: float) -> Tuple[str, str]:
        """
        Maps predicted score to academic risk level and color badge.
        Complies with R-ETH-01 (uses "Có nguy cơ", never "Sẽ rớt").

        Args:
            score: Predicted final score.

        Returns:
            Tuple[str, str]: (Risk label, Hex color code)
        """
        if score >= 8.0:
            return "Rất thấp (Học lực Giỏi/Xuất sắc)", "#10b981"  # Emerald
        elif score >= 6.5:
            return "Thấp (Học lực Khá)", "#3b82f6"  # Blue
        elif score >= 5.0:
            return "Trung bình (Cần cố gắng)", "#f59e0b"  # Amber
        elif score >= 3.5:
            return "Cao (Có nguy cơ học vụ)", "#f97316"  # Orange
        else:
            return "Rất cao (Nguy cơ học vụ nghiêm trọng)", "#ef4444"  # Red

    def sensitivity_analysis(self, student_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculates sensitivity ranking (feature impact) for top 5+ variables.

        Args:
            student_data: Base student attributes.

        Returns:
            List[Dict[str, Any]]: Sorted list of feature impacts.
        """
        base_score = self.predict_score(student_data)
        results = []

        for item in self.SLIDER_FEATURES:
            key = item["key"]
            name = item["name"]
            curr_val = float(student_data.get(key, item["default"]))

            # Perturb feature upwards
            step = item["step"]
            if item["max"] > 10:
                delta_val = 10.0  # +10% for percentage / LMS hours
            else:
                delta_val = 1.0  # +1.0 point for grades

            new_val = min(item["max"], curr_val + delta_val)
            new_score = self.predict_score(student_data, {key: new_val})
            impact = new_score - base_score

            results.append({
                "key": key,
                "name": name,
                "curr_val": curr_val,
                "delta_val": delta_val,
                "impact": round(impact, 2),
                "abs_impact": abs(impact),
                "stars": "⭐" * max(1, min(5, int(abs(impact) * 5 + 1))),
            })

        results.sort(key=lambda x: x["abs_impact"], reverse=True)
        return results

    def reverse_whatif(self, student_data: Dict[str, Any], target_score: float) -> Dict[str, Any]:
        """
        Calculates minimal feature modifications required to achieve target score.

        Args:
            student_data: Base student attributes.
            target_score: Desired target score (0.0 to 10.0).

        Returns:
            Dict[str, Any]: Required changes per feature to reach target.
        """
        current_score = self.predict_score(student_data)
        needed_delta = target_score - current_score

        if needed_delta <= 0:
            return {
                "achievable": True,
                "current_score": current_score,
                "target_score": target_score,
                "message": "Điểm hiện tại của sinh viên đã đạt hoặc vượt mục tiêu!",
                "changes": {},
            }

        # Sensitivity check to prioritize high-impact levers
        sensitivities = self.sensitivity_analysis(student_data)
        changes = {}
        remaining_needed = needed_delta

        for item in sensitivities:
            if remaining_needed <= 0:
                break

            key = item["key"]
            curr_val = item["curr_val"]
            max_val = float(next(f["max"] for f in self.SLIDER_FEATURES if f["key"] == key))

            # How much space left to increase?
            available_room = max_val - curr_val
            if available_room <= 0:
                continue

            # Estimate score gain per unit of feature increase
            impact_per_unit = item["impact"] / item["delta_val"] if item["delta_val"] > 0 and item["impact"] > 0 else 0.1
            
            units_needed = remaining_needed / impact_per_unit
            units_to_add = min(available_room, units_needed)

            suggested_val = round(curr_val + units_to_add, 1)
            changes[key] = {
                "name": item["name"],
                "from": curr_val,
                "to": suggested_val,
                "increase": round(suggested_val - curr_val, 1),
            }

            actual_gained = units_to_add * impact_per_unit
            remaining_needed -= actual_gained

        achieved_score = self.predict_score(student_data, {k: v["to"] for k, v in changes.items()})

        return {
            "achievable": achieved_score >= (target_score - 0.2),
            "current_score": current_score,
            "target_score": target_score,
            "achieved_score": achieved_score,
            "message": "Đã tính toán phương án điều chỉnh tối ưu." if achieved_score >= target_score - 0.2 else "Cần nâng tối đa các chỉ số mới có thể tiếp cận mục tiêu.",
            "changes": changes,
        }

    def generate_advice(self, student_data: Dict[str, Any], changes: Dict[str, Any], old_score: float, new_score: float) -> str:
        """
        Generates dynamic 4-pillar intervention advice based on simulation delta.

        Args:
            student_data: Base student info.
            changes: Modified features.
            old_score: Original score.
            new_score: Simulated score.

        Returns:
            str: Rich formatted markdown advice text.
        """
        delta = new_score - old_score
        advice_lines = []

        if delta > 0.5:
            advice_lines.append(f"🟢 **Tác động rất tích cực (+{delta:.2f} điểm):** Phương án thay đổi giúp sinh viên nâng hạng học lực rõ rệt.")
        elif delta > 0:
            advice_lines.append(f"🔵 **Tác động tích cực nhẹ (+{delta:.2f} điểm):** Cải thiện một phần điểm số tổng kết.")
        elif delta < 0:
            advice_lines.append(f"🔴 **Cảnh báo suy giảm ({delta:.2f} điểm):** Thay đổi này làm giảm kết quả học tập.")
        else:
            advice_lines.append("⚪ **Không thay đổi:** Các chỉ số điều chỉnh chưa đủ tạo sự khác biệt.")

        # Pillar recommendations
        if "chuyen_can" in changes and changes["chuyen_can"] > student_data.get("chuyen_can", 80):
            advice_lines.append("• **Cố vấn & Đào tạo:** Tăng chuyên cần giúp củng cố kiến thức trên lớp và không bị vắng quá quy định.")
        if "diem_gk" in changes and changes["diem_gk"] > student_data.get("diem_gk", 7.0):
            advice_lines.append("• **Học tập & Phụ đạo:** Cải thiện điểm giữa kỳ đòi hỏi tham gia nhóm học tập và ôn luyện trọng tâm môn học.")
        if "nop_bai_dung_han" in changes and changes["nop_bai_dung_han"] > student_data.get("nop_bai_dung_han", 85):
            advice_lines.append("• **Kỷ luật LMS:** Nộp bài đúng hạn giúp tích lũy trọn vẹn điểm quá trình và rèn luyện thói quen làm việc.")
        if "muc_do_stress" in changes and changes["muc_do_stress"] < student_data.get("muc_do_stress", 3):
            advice_lines.append("• **Hỗ trợ tâm lý:** Giảm áp lực stress giúp sinh viên duy trì sự tập trung và động lực bền vững.")

        advice_lines.append("\n*Lưu ý: Kết quả mô phỏng mang tính chất dự báo hỗ trợ giảng viên đưa ra phương án tư vấn.*")
        return "\n".join(advice_lines)
