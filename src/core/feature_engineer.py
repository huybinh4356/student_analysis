"""
Feature Engineering module for generating domain-specific composite indicators.
"""

import pandas as pd
import numpy as np


class FeatureEngineer:
    """Creates interaction, ratio, and composite domain features."""

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates engineered features from existing student metrics.

        Args:
            df: Input student DataFrame.

        Returns:
            pd.DataFrame: DataFrame with additional engineered columns.
        """
        data = df.copy()

        # 1. LMS Learning Intensity (Hours per video watched)
        data["lms_gio_per_video"] = np.where(
            data["lms_xem_video"] > 0,
            data["lms_gio_truy_cap"] / data["lms_xem_video"],
            0.0
        )

        # 2. Academic Engagement Index (Combined attendance % & deadline submission %)
        data["academic_engagement_index"] = (
            0.5 * data["chuyen_can"] + 0.5 * data["nop_bai_dung_han"]
        )

        # 3. Psychological Pressure Ratio (Stress level / Motivation level)
        data["stress_motivation_ratio"] = (
            data["muc_do_stress"] / (data["dong_luc_hoc"] + 1e-5)
        )

        # 4. Composite Midterm Performance Score
        data["composite_exam_score"] = (
            0.4 * data["diem_gk"] + 0.3 * data["diem_quiz"] + 0.3 * data["diem_bai_tap"]
        )

        # 5. Low Engagement Flag (Attendance < 50% OR Deadline submission < 50%)
        data["low_engagement_flag"] = (
            (data["chuyen_can"] < 50.0) | (data["nop_bai_dung_han"] < 50.0)
        ).astype(int)

        return data
