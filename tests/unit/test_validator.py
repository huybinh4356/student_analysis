"""
Unit tests for src/data/validator.py — DataValidator.

Covers happy path, bad-case scenarios (missing columns, invalid ranges,
duplicates, unknown categories) and risk signal detection.
"""

import pytest
import pandas as pd
import numpy as np

from src.data.validator import DataValidator, ValidationResult
from src.core.exceptions import SchemaError


def _make_valid_df(n: int = 5) -> pd.DataFrame:
    """Build a minimal valid DataFrame for testing."""
    return pd.DataFrame({
        "ma_sv":           [f"SV{i:03d}" for i in range(n)],
        "ho_ten":          [f"Nguyen Van {i}" for i in range(n)],
        "gioi_tinh":       ["Nam"] * n,
        "que_quan":        ["Hà Nội"] * n,
        "nganh_hoc":       ["CNTT"] * n,
        "diem_thpt":       [22.0] * n,
        "diem_gk":         [7.0] * n,
        "diem_quiz":       [6.5] * n,
        "diem_bai_tap":    [7.5] * n,
        "lms_gio_truy_cap":[50.0] * n,
        "lms_xem_video":   [10.0] * n,
        "nop_bai_dung_han":[85.0] * n,
        "muc_do_stress":   [2.0] * n,
        "dong_luc_hoc":    [4.0] * n,
        "chuyen_can":      [80.0] * n,
        "hoan_canh_kt":    ["Trung bình"] * n,
        "muc_tuong_tac":   ["Bình thường"] * n,
        "di_lam_them":     ["Không"] * n,
        "ghi_chu_gv":      [None] * n,
        "nguy_co_hoc_vu":  ["Thấp"] * n,
        "diem_tong_ket":   [7.2] * n,
    })


# ── Happy path ────────────────────────────────────────────────────────────────

class TestHappyPath:
    def test_valid_df_passes(self):
        df = _make_valid_df(10)
        result = DataValidator.validate(df)
        assert result.is_valid

    def test_result_has_correct_row_count(self):
        df = _make_valid_df(20)
        result = DataValidator.validate(df)
        assert result.total_rows == 20

    def test_no_blocking_issues_on_valid_data(self):
        df = _make_valid_df(5)
        result = DataValidator.validate(df)
        blocking = [i for i in result.issues if i.error_type in {"MISSING", "INVALID", "DUPLICATE", "UNKNOWN"}]
        assert len(blocking) == 0


# ── Missing columns ───────────────────────────────────────────────────────────

class TestMissingColumns:
    def test_missing_required_column_raises_schema_error(self):
        df = _make_valid_df(5).drop(columns=["diem_gk"])
        with pytest.raises(SchemaError, match="diem_gk"):
            DataValidator.validate(df)

    def test_missing_target_column_raises_schema_error(self):
        df = _make_valid_df(5).drop(columns=["diem_tong_ket"])
        with pytest.raises(SchemaError):
            DataValidator.validate(df)

    def test_missing_id_column_raises_schema_error(self):
        df = _make_valid_df(5).drop(columns=["ma_sv"])
        with pytest.raises(SchemaError):
            DataValidator.validate(df)


# ── Invalid ranges ────────────────────────────────────────────────────────────

class TestInvalidRanges:
    def test_negative_score_is_invalid(self):
        df = _make_valid_df(5)
        df.loc[0, "diem_gk"] = -1.0
        result = DataValidator.validate(df)
        assert not result.is_valid
        invalid = [i for i in result.issues if i.error_type == "INVALID" and i.column == "diem_gk"]
        assert len(invalid) == 1

    def test_score_above_10_is_invalid(self):
        df = _make_valid_df(5)
        df.loc[0, "diem_bai_tap"] = 11.0
        result = DataValidator.validate(df)
        assert not result.is_valid

    def test_attendance_above_100_is_invalid(self):
        df = _make_valid_df(5)
        df.loc[0, "chuyen_can"] = 105.0
        result = DataValidator.validate(df)
        assert not result.is_valid

    def test_stress_above_5_is_invalid(self):
        df = _make_valid_df(5)
        df.loc[0, "muc_do_stress"] = 6.0
        result = DataValidator.validate(df)
        assert not result.is_valid

    def test_target_outside_0_10_is_invalid(self):
        df = _make_valid_df(5)
        df.loc[0, "diem_tong_ket"] = 12.0
        result = DataValidator.validate(df)
        assert not result.is_valid


