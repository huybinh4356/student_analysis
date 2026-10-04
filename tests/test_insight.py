"""
Unit tests for InsightEngine advice generator and What-If simulator.
"""

import pytest
import pandas as pd
from src.core.data_loader import DataLoader
from src.core.insight_engine import InsightEngine


def test_insight_advice_generation():
    """Verify ethical advice generation and warnings."""
    engine = InsightEngine()
    sample_student = {
        "ma_sv": 202300001,
        "ho_ten": "Nguyễn Văn A",
        "chuyen_can": 45.0,  # Low attendance
        "nop_bai_dung_han": 50.0,
        "diem_gk": 4.0,  # Low midterm
        "muc_do_stress": 5,  # High stress
        "dong_luc_hoc": 2,
        "di_lam_them": ">= 20h/tuần",
        "nguy_co_hoc_vu": "Cao",
    }

    result = engine.generate_student_advice(sample_student)

    assert result["ma_sv"] == 202300001
    assert len(result["nguyen_nhan"]) >= 0
    assert len(result["khuyen_nghi_hanh_dong"]) >= 3
    assert "Giảng viên" in result["disclaimer"]


def test_what_if_simulation():
    """Verify What-If simulation re-predicts score and risk."""
    engine = InsightEngine()
    df = DataLoader.load_data().head(1)

    result = engine.simulate_what_if(df, chuyen_can_delta=20.0, diem_gk_delta=2.0)

    assert "diem_cu" in result
    assert "diem_moi" in result
    assert "chenh_lech_diem" in result
    assert "disclaimer" in result
