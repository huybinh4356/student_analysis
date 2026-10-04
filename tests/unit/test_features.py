"""
Unit tests for src/core/feature_engineer.py — v3 (leakage-fixed).
"""

import pytest
import pandas as pd
import numpy as np

from src.core.feature_engineer import FeatureEngineer, _LEAKAGE_BANNED


def _make_df(n: int = 10) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "diem_gk":         rng.uniform(4.0, 9.0, n),
        "diem_quiz":       rng.uniform(4.0, 9.0, n),
        "diem_bai_tap":    rng.uniform(4.0, 9.0, n),
        "chuyen_can":      rng.uniform(60.0, 100.0, n),
        "nop_bai_dung_han":rng.uniform(60.0, 100.0, n),
        "muc_do_stress":   rng.integers(1, 5, n).astype(float),
        "dong_luc_hoc":    rng.integers(1, 5, n).astype(float),
        "lms_gio_truy_cap":rng.uniform(10.0, 200.0, n),
        "lms_xem_video":   rng.integers(1, 50, n).astype(float),
        "diem_tong_ket":   rng.uniform(4.0, 9.0, n),
    })


class TestLeakageGuard:
    def test_composite_exam_score_not_created(self):
        """composite_exam_score must NOT appear in output (leakage ban)."""
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert "composite_exam_score" not in out.columns

    def test_banned_set_contains_composite(self):
        assert "composite_exam_score" in _LEAKAGE_BANNED

    def test_leakage_guard_bans_composite_from_output(self):
        """create_features() output must never contain composite_exam_score."""
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        # Direct check: banned feature absent from output
        for banned in _LEAKAGE_BANNED:
            assert banned not in out.columns, (
                f"Banned leakage feature '{banned}' found in feature engineer output."
            )



class TestFeaturesCreated:
    def test_lms_gio_per_video_created(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert "lms_gio_per_video" in out.columns

    def test_academic_engagement_index_created(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert "academic_engagement_index" in out.columns

    def test_stress_motivation_ratio_created(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert "stress_motivation_ratio" in out.columns

    def test_low_engagement_flag_created(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert "low_engagement_flag" in out.columns

    def test_exactly_4_new_features(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        new_cols = set(out.columns) - set(df.columns)
        assert len(new_cols) == 4


class TestFeatureValues:
    def test_lms_per_video_zero_when_no_videos(self):
        df = _make_df(5)
        df["lms_xem_video"] = 0
        out = FeatureEngineer.create_features(df)
        assert (out["lms_gio_per_video"] == 0.0).all()

    def test_engagement_index_range(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert out["academic_engagement_index"].between(0.0, 100.0).all()

    def test_low_engagement_flag_binary(self):
        df = _make_df()
        out = FeatureEngineer.create_features(df)
        assert set(out["low_engagement_flag"].unique()).issubset({0, 1})

    def test_low_engagement_flag_triggers_below_50(self):
        df = _make_df(3)
        df["chuyen_can"] = [30.0, 80.0, 80.0]
        df["nop_bai_dung_han"] = [80.0, 80.0, 80.0]
        out = FeatureEngineer.create_features(df)
        assert out["low_engagement_flag"].iloc[0] == 1
        assert out["low_engagement_flag"].iloc[1] == 0

    def test_stress_ratio_no_zero_division(self):
        df = _make_df(5)
        df["dong_luc_hoc"] = 0.0
        out = FeatureEngineer.create_features(df)
        assert not out["stress_motivation_ratio"].isna().any()
        assert not np.isinf(out["stress_motivation_ratio"]).any()

    def test_original_df_not_mutated(self):
        df = _make_df()
        df_copy = df.copy()
        FeatureEngineer.create_features(df)
        pd.testing.assert_frame_equal(df, df_copy)
