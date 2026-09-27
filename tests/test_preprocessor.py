"""
Unit tests for DataPreprocessor and FeatureEngineer modules.
"""

import pytest
import pandas as pd
from src.core.data_loader import DataLoader
from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor


def test_feature_engineering():
    """Verify feature engineering creates expected columns with correct math."""
    df = DataLoader.load_from_db().head(10)
    fe_df = FeatureEngineer.create_features(df)

    assert "lms_gio_per_video" in fe_df.columns
    assert "academic_engagement_index" in fe_df.columns
    assert "stress_motivation_ratio" in fe_df.columns
    assert "composite_exam_score" in fe_df.columns
    assert "low_engagement_flag" in fe_df.columns

    # Verify math for composite_exam_score (0.4*gk + 0.3*quiz + 0.3*bt)
    sample = fe_df.iloc[0]
    expected_score = round(0.4 * sample["diem_gk"] + 0.3 * sample["diem_quiz"] + 0.3 * sample["diem_bai_tap"], 4)
    assert round(sample["composite_exam_score"], 4) == expected_score


def test_preprocessor_split_and_transform():
    """Verify DataPreprocessor splits without data leakage and transforms shapes correctly."""
    df = DataLoader.load_from_db()
    fe_df = FeatureEngineer.create_features(df)
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

    X, y_reg, y_cls = preprocessor.prepare_features(fe_df)
    splits = preprocessor.split_data(X, y_reg, y_cls)

    n_total = len(df)
    n_test = int(n_total * 0.2)
    n_train = n_total - n_test

    assert len(splits["X_train"]) == n_train
    assert len(splits["X_test"]) == n_test

    X_train_t, X_test_t, feature_names = preprocessor.encode_and_scale(
        splits["X_train"], splits["X_test"]
    )

    assert X_train_t.shape[0] == n_train
    assert X_test_t.shape[0] == n_test
    assert X_train_t.shape[1] == len(feature_names)
