"""
What-If Simulation Service — Rebuilt for Student Analysis Platform v3.
Phases 13, 14, 15, 16, 17 implementation:
- Consumes PredictionService exclusively (no independent model loading).
- NO silent fake fallback formulas (R-MODEL-02, WHATIF-01).
- Standardized Sensitivity: marginal change in score per unit (WHATIF-02).
- Constrained Target Solver: scipy.optimize bounded quadratic cost optimization (WHATIF-03).
- Explicit predictive vs causal distinction disclaimer (WHATIF-04).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.services.prediction_service import PredictionService, StudentPrediction
from src.core.exceptions import PredictionError, WhatIfError

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "Lưu ý: Đây là mô phỏng kịch bản dự báo thống kê (predictive simulation), "
    "không đảm bảo cam kết nhân quả thực tế (causal estimation)."
)


@dataclass
class SimulationResult:
    """Outcome of a forward What-If parameter modification."""
    baseline_score: float
    simulated_score: float
    score_delta: float
    baseline_risk: str
    simulated_risk: str
    risk_changed: bool
    applied_changes: Dict[str, Any]
    disclaimer: str = DISCLAIMER_TEXT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_score": round(self.baseline_score, 2),
            "simulated_score": round(self.simulated_score, 2),
            "score_delta": round(self.score_delta, 2),
            "baseline_risk": self.baseline_risk,
            "simulated_risk": self.simulated_risk,
            "risk_changed": self.risk_changed,
            "applied_changes": self.applied_changes,
            "disclaimer": self.disclaimer,
        }


@dataclass
class SensitivityItem:
    """Standardized effect of modifying a single feature."""
    feature_name: str
    feature_label_vi: str
    unit_step: str
    raw_delta: float
    score_impact: float
    effect_per_unit: float
    direction: str                     # "Tích cực" | "Tiêu cực"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature_name,
            "label": self.feature_label_vi,
            "unit": self.unit_step,
            "impact": round(self.score_impact, 3),
            "effect_per_unit": round(self.effect_per_unit, 4),
            "direction": self.direction,
        }


@dataclass
class TargetSolution:
    """Result of constrained optimization for reverse What-If."""
    achieved: bool
    target_score: float
    achievable_score: float
    required_changes: Dict[str, Dict[str, float]]  # {feat: {"old": x, "new": y, "delta": +d}}
    total_cost: float
    message: str
    disclaimer: str = DISCLAIMER_TEXT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "achieved": self.achieved,
            "target_score": round(self.target_score, 2),
            "achievable_score": round(self.achievable_score, 2),
            "required_changes": self.required_changes,
            "total_cost": round(self.total_cost, 2),
            "message": self.message,
            "disclaimer": self.disclaimer,
        }


class WhatIfService:
    """
    Service providing forward simulation, standardized sensitivity,
    and constrained target goal-seeking.
    """

    def __init__(self, prediction_service: Optional[PredictionService] = None):
        self.pred_service = prediction_service or PredictionService()

    def simulate(
        self,
        student_data: Dict[str, Any],
        changes: Optional[Dict[str, Any]] = None,
    ) -> SimulationResult:
        """
        Runs forward What-If scenario by applying feature changes to a student profile.

        Args:
            student_data: Baseline student attributes.
            changes: Mapping of features to updated values or relative deltas.

        Returns:
            SimulationResult with baseline vs simulated score and risk.

        Raises:
            PredictionError: If underlying prediction fails (NO fake formulas).
        """
        # Baseline prediction
        base_pred = self.pred_service.predict_student(student_data)
        base_score = base_pred.predicted_score
        base_risk = base_pred.risk_label

        if not changes:
            return SimulationResult(
                baseline_score=base_score,
                simulated_score=base_score,
                score_delta=0.0,
                baseline_risk=base_risk,
                simulated_risk=base_risk,
                risk_changed=False,
                applied_changes={},
            )

        # Apply changes
        simulated_data = student_data.copy()
        for k, v in changes.items():
            simulated_data[k] = v

        sim_pred = self.pred_service.predict_student(simulated_data)
        sim_score = sim_pred.predicted_score
        sim_risk = sim_pred.risk_label

        return SimulationResult(
            baseline_score=base_score,
            simulated_score=sim_score,
            score_delta=sim_score - base_score,
            baseline_risk=base_risk,
            simulated_risk=sim_risk,
            risk_changed=(base_risk != sim_risk),
            applied_changes=changes,
        )

    def analyze_sensitivity(self, student_data: Dict[str, Any]) -> List[SensitivityItem]:
        """
        Computes standardized marginal impact for controllable features.
        Standardizes change per unit: Δscore / Δfeature.
        """
        baseline_score = self.pred_service.predict_score(student_data)

        # Controllable features: (key, label, delta_to_test, unit_display, divisor)
        test_features = [
            ("diem_gk", "Điểm Giữa kỳ", 1.0, "+1.0 điểm", 1.0),
            ("diem_quiz", "Điểm Quiz", 1.0, "+1.0 điểm", 1.0),
            ("diem_bai_tap", "Điểm Bài tập", 1.0, "+1.0 điểm", 1.0),
            ("chuyen_can", "Chuyên cần", 10.0, "+10%", 10.0),
            ("nop_bai_dung_han", "Nộp bài đúng hạn", 10.0, "+10%", 10.0),
            ("lms_gio_truy_cap", "LMS Giờ học", 5.0, "+5 giờ", 5.0),
            ("dong_luc_hoc", "Động lực học", 1.0, "+1 mức", 1.0),
            ("muc_do_stress", "Mức độ Stress", -1.0, "-1 mức", -1.0),
        ]

        items = []
        for key, label, delta, unit_lbl, divisor in test_features:
            val = student_data.get(key)
            if val is None or not isinstance(val, (int, float)):
                continue

            test_dict = student_data.copy()
            test_dict[key] = val + delta
            try:
                new_score = self.pred_service.predict_score(test_dict)
                impact = new_score - baseline_score
                effect_per_unit = impact / divisor

                items.append(SensitivityItem(
                    feature_name=key,
                    feature_label_vi=label,
                    unit_step=unit_lbl,
                    raw_delta=delta,
                    score_impact=impact,
                    effect_per_unit=effect_per_unit,
                    direction="Tích cực" if impact >= 0 else "Tiêu cực",
                ))
            except Exception as e:
                logger.debug("Sensitivity test failed for %s: %s", key, e)

        # Sort by absolute impact descending
        items.sort(key=lambda x: abs(x.score_impact), reverse=True)
        return items

    def solve_target_score(
        self,
        student_data: Dict[str, Any],
        target_score: float,
        tolerated_error: float = 0.05,
    ) -> TargetSolution:
        """
        Constrained Target Solver (Reverse What-If):
        Finds the minimum-effort intervention required to achieve the target score.

        Uses scipy.optimize.minimize with bounded limits on academic grades and effort.

        Args:
            student_data: Current student profile.
            target_score: Desired final grade (e.g. 7.0, 8.0).
            tolerated_error: Allowable tolerance.

        Returns:
            TargetSolution with optimal changes and effort breakdown.
        """
        baseline_score = self.pred_service.predict_score(student_data)
        if baseline_score >= target_score:
            return TargetSolution(
                achieved=True,
                target_score=target_score,
                achievable_score=baseline_score,
                required_changes={},
                total_cost=0.0,
                message=f"Điểm dự báo hiện tại ({baseline_score:.2f}) đã đạt hoặc vượt mục tiêu ({target_score:.2f}).",
            )

        # Decision variables: [gk, quiz, bt, cc, nop_bai, lms, stress, dong_luc]
        vars_info = [
            ("diem_gk", 0.0, 10.0, 2.0),           # (name, min, max, weight_cost)
            ("diem_quiz", 0.0, 10.0, 1.5),
            ("diem_bai_tap", 0.0, 10.0, 1.5),
            ("chuyen_can", 0.0, 100.0, 0.05),
            ("nop_bai_dung_han", 0.0, 100.0, 0.05),
            ("lms_gio_truy_cap", 0.0, 200.0, 0.02),
            ("dong_luc_hoc", 1.0, 5.0, 1.0),
            ("muc_do_stress", 1.0, 5.0, 1.0),
        ]

        x0 = []
        bounds = []
        weights = []

        for name, min_b, max_b, w in vars_info:
            current_val = float(student_data.get(name, min_b))
            x0.append(current_val)
            weights.append(w)

            # Constraints: student generally improves (grades can only increase, stress can only decrease)
            if name == "muc_do_stress":
                bounds.append((min_b, current_val))  # Stress can only decrease or stay same
            else:
                bounds.append((current_val, max_b))   # Other features can only increase

        x0 = np.array(x0)
        weights = np.array(weights)

        # Objective: minimize weighted normalized change
        def objective(x):
            return np.sum(weights * ((x - x0) ** 2))

        # Constraint: predict_score(x) >= target_score
        def score_constraint(x):
            cand_dict = student_data.copy()
            for idx, (name, _, _, _) in enumerate(vars_info):
                cand_dict[name] = float(x[idx])
            try:
                pred = self.pred_service.predict_score(cand_dict)
                return pred - target_score
            except Exception:
                return -10.0

        constraints = [{"type": "ineq", "fun": score_constraint}]

        try:
            res = minimize(
                objective,
                x0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 100, "ftol": 1e-4},
            )

            # Check if achievable
            final_dict = student_data.copy()
            for idx, (name, _, _, _) in enumerate(vars_info):
                final_dict[name] = float(res.x[idx])
            achieved_score = self.pred_service.predict_score(final_dict)

            achieved = (achieved_score >= target_score - tolerated_error)
            changes = {}
            for idx, (name, _, _, _) in enumerate(vars_info):
                old_v = round(float(x0[idx]), 1)
                new_v = round(float(res.x[idx]), 1)
                delta = round(new_v - old_v, 1)
                if abs(delta) >= 0.1:
                    changes[name] = {
                        "hien_tai": old_v,
                        "de_xuat": new_v,
                        "thay_doi": f"+{delta}" if delta > 0 else f"{delta}",
                    }

            msg = (
                f"Đã tìm thấy phương án can thiệp tối ưu để đạt {achieved_score:.2f} điểm."
                if achieved else
                f"Mục tiêu {target_score:.2f} không thể đạt trong giới hạn tối đa (tối đa đạt được {achieved_score:.2f})."
            )

            return TargetSolution(
                achieved=achieved,
                target_score=target_score,
                achievable_score=achieved_score,
                required_changes=changes,
                total_cost=float(res.fun),
                message=msg,
            )

        except Exception as e:
            logger.error("Target solver optimization failed: %s", e)
            raise WhatIfError(f"Target optimization failed: {e}") from e
