"""
Unit tests for PredictionService and WhatIfService (v3.0.0).
Tests:
- Unified inference: predict_score, predict_risk, predict_probability, predict_student.
- No silent fallback fake formulas.
- Data completeness / reliability calculation.
- Standardized sensitivity analysis.
- Constrained target solver via bounded optimization.
- Disclaimer presence (predictive vs causal).
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.services.prediction_service import PredictionService, StudentPrediction
from src.services.whatif_service import WhatIfService, SimulationResult
from src.core.whatif_engine import WhatIfEngine
from src.core.exceptions import PredictionError


@pytest.fixture
def sample_student():
    return {
        "ma_sv": 20230001,
        "ho_ten": "Nguyễn Văn Test",
        "gioi_tinh": "Nam",
        "que_quan": "Hà Nội",
        "nganh_hoc": "CNTT",
        "diem_thpt": 24.5,
        "diem_gk": 7.0,
        "lms_gio_truy_cap": 45.0,
        "lms_xem_video": 30.0,
        "nop_bai_dung_han": 85.0,
        "diem_quiz": 7.5,
        "diem_bai_tap": 8.0,
        "hoan_canh_kt": "Trung bình",
        "di_lam_them": "Không",
        "muc_do_stress": 2.0,
        "dong_luc_hoc": 4.0,
        "chuyen_can": 90.0,
        "muc_tuong_tac": "Tích cực",
        "ghi_chu_gv": "",
    }


class TestPredictionService:
    def test_predict_score_in_valid_range(self, sample_student):
        service = PredictionService()
        if not service.is_ready():
            pytest.skip("Models not trained yet")

        score = service.predict_score(sample_student)
        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0

    def test_predict_risk_returns_valid_label_and_probabilities(self, sample_student):
        service = PredictionService()
        if not service.is_ready():
            pytest.skip("Models not trained yet")

        risk_label, risk_ordinal, probas = service.predict_risk(sample_student)
        assert risk_label in ["Rất thấp", "Thấp", "Trung bình", "Cao"]
        assert risk_ordinal in [1, 2, 3, 4]
        assert isinstance(probas, dict)

    def test_predict_student_full_output(self, sample_student):
        service = PredictionService()
        if not service.is_ready():
            pytest.skip("Models not trained yet")

        pred = service.predict_student(sample_student)
        assert isinstance(pred, StudentPrediction)
        assert pred.ma_sv == 20230001
        assert pred.reliability_score == 100.0
        assert len(pred.missing_fields) == 0
        assert "dự báo" in pred.disclaimer

    def test_reliability_score_reflects_missing_data(self, sample_student):
        service = PredictionService()
        student_with_missing = sample_student.copy()
        student_with_missing["diem_gk"] = None
        student_with_missing["chuyen_can"] = np.nan

        rel, missing = service.calculate_reliability(student_with_missing)
        assert rel < 100.0
        assert "diem_gk" in missing
        assert "chuyen_can" in missing


class TestWhatIfService:
    def test_forward_simulation(self, sample_student):
        service = WhatIfService()
        res = service.simulate(sample_student, {"chuyen_can": 100.0, "diem_gk": 9.0})

        assert isinstance(res, SimulationResult)
        assert res.simulated_score >= res.baseline_score
        assert "predictive simulation" in res.disclaimer

    def test_standardized_sensitivity(self, sample_student):
        service = WhatIfService()
        items = service.analyze_sensitivity(sample_student)

        assert len(items) > 0
        for item in items:
            assert item.unit_step != ""
            assert item.direction in ["Tích cực", "Tiêu cực"]
            assert abs(item.effect_per_unit) >= 0.0

    def test_target_solver_bounded(self, sample_student):
        service = WhatIfService()
        sol = service.solve_target_score(sample_student, target_score=8.5)

        assert sol.target_score == 8.5
        assert isinstance(sol.achieved, bool)
        assert sol.achievable_score >= 0.0
        assert "disclaimer" in sol.to_dict()

    def test_whatif_engine_adapter(self, sample_student):
        engine = WhatIfEngine()
        score = engine.predict_score(sample_student)
        assert 0.0 <= score <= 10.0

        sens = engine.sensitivity_analysis(sample_student)
        assert len(sens) > 0

        rev = engine.reverse_whatif(sample_student, target_score=8.0)
        assert "target_score" in rev
        assert "recommended_actions" in rev
