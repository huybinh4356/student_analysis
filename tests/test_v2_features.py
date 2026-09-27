"""
Unit tests for v2.0 upgrade features:
MissingDetector, DatasetHealthChecker, WhatIfEngine, and ScenarioManager.
"""

import pytest
import pandas as pd
from src.core.missing_detector import MissingDetector
from src.core.dataset_health import DatasetHealthChecker
from src.core.whatif_engine import WhatIfEngine
from src.core.scenario_manager import ScenarioManager


def test_missing_detector_for_student():
    """Verify missing data detection and confidence penalty calculation."""
    detector = MissingDetector()
    student_with_missing = {
        "ma_sv": "202300001",
        "ho_ten": "Test Student",
        "diem_gk": None,  # Critical missing
        "chuyen_can": 20.0,  # Warning (< 30%)
        "lms_gio_truy_cap": 2.0,  # Info (< 5h)
    }

    issues = detector.detect_for_student(student_with_missing)
    assert len(issues) >= 3

    crits = [i for i in issues if i.severity == "critical"]
    warns = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    assert len(crits) >= 1
    assert len(warns) >= 1
    assert len(infos) >= 1

    confidence = detector.calculate_confidence_penalty(issues)
    assert confidence < 100.0
    assert confidence >= 30.0


def test_dataset_health_checker():
    """Verify dataset health assessment, invalid range check, and IQR outliers."""
    checker = DatasetHealthChecker()
    df_sample = pd.DataFrame([
        {"diem_gk": 8.0, "diem_quiz": 7.0, "diem_bai_tap": 8.0, "chuyen_can": 90, "nop_bai_dung_han": 95},
        {"diem_gk": 15.0, "diem_quiz": None, "diem_bai_tap": 6.0, "chuyen_can": 80, "nop_bai_dung_han": 85},
    ])

    report = checker.check(df_sample)
    assert report["total_rows"] == 2
    assert "diem_quiz" in report["missing_summary"]
    assert "diem_gk" in report["invalid_values"]
    assert report["overall_status"] in ["good", "warning", "critical"]
    assert len(report["recommendations"]) > 0


def test_whatif_engine_simulation_and_sensitivity():
    """Verify 7-slider simulation, score/risk prediction, sensitivity ranking, and reverse solver."""
    engine = WhatIfEngine()
    student = {
        "ma_sv": "202300002",
        "diem_gk": 6.0,
        "diem_quiz": 6.0,
        "diem_bai_tap": 6.0,
        "chuyen_can": 70,
        "nop_bai_dung_han": 75,
        "lms_gio_truy_cap": 30,
        "muc_do_stress": 3,
    }

    # 1. Base prediction
    base_score = engine.predict_score(student)
    assert 0.0 <= base_score <= 10.0

    # 2. Risk label & color
    risk_lbl, risk_col = engine.predict_risk(base_score)
    assert isinstance(risk_lbl, str)
    assert risk_col.startswith("#")

    # 3. Simulation with changes
    changes = {"chuyen_can": 95, "nop_bai_dung_han": 95, "diem_gk": 8.5}
    sim_score = engine.predict_score(student, changes)
    assert sim_score >= base_score

    # 4. Sensitivity ranking
    sens = engine.sensitivity_analysis(student)
    assert len(sens) >= 5
    assert "impact" in sens[0]

    # 5. Reverse What-If Solver
    reverse_res = engine.reverse_whatif(student, target_score=8.5)
    assert "achievable" in reverse_res
    assert "changes" in reverse_res


def test_scenario_manager():
    """Verify saving and retrieving simulation scenarios."""
    mgr = ScenarioManager()
    scn = mgr.save_scenario(
        name="Kịch bản Tăng Chuyên Cần",
        student_id="202300003",
        student_name="Nguyen Van A",
        original_score=6.5,
        simulated_score=7.8,
        changes={"chuyen_can": 95},
        advice="Gợi ý cải thiện.",
    )

    assert scn.id.startswith("SCN_")
    all_scenarios = mgr.get_all_scenarios()
    assert len(all_scenarios) == 1
    assert all_scenarios[0].student_id == "202300003"


def test_data_loader_load_data():
    """Verify DataLoader.load_data static method loads non-empty DataFrame."""
    from src.core.data_loader import DataLoader
    df = DataLoader.load_data()
    assert not df.empty
    assert len(df) == 1000

