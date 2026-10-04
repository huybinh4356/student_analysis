"""
Unit tests for src/data/schema.py — data contract.
"""

import pytest
from src.data.schema import (
    ALL_SPECS, FEATURE_COLS, NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS,
    TARGET_COLS, TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL,
    LEAKAGE_BANNED_FEATURES, REQUIRED_COLS, ORDINAL_MAPPINGS,
)


class TestSchemaCompleteness:
    def test_all_specs_not_empty(self):
        assert len(ALL_SPECS) > 0

    def test_target_regression_defined(self):
        assert TARGET_REGRESSION == "diem_tong_ket"
        assert TARGET_REGRESSION in ALL_SPECS

    def test_target_classification_defined(self):
        assert TARGET_CLASSIFICATION == "nguy_co_hoc_vu"
        assert TARGET_CLASSIFICATION in ALL_SPECS

    def test_id_col_defined(self):
        assert ID_COL == "ma_sv"
        assert ID_COL in ALL_SPECS

    def test_feature_cols_do_not_include_targets(self):
        assert TARGET_REGRESSION not in FEATURE_COLS
        assert TARGET_CLASSIFICATION not in FEATURE_COLS

    def test_feature_cols_do_not_include_id(self):
        assert ID_COL not in FEATURE_COLS

    def test_leakage_banned_features_explicit(self):
        """composite_exam_score must be in the banned set (R²=0.938 audit)."""
        assert "composite_exam_score" in LEAKAGE_BANNED_FEATURES

    def test_leakage_banned_not_in_feature_cols(self):
        """Banned features must never appear in the feature set used for training."""
        for banned in LEAKAGE_BANNED_FEATURES:
            assert banned not in FEATURE_COLS, (
                f"{banned} is in FEATURE_COLS but should be banned (leakage risk)."
            )


class TestNumericSpecRanges:
    def test_grade_features_range_0_to_10(self):
        grade_cols = {"diem_gk", "diem_quiz", "diem_bai_tap"}
        for spec in NUMERIC_COLS:
            if spec.name in grade_cols:
                assert spec.min_val == 0.0, f"{spec.name} min should be 0.0"
                assert spec.max_val == 10.0, f"{spec.name} max should be 10.0"

    def test_attendance_range_0_to_100(self):
        for spec in NUMERIC_COLS:
            if spec.name == "chuyen_can":
                assert spec.min_val == 0.0
                assert spec.max_val == 100.0

    def test_stress_range_1_to_5(self):
        for spec in NUMERIC_COLS:
            if spec.name == "muc_do_stress":
                assert spec.min_val == 1.0
                assert spec.max_val == 5.0

    def test_target_regression_range(self):
        for spec in TARGET_COLS:
            if spec.name == TARGET_REGRESSION:
                assert spec.min_val == 0.0
                assert spec.max_val == 10.0


class TestOrdinalMappings:
    def test_nguy_co_has_4_classes(self):
        assert len(ORDINAL_MAPPINGS["nguy_co_hoc_vu"]) == 4

    def test_nguy_co_values_sequential(self):
        values = sorted(ORDINAL_MAPPINGS["nguy_co_hoc_vu"].values())
        assert values == [1, 2, 3, 4]

    def test_hoan_canh_kt_mapping(self):
        m = ORDINAL_MAPPINGS["hoan_canh_kt"]
        assert m["Khó khăn"] < m["Trung bình"] < m["Khá giả"]

    def test_muc_tuong_tac_mapping(self):
        m = ORDINAL_MAPPINGS["muc_tuong_tac"]
        assert m["Thụ động"] < m["Bình thường"] < m["Tích cực"]
