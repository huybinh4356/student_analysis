"""
Model Trainer Module for Machine Learning Regression and Classification Pipelines.
Enforces Rules: R-MODEL-01 to R-MODEL-08.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd

from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression, RidgeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBRegressor, XGBClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score


class ModelTrainer:
    """Trains, evaluates, and compares ML regression & classification models."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train_evaluate_regression(
        self, X_train: np.ndarray, X_test: np.ndarray, y_train: pd.Series, y_test: pd.Series
    ) -> pd.DataFrame:
        """
        Trains baseline and 5 regression models, evaluating R2, RMSE, MAE, CV score, and overfit check.

        Args:
            X_train: Transformed train features.
            X_test: Transformed test features.
            y_train: Continuous target train values.
            y_test: Continuous target test values.

        Returns:
            pd.DataFrame: Comparative performance table.
        """
        models = {
            "Baseline (Mean)": DummyRegressor(strategy="mean"),
            "Linear Regression": LinearRegression(),
            "Ridge Regression": Ridge(alpha=1.0),
            "Lasso Regression": Lasso(alpha=0.01),
            "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
            "XGBoost Regressor": XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        }

        results = []
        trained_objects = {}

        for name, model in models.items():
            model.fit(X_train, y_train)
            trained_objects[name] = model

            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)

            r2_train = r2_score(y_train, y_train_pred)
            r2_test = r2_score(y_test, y_test_pred)
            rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
            mae_test = mean_absolute_error(y_test, y_test_pred)

            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
            cv_mean = np.mean(cv_scores)

            overfit_diff = r2_train - r2_test
            overfit_flag = "⚠️ YES (>0.1)" if overfit_diff > 0.1 else "NO"

            results.append({
                "Model": name,
                "Train R²": round(r2_train, 4),
                "Test R²": round(r2_test, 4),
                "CV R² (5-fold)": round(cv_mean, 4),
                "RMSE": round(rmse_test, 4),
                "MAE": round(mae_test, 4),
                "Overfitting": overfit_flag,
            })

        summary_df = pd.DataFrame(results)

        # Rule R-MODEL-05: Parsimony Check (If Ridge & XGBoost difference < 0.03 R2 -> pick Ridge)
        ridge_r2 = summary_df.loc[summary_df["Model"] == "Ridge Regression", "Test R²"].values[0]
        xgb_r2 = summary_df.loc[summary_df["Model"] == "XGBoost Regressor", "Test R²"].values[0]
        best_name = "Ridge Regression" if (xgb_r2 - ridge_r2) < 0.03 else "XGBoost Regressor"

        # Save Best Model
        joblib.dump(trained_objects[best_name], self.models_dir / "ridge_regression_model.pkl")

        return summary_df

    def train_evaluate_classification(
        self, X_train: np.ndarray, X_test: np.ndarray, y_train: pd.Series, y_test: pd.Series
    ) -> pd.DataFrame:
        """
        Trains baseline and 5 classification models, evaluating Accuracy, F1-macro, F1-weighted.

        Args:
            X_train: Transformed train features.
            X_test: Transformed test features.
            y_train: Categorical target train values (1-4).
            y_test: Categorical target test values (1-4).

        Returns:
            pd.DataFrame: Comparative performance table.
        """
        # Adjust 1-based indexing to 0-based for XGBoost Classifier
        y_train_xgb = y_train - 1
        y_test_xgb = y_test - 1

        models = {
            "Baseline (Majority)": DummyClassifier(strategy="most_frequent"),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Ridge Classifier": RidgeClassifier(random_state=42),
            "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
            "XGBoost Classifier": XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        }

        results = []
        trained_objects = {}

        for name, model in models.items():
            if name == "XGBoost Classifier":
                model.fit(X_train, y_train_xgb)
                y_train_pred = model.predict(X_train) + 1
                y_test_pred = model.predict(X_test) + 1
            else:
                model.fit(X_train, y_train)
                y_train_pred = model.predict(X_train)
                y_test_pred = model.predict(X_test)

            trained_objects[name] = model

            acc_train = accuracy_score(y_train, y_train_pred)
            acc_test = accuracy_score(y_test, y_test_pred)
            f1_macro = f1_score(y_test, y_test_pred, average="macro")
            f1_weighted = f1_score(y_test, y_test_pred, average="weighted")

            cv_scores = cross_val_score(model, X_train, y_train if name != "XGBoost Classifier" else y_train_xgb, cv=5, scoring="accuracy")
            cv_mean = np.mean(cv_scores)

            overfit_diff = acc_train - acc_test
            overfit_flag = "⚠️ YES (>0.1)" if overfit_diff > 0.1 else "NO"

            results.append({
                "Model": name,
                "Train Acc": round(acc_train, 4),
                "Test Acc": round(acc_test, 4),
                "CV Acc (5-fold)": round(cv_mean, 4),
                "F1-Macro": round(f1_macro, 4),
                "F1-Weighted": round(f1_weighted, 4),
                "Overfitting": overfit_flag,
            })

        summary_df = pd.DataFrame(results)

        # Save Best Classification Model
        best_model_name = summary_df.sort_values(by="F1-Macro", ascending=False).iloc[0]["Model"]
        joblib.dump(trained_objects[best_model_name], self.models_dir / "risk_classifier_model.pkl")

        return summary_df
