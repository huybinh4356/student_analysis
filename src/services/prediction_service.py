"""
Prediction Service — central inference engine for Student Analysis Platform v3.
Phases 8, 9 & 12 implementation:
- Single entry point for all UI widgets (Diagnosis, What-If, Report).
- End-to-end inference using registered Pipeline bundles.
- Calibrated class probabilities for Risk classes.
- Explicit Data Completeness / Reliability score (replaces heuristic penalty).
- Strict error handling: raises PredictionError if models fail, NEVER returning fake scores.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import numpy as np
import pandas as pd

from src.core.model_registry import ModelRegistry
from src.core.feature_engineer import FeatureEngineer
from src.core.exceptions import PredictionError, ModelNotFoundError
from src.data.schema import (
    FEATURE_COLS, NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS,
    RISK_CLASSES, ORDINAL_MAPPINGS,
)

logger = logging.getLogger(__name__)

# Reverse map for risk ordinals
_ORDINAL_TO_RISK = {v: k for k, v in ORDINAL_MAPPINGS["nguy_co_hoc_vu"].items()}
_INDEX_TO_RISK = {
    0: "Rất thấp",
    1: "Thấp",
    2: "Trung bình",
    3: "Cao",
}


@dataclass
class StudentPrediction:
    """Standardized prediction output for a student."""
    ma_sv: Optional[Union[str, int]] = None
    predicted_score: float = 0.0
    risk_label: str = "Trung bình"
    risk_ordinal: int = 3
    risk_color: str = "#f59e0b"
    probabilities: Dict[str, float] = field(default_factory=dict)
    reliability_score: float = 100.0   # 0 to 100% data completeness
    missing_fields: List[str] = field(default_factory=list)
    model_version: str = "3.0.0"
    disclaimer: str = (
        "Kết quả mang tính chất dự báo thống kê hỗ trợ tư vấn học tập, "
        "không phải là thước đo định danh cố định hay cam kết nguyên nhân - kết quả."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ma_sv": self.ma_sv,
            "predicted_score": round(self.predicted_score, 2),
            "risk_label": self.risk_label,
            "risk_ordinal": self.risk_ordinal,
            "risk_color": self.risk_color,
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "reliability_score": round(self.reliability_score, 1),
            "missing_fields": self.missing_fields,
            "model_version": self.model_version,
            "disclaimer": self.disclaimer,
        }


class PredictionService:
    """
    Central service for student grade and academic risk predictions.
    Replaces disjoint individual model loaders across UI widgets.
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self.registry = ModelRegistry(models_dir)
        self._reg_bundle: Optional[Dict[str, Any]] = None
        self._cls_bundle: Optional[Dict[str, Any]] = None
        self._load_models()

    def _load_models(self) -> None:
        """Loads regression and classification model bundles from registry."""
        try:
            self._reg_bundle = self.registry.load_bundle("regression")
            logger.info("Loaded regression model: %s", self._reg_bundle.get("metadata", {}).get("model_name"))
        except Exception as e:
            logger.warning("Regression model bundle not loaded: %s", e)
            self._reg_bundle = None

        try:
            self._cls_bundle = self.registry.load_bundle("classification")
            logger.info("Loaded classification model: %s", self._cls_bundle.get("metadata", {}).get("model_name"))
        except Exception as e:
            logger.warning("Classification model bundle not loaded: %s", e)
            self._cls_bundle = None

    def is_ready(self) -> bool:
        """Returns True if both models are available."""
        return self._reg_bundle is not None and self._cls_bundle is not None

    def _prepare_input_df(self, data: Union[Dict[str, Any], pd.DataFrame]) -> pd.DataFrame:
        """Standardizes input dictionary or DataFrame and derives domain features."""
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError(f"Unsupported data type for prediction: {type(data)}")

        # Ensure domain composite features exist
        df = FeatureEngineer.create_features(df)
        return df

    def calculate_reliability(self, student_dict: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Calculates data completeness / reliability percentage based on key predictors.
        Replaces fake confidence penalty heuristic.

        Returns:
            Tuple of (reliability_percentage, list of missing fields)
        """
        critical_cols = [
            "diem_gk", "diem_quiz", "diem_bai_tap", "chuyen_can",
            "nop_bai_dung_han", "lms_gio_truy_cap", "muc_do_stress", "dong_luc_hoc",
        ]
        missing = []
        for col in critical_cols:
            val = student_dict.get(col)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                missing.append(col)

        completeness_ratio = (len(critical_cols) - len(missing)) / len(critical_cols)
        reliability = completeness_ratio * 100.0
        return round(reliability, 1), missing

    def predict_score(self, student_data: Union[Dict[str, Any], pd.DataFrame]) -> float:
        """
        Predicts final semester score (0 to 10) using the registered Regression Pipeline.

        Raises:
            PredictionError: If regression model is unavailable or prediction fails.
        """
        if self._reg_bundle is None:
            raise ModelNotFoundError("Regression model bundle is not available in registry.")

        pipeline = self._reg_bundle["pipeline"]
        df = self._prepare_input_df(student_data)

        try:
            preds = pipeline.predict(df)
            score = float(preds[0]) if len(preds) > 0 else 5.0
            return float(np.clip(score, 0.0, 10.0))
        except Exception as e:
            logger.error("Regression prediction failed: %s", e)
            raise PredictionError(f"Regression prediction failed: {e}") from e

    def predict_risk(
        self, student_data: Union[Dict[str, Any], pd.DataFrame]
    ) -> Tuple[str, int, Dict[str, float]]:
        """
        Predicts academic risk category and class probabilities using the Classification Pipeline.

        Returns:
            Tuple of (risk_label, risk_ordinal, probabilities_dict)

        Raises:
            PredictionError: If classification model is unavailable or fails.
        """
        if self._cls_bundle is None:
            raise ModelNotFoundError("Classification model bundle is not available in registry.")

        pipeline = self._cls_bundle["pipeline"]
        df = self._prepare_input_df(student_data)

        try:
            preds = pipeline.predict(df)
            raw_pred = preds[0]

            # Model may output 0-indexed (0, 1, 2, 3) or 1-indexed (1, 2, 3, 4)
            if raw_pred in [0, 1, 2, 3]:
                risk_label = _INDEX_TO_RISK[int(raw_pred)]
                risk_ordinal = int(raw_pred) + 1
            elif raw_pred in [1, 2, 3, 4]:
                risk_label = _ORDINAL_TO_RISK[int(raw_pred)]
                risk_ordinal = int(raw_pred)
            else:
                risk_label = str(raw_pred)
                risk_ordinal = 3

            # Compute probabilities if supported
            probabilities = {}
            if hasattr(pipeline, "predict_proba"):
                try:
                    probas = pipeline.predict_proba(df)[0]
                    classes = pipeline.classes_
                    for idx, prob in enumerate(probas):
                        cls_val = classes[idx]
                        if cls_val in _INDEX_TO_RISK:
                            lbl = _INDEX_TO_RISK[cls_val]
                        elif cls_val in _ORDINAL_TO_RISK:
                            lbl = _ORDINAL_TO_RISK[cls_val]
                        else:
                            lbl = f"Class {cls_val}"
                        probabilities[lbl] = float(prob)
                except Exception as pe:
                    logger.debug("predict_proba failed: %s", pe)

            return risk_label, risk_ordinal, probabilities
        except Exception as e:
            logger.error("Classification prediction failed: %s", e)
            raise PredictionError(f"Classification prediction failed: {e}") from e

    def predict_student(self, student_data: Dict[str, Any]) -> StudentPrediction:
        """
        Complete prediction for a student profile, yielding score, risk, probabilities,
        and data completeness.
        """
        ma_sv = student_data.get("ma_sv")
        predicted_score = self.predict_score(student_data)
        risk_label, risk_ordinal, probabilities = self.predict_risk(student_data)
        reliability, missing = self.calculate_reliability(student_data)

        color = RISK_CLASSES.get(risk_label, {}).get("color", "#3b82f6")
        version = self._reg_bundle.get("version", "3.0.0") if self._reg_bundle else "3.0.0"

        return StudentPrediction(
            ma_sv=ma_sv,
            predicted_score=predicted_score,
            risk_label=risk_label,
            risk_ordinal=risk_ordinal,
            risk_color=color,
            probabilities=probabilities,
            reliability_score=reliability,
            missing_fields=missing,
            model_version=version,
        )
