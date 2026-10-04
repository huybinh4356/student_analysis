"""
Model Trainer Module for Machine Learning Regression and Classification Pipelines.
Phase 4 & 5 implementation:
- End-to-end Pipeline training with zero CV leakage (R-DATA-04).
- Model selection based strictly on CV score (never test set) (R-MODEL-02).
- Automatic persistence via ModelRegistry into models/registry.json and bundle artifacts.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
import joblib

from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression, RidgeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBRegressor, XGBClassifier
from sklearn.model_selection import cross_validate, StratifiedKFold, KFold
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, f1_score, recall_score, classification_report,
)

from src.core.preprocessor import DataPreprocessor, build_column_preprocessor
from src.core.model_registry import ModelRegistry
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains, evaluates, and selects best ML models using clean cross-validation pipelines.
    """

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            self.models_dir = Path(__file__).resolve().parents[2] / "models"
        else:
            self.models_dir = Path(models_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry = ModelRegistry(self.models_dir)

    def train_evaluate_regression(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        cv_folds: int = 5,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Trains and compares 6 regression candidates using end-to-end Pipelines.
        Model selection is done purely on Cross-Validation R² on X_train.
        Final evaluation on X_test is run once on the winning model.

        Args:
            X_train: Raw training feature DataFrame.
            X_test: Raw testing feature DataFrame.
            y_train: Continuous target train values.
            y_test: Continuous target test values.
            cv_folds: Number of folds for cross-validation.

        Returns:
            Tuple of (summary_df, best_model_info)
        """
        feature_cols = list(X_train.columns)

        candidate_models = {
            "Baseline (Mean)": DummyRegressor(strategy="mean"),
            "Linear Regression": LinearRegression(),
            "Ridge Regression": Ridge(alpha=1.0, random_state=42),
            "Lasso Regression": Lasso(alpha=0.01, random_state=42),
            "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
            "XGBoost Regressor": XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        }

        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        candidate_pipelines = {}
        cv_records = []

        logger.info("Starting regression model comparison across %d candidates...", len(candidate_models))

        for name, estimator in candidate_models.items():
            preprocessor = build_column_preprocessor(feature_cols)
            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model", estimator),
            ])

            # CV on raw X_train — preprocessor fits per-fold, strictly preventing leakage
            cv_scores = cross_validate(
                pipe,
                X_train,
                y_train,
                cv=cv,
                scoring={"r2": "r2", "neg_mae": "neg_mean_absolute_error"},
                return_train_score=True,
            )

            cv_r2_mean = float(np.mean(cv_scores["test_r2"]))
            cv_r2_std = float(np.std(cv_scores["test_r2"]))
            cv_mae_mean = float(-np.mean(cv_scores["test_neg_mae"]))
            train_r2_mean = float(np.mean(cv_scores["train_r2"]))

            candidate_pipelines[name] = pipe

            cv_records.append({
                "Model": name,
                "CV R² (mean)": round(cv_r2_mean, 4),
                "CV R² (std)": round(cv_r2_std, 4),
                "CV MAE": round(cv_mae_mean, 4),
                "Train R² (mean)": round(train_r2_mean, 4),
                "Overfitting Gap": round(train_r2_mean - cv_r2_mean, 4),
            })

        summary_df = pd.DataFrame(cv_records)

        # ── Model Selection based STRICTLY on CV performance (R-MODEL-02) ────
        # Parsimony rule: if best model is complex (RF/XGB) but Ridge/Linear is within 0.02 CV R²,
        # prefer the simpler interpretable model.
        sorted_candidates = summary_df.sort_values(by="CV R² (mean)", ascending=False)
        top_name = sorted_candidates.iloc[0]["Model"]
        top_cv_r2 = sorted_candidates.iloc[0]["CV R² (mean)"]

        linear_row = summary_df[summary_df["Model"] == "Ridge Regression"]
        if not linear_row.empty and top_name not in ["Linear Regression", "Ridge Regression", "Lasso Regression"]:
            linear_cv_r2 = linear_row.iloc[0]["CV R² (mean)"]
            if (top_cv_r2 - linear_cv_r2) < 0.02:
                best_name = "Ridge Regression"
                selection_reason = f"Ridge selected by parsimony: CV R² ({linear_cv_r2}) within 0.02 of top {top_name} ({top_cv_r2})"
            else:
                best_name = top_name
                selection_reason = f"Selected by highest CV R² ({top_cv_r2})"
        else:
            best_name = top_name
            selection_reason = f"Selected by highest CV R² ({top_cv_r2})"

        logger.info("Selected best regression model: %s (%s)", best_name, selection_reason)

        # ── Final Fit & ONE-TIME Test Evaluation ──────────────────────────────
        best_pipeline = candidate_pipelines[best_name]
        best_pipeline.fit(X_train, y_train)

        y_test_pred = best_pipeline.predict(X_test)
        test_r2 = float(r2_score(y_test, y_test_pred))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, y_test_pred)))
        test_mae = float(mean_absolute_error(y_test, y_test_pred))

        best_cv_row = summary_df[summary_df["Model"] == best_name].iloc[0]
        cv_metrics = {
            "cv_r2_mean": float(best_cv_row["CV R² (mean)"]),
            "cv_r2_std": float(best_cv_row["CV R² (std)"]),
            "cv_mae": float(best_cv_row["CV MAE"]),
        }
        test_metrics = {
            "r2": round(test_r2, 4),
            "rmse": round(test_rmse, 4),
            "mae": round(test_mae, 4),
        }

        # Add Test metrics to summary table for reporting
        summary_df["Selected"] = summary_df["Model"].apply(lambda m: "[Best]" if m == best_name else "")
        summary_df.loc[summary_df["Model"] == best_name, "Test R²"] = round(test_r2, 4)
        summary_df.loc[summary_df["Model"] == best_name, "Test RMSE"] = round(test_rmse, 4)
        summary_df.loc[summary_df["Model"] == best_name, "Test MAE"] = round(test_mae, 4)

        # ── Persist to Registry Bundle ───────────────────────────────────────
        saved_path = self.registry.save_bundle(
            task_type="regression",
            model_name=best_name,
            pipeline=best_pipeline,
            cv_metrics=cv_metrics,
            test_metrics=test_metrics,
            feature_names=feature_cols,
            selection_reason=selection_reason,
        )

        best_info = {
            "model_name": best_name,
            "pipeline": best_pipeline,
            "cv_metrics": cv_metrics,
            "test_metrics": test_metrics,
            "artifact_path": str(saved_path),
            "selection_reason": selection_reason,
        }

        return summary_df, best_info

    def train_evaluate_classification(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        cv_folds: int = 5,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Trains and compares 6 classification candidates using end-to-end Pipelines.
        Model selection is done purely on Cross-Validation Macro F1 on X_train.
        Final evaluation on X_test is run once on the winning model.

        Args:
            X_train: Raw training feature DataFrame.
            X_test: Raw testing feature DataFrame.
            y_train: Categorical target train values (1-4).
            y_test: Categorical target test values (1-4).
            cv_folds: Number of folds for cross-validation.

        Returns:
            Tuple of (summary_df, best_model_info)
        """
        feature_cols = list(X_train.columns)

        candidate_models = {
            "Baseline (Majority)": DummyClassifier(strategy="most_frequent"),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Ridge Classifier": RidgeClassifier(random_state=42),
            "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
            "XGBoost Classifier": XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        }

        # XGBoost requires 0-based indexing for labels
        y_train_xgb = y_train - 1
        y_test_xgb = y_test - 1

        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        candidate_pipelines = {}
        cv_records = []

        logger.info("Starting classification model comparison across %d candidates...", len(candidate_models))

        for name, estimator in candidate_models.items():
            preprocessor = build_column_preprocessor(feature_cols)
            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model", estimator),
            ])

            target_train = y_train_xgb if name == "XGBoost Classifier" else y_train

            cv_scores = cross_validate(
                pipe,
                X_train,
                target_train,
                cv=cv,
                scoring={"f1_macro": "f1_macro", "accuracy": "accuracy"},
                return_train_score=True,
            )

            cv_f1_mean = float(np.mean(cv_scores["test_f1_macro"]))
            cv_f1_std = float(np.std(cv_scores["test_f1_macro"]))
            cv_acc_mean = float(np.mean(cv_scores["test_accuracy"]))
            train_f1_mean = float(np.mean(cv_scores["train_f1_macro"]))

            candidate_pipelines[name] = pipe

            cv_records.append({
                "Model": name,
                "CV Macro F1 (mean)": round(cv_f1_mean, 4),
                "CV Macro F1 (std)": round(cv_f1_std, 4),
                "CV Accuracy": round(cv_acc_mean, 4),
                "Train F1 (mean)": round(train_f1_mean, 4),
                "Overfitting Gap": round(train_f1_mean - cv_f1_mean, 4),
            })

        summary_df = pd.DataFrame(cv_records)

        # ── Model Selection based STRICTLY on CV Macro F1 (R-MODEL-02) ────────
        sorted_candidates = summary_df.sort_values(by="CV Macro F1 (mean)", ascending=False)
        best_name = sorted_candidates.iloc[0]["Model"]
        best_cv_f1 = sorted_candidates.iloc[0]["CV Macro F1 (mean)"]
        selection_reason = f"Selected by highest CV Macro F1 ({best_cv_f1})"

        logger.info("Selected best classification model: %s (%s)", best_name, selection_reason)

        # ── Final Fit & ONE-TIME Test Evaluation ──────────────────────────────
        best_pipeline = candidate_pipelines[best_name]
        is_xgb = (best_name == "XGBoost Classifier")
        best_pipeline.fit(X_train, y_train_xgb if is_xgb else y_train)

        y_test_pred_raw = best_pipeline.predict(X_test)
        y_test_pred = (y_test_pred_raw + 1) if is_xgb else y_test_pred_raw

        test_acc = float(accuracy_score(y_test, y_test_pred))
        test_f1_macro = float(f1_score(y_test, y_test_pred, average="macro"))
        test_f1_weighted = float(f1_score(y_test, y_test_pred, average="weighted"))

        # Recall for High-Risk (class 4)
        recall_high_risk = float(recall_score(
            (y_test == 4).astype(int),
            (y_test_pred == 4).astype(int),
            zero_division=0,
        ))

        best_cv_row = summary_df[summary_df["Model"] == best_name].iloc[0]
        cv_metrics = {
            "cv_f1_macro_mean": float(best_cv_row["CV Macro F1 (mean)"]),
            "cv_f1_macro_std": float(best_cv_row["CV Macro F1 (std)"]),
            "cv_accuracy": float(best_cv_row["CV Accuracy"]),
        }
        test_metrics = {
            "accuracy": round(test_acc, 4),
            "f1_macro": round(test_f1_macro, 4),
            "f1_weighted": round(test_f1_weighted, 4),
            "recall_high_risk": round(recall_high_risk, 4),
        }

        # Add Test metrics to summary table
        summary_df["Selected"] = summary_df["Model"].apply(lambda m: "[Best]" if m == best_name else "")
        summary_df.loc[summary_df["Model"] == best_name, "Test Accuracy"] = round(test_acc, 4)
        summary_df.loc[summary_df["Model"] == best_name, "Test F1-Macro"] = round(test_f1_macro, 4)
        summary_df.loc[summary_df["Model"] == best_name, "Recall High-Risk"] = round(recall_high_risk, 4)

        # ── Persist to Registry Bundle ───────────────────────────────────────
        saved_path = self.registry.save_bundle(
            task_type="classification",
            model_name=best_name,
            pipeline=best_pipeline,
            cv_metrics=cv_metrics,
            test_metrics=test_metrics,
            feature_names=feature_cols,
            selection_reason=selection_reason,
        )

        best_info = {
            "model_name": best_name,
            "pipeline": best_pipeline,
            "cv_metrics": cv_metrics,
            "test_metrics": test_metrics,
            "artifact_path": str(saved_path),
            "selection_reason": selection_reason,
        }

        return summary_df, best_info
