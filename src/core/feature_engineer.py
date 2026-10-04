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

        lms_video = data["lms_xem_video"] if "lms_xem_video" in data.columns else pd.Series(0.0, index=data.index)
        lms_hours = data["lms_gio_truy_cap"] if "lms_gio_truy_cap" in data.columns else pd.Series(0.0, index=data.index)
        chuyen_can = data["chuyen_can"] if "chuyen_can" in data.columns else pd.Series(80.0, index=data.index)
        nop_bai = data["nop_bai_dung_han"] if "nop_bai_dung_han" in data.columns else pd.Series(80.0, index=data.index)
        stress = data["muc_do_stress"] if "muc_do_stress" in data.columns else pd.Series(2.0, index=data.index)
        dong_luc = data["dong_luc_hoc"] if "dong_luc_hoc" in data.columns else pd.Series(3.0, index=data.index)

        # 1. LMS Learning Intensity (hours per video watched)
        data["lms_gio_per_video"] = np.where(
            lms_video > 0,
            lms_hours / lms_video,
            0.0,
        )

        # 2. Academic Engagement Index
        data["academic_engagement_index"] = (
            0.5 * chuyen_can + 0.5 * nop_bai
        )

        # 3. Psychological Pressure Ratio (stress / motivation)
        data["stress_motivation_ratio"] = (
            stress / (dong_luc + 1e-5)
        )

        # 4. Low Engagement Flag
        data["low_engagement_flag"] = (
            (chuyen_can < 50.0) | (nop_bai < 50.0)
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
