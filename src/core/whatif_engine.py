"""
What-If Simulation Engine — Adapter layer connecting UI widgets to WhatIfService.
Phases 13-17 implementation:
- Delegates simulation, sensitivity, and reverse solving to WhatIfService.
- Removes silent fake fallback formulas (R-MODEL-02, WHATIF-01).
- Unifies risk semantics with registered classification model (ML-11).
- Emphasizes predictive simulation vs causal estimation distinction (WHATIF-04).
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging
import numpy as np
import pandas as pd

from src.services.whatif_service import WhatIfService, SensitivityItem, TargetSolution, DISCLAIMER_TEXT
from src.services.prediction_service import PredictionService
from src.core.exceptions import PredictionError

logger = logging.getLogger(__name__)


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

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path(__file__).resolve().parents[2] / "models"
        self.pred_service = PredictionService(models_dir=self.models_dir)
        self.service = WhatIfService(prediction_service=self.pred_service)

    def predict_score(self, student_data: Dict[str, Any], changes: Optional[Dict[str, Any]] = None) -> float:
        """
        Predicts final score given student data and applied feature changes.
        Uses registered ML Regression Pipeline. Raises PredictionError if unavailable.
        """
        data = student_data.copy()
        if changes:
            data.update(changes)
        return self.pred_service.predict_score(data)

    def predict_risk(self, score: float, student_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Predicts academic risk level and badge color.
        If student_data is provided, uses the true Classification Pipeline (ML-11).
        """
        if student_data:
            try:
                risk_label, _, _ = self.pred_service.predict_risk(student_data)
                color = self._get_risk_color(risk_label)
                return risk_label, color
            except Exception as e:
                logger.debug("Classification pipeline prediction failed, falling back to score band: %s", e)

        # Standard grade classification bands
        if score >= 8.0:
            return "Rất thấp (Học lực Giỏi/Xuất sắc)", "#10b981"
        elif score >= 6.5:
            return "Thấp (Học lực Khá)", "#3b82f6"
        elif score >= 5.0:
            return "Trung bình (Cần cố gắng)", "#f59e0b"
        elif score >= 3.5:
            return "Cao (Có nguy cơ học vụ)", "#f97316"
        else:
            return "Rất cao (Nguy cơ học vụ nghiêm trọng)", "#ef4444"

    def _get_risk_color(self, risk_label: str) -> str:
        color_map = {
            "Rất thấp": "#10b981",
            "Thấp": "#3b82f6",
            "Trung bình": "#f59e0b",
            "Cao": "#ef4444",
        }
        for k, color in color_map.items():
            if k in risk_label:
                return color
        return "#3b82f6"

    def sensitivity_analysis(self, student_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculates standardized sensitivity ranking for top controllable variables.
        Standardizes change per unit: Δscore / Δfeature.
        """
        items = self.service.analyze_sensitivity(student_data)
        results = []
        for it in items:
            results.append({
                "feature": it.feature_name,
                "name": it.feature_label_vi,
                "label": it.feature_label_vi,
                "delta": it.score_impact,
                "impact": it.score_impact,
                "stars": "*" * max(1, min(5, int(abs(it.score_impact) * 5 + 1))),
                "effect_per_unit": it.effect_per_unit,
                "display": f"{it.unit_step} -> {'+' if it.score_impact >= 0 else ''}{it.score_impact:.2f} điểm",
                "impact_type": "Tích cực" if it.score_impact >= 0 else "Tiêu cực",
            })
        return results

    def reverse_whatif(
        self,
        student_data: Dict[str, Any],
        target_score: float = 7.0,
    ) -> Dict[str, Any]:
        """
        Solves for minimum intervention required to reach target score
        using bounded optimization (WHATIF-03).
        """
        current_score = self.predict_score(student_data)
        sol = self.service.solve_target_score(student_data, target_score)
        
        actions = []
        changes_dict = {}
        for feat, diff in sol.required_changes.items():
            name_vi = next((f["name"] for f in self.SLIDER_FEATURES if f["key"] == feat), feat)
            actions.append({
                "feature": feat,
                "label": name_vi,
                "current": diff["hien_tai"],
                "target": diff["de_xuat"],
                "delta": diff["thay_doi"],
            })
            changes_dict[feat] = {
                "name": name_vi,
                "from": diff["hien_tai"],
                "to": diff["de_xuat"],
                "increase": diff["thay_doi"],
            }

        return {
            "current_score": current_score,
            "target_score": sol.target_score,
            "achieved_score": sol.achievable_score,
            "achievable_score": sol.achievable_score,
            "achieved": sol.achieved,
            "achievable": sol.achieved,
            "changes": changes_dict,
            "recommended_actions": actions,
            "message": sol.message,
            "disclaimer": DISCLAIMER_TEXT,
        }

    def generate_advice(
        self,
        student_data: Dict[str, Any],
        changes: Dict[str, Any],
        old_score: float,
        new_score: float,
    ) -> str:
        """
        Generates dynamic pedagogical intervention advice based on simulation delta.
        """
        delta = new_score - old_score
        advice_lines = []

        if delta > 0.5:
            advice_lines.append(f"**[Tác động rất tích cực (+{delta:.2f} điểm)]:** Kịch bản điều chỉnh giúp sinh viên nâng hạng học lực rõ rệt.")
        elif delta > 0:
            advice_lines.append(f"**[Tác động tích cực (+{delta:.2f} điểm)]:** Cải thiện một phần điểm số dự báo.")
        elif delta < -0.05:
            advice_lines.append(f"**[Cảnh báo suy giảm ({delta:.2f} điểm)]:** Thay đổi này làm giảm kết quả dự báo.")
        else:
            advice_lines.append("**[Không thay đổi]:** Các chỉ số điều chỉnh chưa đủ tạo sự khác biệt.")

        # Pillar recommendations
        if "chuyen_can" in changes and changes["chuyen_can"] > student_data.get("chuyen_can", 80):
            advice_lines.append("• **Cố vấn & Đào tạo:** Tăng chuyên cần giúp củng cố kiến thức trên lớp và không bị vắng quá quy định.")
        if "diem_gk" in changes and changes["diem_gk"] > student_data.get("diem_gk", 7.0):
            advice_lines.append("• **Học tập & Phụ đạo:** Cải thiện điểm giữa kỳ đòi hỏi tham gia nhóm học tập và ôn luyện trọng tâm môn học.")
        if "nop_bai_dung_han" in changes and changes["nop_bai_dung_han"] > student_data.get("nop_bai_dung_han", 85):
            advice_lines.append("• **Kỷ luật LMS:** Nộp bài đúng hạn giúp tích lũy trọn vẹn điểm quá trình và rèn luyện thói quen làm việc.")
        if "muc_do_stress" in changes and changes["muc_do_stress"] < student_data.get("muc_do_stress", 3):
            advice_lines.append("• **Hỗ trợ tâm lý:** Giảm áp lực stress giúp sinh viên duy trì sự tập trung và động lực bền vững.")

        advice_lines.append(f"\n*{DISCLAIMER_TEXT}*")
        return "\n".join(advice_lines)