# ── Duplicate detection ───────────────────────────────────────────────────────

class TestDuplicates:
    def test_duplicate_student_id_flagged(self):
        df = _make_valid_df(5)
        df.loc[0, "ma_sv"] = df.loc[1, "ma_sv"]   # force duplicate ID
        result = DataValidator.validate(df)
        assert not result.is_valid
        dup_issues = [i for i in result.issues if i.error_type == "DUPLICATE" and i.column == "ma_sv"]
        assert len(dup_issues) == 1

    def test_duplicate_rows_flagged(self):
        df = _make_valid_df(4)
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # add exact duplicate row
        result = DataValidator.validate(df)
        assert not result.is_valid


# ── Unknown categories ────────────────────────────────────────────────────────

class TestUnknownCategories:
    def test_unknown_risk_class_flagged(self):
        df = _make_valid_df(5)
        df.loc[0, "nguy_co_hoc_vu"] = "Siêu cao"   # not a valid class
        result = DataValidator.validate(df)
        assert not result.is_valid
        unknown = [i for i in result.issues if i.error_type == "UNKNOWN" and i.column == "nguy_co_hoc_vu"]
        assert len(unknown) == 1

    def test_unknown_hoan_canh_flagged(self):
        df = _make_valid_df(5)
        df.loc[0, "hoan_canh_kt"] = "Giàu có"
        result = DataValidator.validate(df)
        assert not result.is_valid

    def test_unknown_gioi_tinh_flagged(self):
        df = _make_valid_df(5)
        df.loc[0, "gioi_tinh"] = "Khác"
        result = DataValidator.validate(df)
        # gioi_tinh allowed: Nam/Nữ
        assert not result.is_valid


# ── Risk signals ──────────────────────────────────────────────────────────────

class TestRiskSignals:
    def test_low_attendance_generates_risk_signal(self):
        df = _make_valid_df(5)
        df.loc[0, "chuyen_can"] = 30.0    # below 50%
        result = DataValidator.validate(df)
        # Should still be valid (RISK_SIGNAL is non-blocking)
        assert result.is_valid
        risk = [i for i in result.issues if i.error_type == "RISK_SIGNAL" and i.column == "chuyen_can"]
        assert len(risk) == 1

    def test_high_stress_generates_risk_signal(self):
        df = _make_valid_df(5)
        df.loc[0, "muc_do_stress"] = 4.0   # >= 4.0 threshold
        result = DataValidator.validate(df)
        assert result.is_valid
        risk = [i for i in result.issues if i.error_type == "RISK_SIGNAL" and i.column == "muc_do_stress"]
        assert len(risk) == 1


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_all_null_numeric_columns_fails(self):
        df = _make_valid_df(5)
        df["diem_tong_ket"] = np.nan
        result = DataValidator.validate(df)
        assert not result.is_valid

    def test_single_row_valid(self):
        df = _make_valid_df(1)
        result = DataValidator.validate(df)
        assert result.is_valid

    def test_rates_are_between_0_and_1(self):
        df = _make_valid_df(10)
        df.loc[0, "diem_gk"] = -5.0
        result = DataValidator.validate(df)
        assert 0.0 <= result.missing_rate <= 1.0
        assert 0.0 <= result.invalid_rate <= 1.0
        assert 0.0 <= result.duplicate_rate <= 1.0
