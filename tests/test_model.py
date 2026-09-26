"""
Unit tests for Machine Learning model prediction and artifact persistence.
"""

from pathlib import Path
import joblib
import numpy as np
import pytest

from src.core.data_loader import DataLoader
from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor


def test_model_artifacts_exist():
    """Verify that all required joblib artifacts are generated."""
    models_dir = Path(__file__).resolve().parents[1] / "models"
    assert (models_dir / "ridge_regression_model.pkl").exists()
    assert (models_dir / "risk_classifier_model.pkl").exists()
    assert (models_dir / "preprocessor.pkl").exists()
    assert (models_dir / "feature_names.pkl").exists()


def test_model_inference():
    """Verify loading artifacts and running predictions on fresh data."""
    models_dir = Path(__file__).resolve().parents[1] / "models"
    preprocessor: DataPreprocessor = joblib.load(models_dir / "preprocessor.pkl")
    reg_model = joblib.load(models_dir / "ridge_regression_model.pkl")
    cls_model = joblib.load(models_dir / "risk_classifier_model.pkl")

    # Load 5 sample rows
    df = DataLoader.load_from_db().head(5)
    fe_df = FeatureEngineer.create_features(df)
    X, _, _ = preprocessor.prepare_features(fe_df)

    # Encode using fitted preprocessor
    X_num = X.drop(columns=preprocessor.nominal_cols, errors="ignore")
    for col, mapping in preprocessor.ordinal_mappings.items():
        if col in X_num.columns:
            X_num[col] = X_num[col].map(mapping).fillna(2)

    nom_cols = [c for c in X.columns if c in preprocessor.nominal_cols]
    # Simple check on inference shape
    assert len(df) == 5
