"""
Feature Engineering module for generating domain-specific composite indicators.

Leakage Policy (v3):
    composite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT was REMOVED.
    Audit (2026-10-04) confirmed R²=0.938 between this feature and diem_tong_ket,
    which would artificially inflate regression R² to ~94%.
    Raw components (diem_gk, diem_quiz, diem_bai_tap) are retained individually
    and provide strong signal (R² 0.86–0.89 each) without leakage.
"""

import pandas as pd
import numpy as np

# Features that MUST NOT be derived from target components (leakage guard)
_LEAKAGE_BANNED = {"composite_exam_score"}


class FeatureEngineer:
    """Creates interaction, ratio, and composite domain features.

    Rules:
        - Never create a feature that is a linear combination of GK/Quiz/BT
          if diem_tong_ket is the regression target (leakage by construction).
        - Raw grade features (diem_gk, diem_quiz, diem_bai_tap) are kept as-is.
    """

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates engineered features from existing student metrics.

        Removed in v3:
            composite_exam_score — leakage R²=0.938 vs diem_tong_ket (audit 2026-10-04).

        Args:
            df: Input student DataFrame.

        Returns:
            pd.DataFrame: DataFrame with additional engineered columns.
        """
        data = df.copy()

        # 1. LMS Learning Intensity (hours per video watched)
        #    Captures study depth, not just time spent.
        data["lms_gio_per_video"] = np.where(
            data["lms_xem_video"] > 0,
            data["lms_gio_truy_cap"] / data["lms_xem_video"],
            0.0,
        )

        # 2. Academic Engagement Index
        #    Combines attendance % and on-time submission % into a single engagement score.
        #    Neither component is a grade — no leakage risk.
        data["academic_engagement_index"] = (
            0.5 * data["chuyen_can"] + 0.5 * data["nop_bai_dung_han"]
        )

        # 3. Psychological Pressure Ratio (stress / motivation)
        #    High ratio → high risk signal independent of grades.
        data["stress_motivation_ratio"] = (
            data["muc_do_stress"] / (data["dong_luc_hoc"] + 1e-5)
        )

        # 4. Low Engagement Flag
        #    Binary alert: attendance < 50% OR deadline submission < 50%.
        data["low_engagement_flag"] = (
            (data["chuyen_can"] < 50.0) | (data["nop_bai_dung_han"] < 50.0)
        ).astype(int)

        # Sanity check: ensure no banned leakage feature was accidentally created
        new_cols = set(data.columns) - set(df.columns)
        leaked = _LEAKAGE_BANNED & new_cols
        if leaked:
            raise RuntimeError(
                f"Leakage guard triggered: features {leaked} must not be created. "
                "See leakage audit in docs/data_dictionary.md."
            )


        return data
