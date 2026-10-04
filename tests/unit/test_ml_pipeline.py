"""
Unit tests for ML Layer v3 — sklearn Pipeline, clean CV, ModelRegistry, and zero-leakage training.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.core.preprocessor import DataPreprocessor, build_column_preprocessor, OrdinalMapper
from src.core.model_trainer import ModelTrainer
from src.core.model_registry import ModelRegistry
from src.data.schema import FEATURE_COLS, TARGET_REGRESSION, TARGET_CLASSIFICATION


@pytest.fixture
def sample_students_df():
    """Generates synthetic student DataFrame adhering strictly to schema."""
    np.random.seed(42)
    n = 60
    return pd.DataFrame({
        "ma_sv": [f"SV{i:04d}" for i in range(n)],
        "ho_ten": [f"Sinh Vien {i}" for i in range(n)],
        "gioi_tinh": np.random.choice(["Nam", "Nữ"], size=n),
        "que_quan": np.random.choice(["Hà Nội", "Đà Nẵng", "TP.HCM"], size=n),
        "nganh_hoc": np.random.choice(["CNTT", "KTPM", "HTTT"], size=n),
        "diem_thpt": np.random.uniform(18.0, 29.0, size=n),
        "diem_gk": np.random.uniform(3.0, 9.5, size=n),
        "lms_gio_truy_cap": np.random.uniform(10.0, 80.0, size=n),
        "lms_xem_video": np.random.uniform(5.0, 60.0, size=n),
        "nop_bai_dung_han": np.random.uniform(50.0, 100.0, size=n),
        "diem_quiz": np.random.uniform(4.0, 10.0, size=n),
        "diem_bai_tap": np.random.uniform(4.0, 10.0, size=n),
        "hoan_canh_kt": np.random.choice(["Khó khăn", "Trung bình", "Khá giả"], size=n),
        "di_lam_them": np.random.choice(["Có", "Không"], size=n),
        "muc_do_stress": np.random.uniform(1.0, 5.0, size=n),
        "dong_luc_hoc": np.random.uniform(1.0, 5.0, size=n),
        "chuyen_can": np.random.uniform(50.0, 100.0, size=n),
        "muc_tuong_tac": np.random.choice(["Thụ động", "Bình thường", "Tích cực"], size=n),
        "ghi_chu_gv": [""] * n,
        "nguy_co_hoc_vu": np.random.choice(["Rất thấp", "Thấp", "Trung bình", "Cao"], size=n),
        "diem_tong_ket": np.random.uniform(3.5, 9.5, size=n),
    })


class TestDataPreprocessor:
    def test_prepare_features_excludes_targets_and_id(self, sample_students_df):
        prep = DataPreprocessor()
        X, y_reg, y_cls = prep.prepare_features(sample_students_df)

        assert "ma_sv" not in X.columns
        assert "ho_ten" not in X.columns
        assert TARGET_REGRESSION not in X.columns
        assert TARGET_CLASSIFICATION not in X.columns
        assert "composite_exam_score" not in X.columns

        assert len(y_reg) == len(sample_students_df)
        assert len(y_cls) == len(sample_students_df)
        assert set(y_cls.unique()).issubset({1, 2, 3, 4})

    def test_split_data_maintains_balance(self, sample_students_df):
        prep = DataPreprocessor(test_size=0.25, random_state=42)
        X, y_reg, y_cls = prep.prepare_features(sample_students_df)
        splits = prep.split_data(X, y_reg, y_cls)

        assert len(splits["X_train"]) == 45
        assert len(splits["X_test"]) == 15
        assert len(splits["y_reg_train"]) == 45
        assert len(splits["y_cls_train"]) == 45

    def test_column_transformer_fit_transform(self, sample_students_df):
        prep = DataPreprocessor()
        X, _, _ = prep.prepare_features(sample_students_df)
        ct = build_column_preprocessor(list(X.columns))

        transformed = ct.fit_transform(X)
        assert isinstance(transformed, np.ndarray)
        assert transformed.shape[0] == len(sample_students_df)
        assert not np.isnan(transformed).any()


class TestModelTrainerAndRegistry:
    def test_train_and_register_regression(self, sample_students_df, tmp_path):
        prep = DataPreprocessor(test_size=0.2, random_state=42)
        X, y_reg, y_cls = prep.prepare_features(sample_students_df)
        splits = prep.split_data(X, y_reg, y_cls)

        trainer = ModelTrainer(models_dir=tmp_path)
        summary_df, best_info = trainer.train_evaluate_regression(
            splits["X_train"],
            splits["X_test"],
            splits["y_reg_train"],
            splits["y_reg_test"],
            cv_folds=3,
        )

        assert not summary_df.empty
        assert "CV R² (mean)" in summary_df.columns
        assert "Selected" in summary_df.columns
        assert best_info["model_name"] != ""
        assert "r2" in best_info["test_metrics"]

        # Verify registry artifacts
        registry = ModelRegistry(models_dir=tmp_path)
        bundle = registry.load_bundle("regression")
        assert "pipeline" in bundle
        assert "metadata" in bundle
        assert bundle["metadata"]["model_name"] == best_info["model_name"]

        # Predict with loaded pipeline
        pipeline = bundle["pipeline"]
        preds = pipeline.predict(splits["X_test"].head(3))
        assert len(preds) == 3
        assert np.all(preds >= 0.0)

    def test_train_and_register_classification(self, sample_students_df, tmp_path):
        prep = DataPreprocessor(test_size=0.2, random_state=42)
        X, y_reg, y_cls = prep.prepare_features(sample_students_df)
        splits = prep.split_data(X, y_reg, y_cls)

        trainer = ModelTrainer(models_dir=tmp_path)
        summary_df, best_info = trainer.train_evaluate_classification(
            splits["X_train"],
            splits["X_test"],
            splits["y_cls_train"],
            splits["y_cls_test"],
            cv_folds=3,
        )

        assert not summary_df.empty
        assert "CV Macro F1 (mean)" in summary_df.columns
        assert best_info["model_name"] != ""
        assert "accuracy" in best_info["test_metrics"]

        # Verify registry artifacts
        registry = ModelRegistry(models_dir=tmp_path)
        bundle = registry.load_bundle("classification")
        assert "pipeline" in bundle
        pipeline = bundle["pipeline"]
        preds = pipeline.predict(splits["X_test"].head(3))
        assert len(preds) == 3
