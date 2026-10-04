"""
Model Registry — manages model artifacts, versioning, bundling, and metadata.
Phase 6 & 7 implementation for v3.0.0.
"""

from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata describing a trained model and its evaluation metrics."""
    model_name: str
    task_type: str                     # "regression" | "classification"
    artifact_relpath: str              # e.g. "regression/best_model.pkl"
    version: str = "3.0.0"
    trained_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cv_metrics: Dict[str, float] = field(default_factory=dict)
    test_metrics: Dict[str, float] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    dataset_version: str = "default"
    selection_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelMetadata:
        return cls(**data)


class ModelRegistry:
    """Central registry for persisting, loading, and querying model artifacts."""

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            # Default to project root / models
            self.models_dir = Path(__file__).resolve().parents[2] / "models"
        else:
            self.models_dir = Path(models_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.models_dir / "registry.json"

    def get_registry_data(self) -> Dict[str, Any]:
        """Loads the registry.json dictionary, returning empty dict if missing."""
        if not self.registry_file.exists():
            return {}
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Could not read registry.json: %s", e)
            return {}

    def save_registry_data(self, data: Dict[str, Any]) -> None:
        """Atomically saves registry data to registry.json."""
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_bundle(
        self,
        task_type: str,
        model_name: str,
        pipeline: Any,
        cv_metrics: Dict[str, float],
        test_metrics: Dict[str, float],
        feature_names: List[str],
        selection_reason: str = "",
        dataset_version: str = "default",
    ) -> Path:
        """
        Saves a self-contained model bundle (pipeline + metadata) to disk.

        Args:
            task_type: "regression" or "classification"
            model_name: Name of algorithm (e.g. "Ridge Regression", "XGBoost Regressor")
            pipeline: Fitted sklearn Pipeline or model object
            cv_metrics: Cross-validation summary scores (e.g. CV R², CV MAE)
            test_metrics: Single final test evaluation scores (e.g. Test R², MAE, RMSE)
            feature_names: List of input feature names
            selection_reason: Explanation of why this model was chosen
            dataset_version: Identifier of dataset used for training

        Returns:
            Path to saved artifact bundle
        """
        sub_dir = self.models_dir / task_type
        sub_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = sub_dir / "best_model.pkl"
        rel_artifact_path = f"{task_type}/best_model.pkl"

        metadata = ModelMetadata(
            model_name=model_name,
            task_type=task_type,
            artifact_relpath=rel_artifact_path,
            cv_metrics=cv_metrics,
            test_metrics=test_metrics,
            feature_names=feature_names,
            selection_reason=selection_reason,
            dataset_version=dataset_version,
        )

        bundle = {
            "pipeline": pipeline,
            "metadata": metadata.to_dict(),
            "feature_names": feature_names,
            "version": metadata.version,
        }

        joblib.dump(bundle, artifact_path)
        logger.info("Saved %s model bundle to %s", task_type, artifact_path)

        # Update registry.json
        reg_data = self.get_registry_data()
        reg_data[task_type] = metadata.to_dict()
        self.save_registry_data(reg_data)

        # Legacy compatibility links/files:
        # What-If and Diagnosis widgets in v2 look for ridge_regression_model.pkl and risk_classifier_model.pkl
        try:
            if task_type == "regression":
                joblib.dump(pipeline, self.models_dir / "ridge_regression_model.pkl")
            elif task_type == "classification":
                joblib.dump(pipeline, self.models_dir / "risk_classifier_model.pkl")
            joblib.dump(feature_names, self.models_dir / "feature_names.pkl")
        except Exception as e:
            logger.warning("Could not write legacy model compatibility file: %s", e)

        return artifact_path

    def load_bundle(self, task_type: str) -> Dict[str, Any]:
        """
        Loads the complete model bundle for the specified task type.

        Args:
            task_type: "regression" or "classification"

        Returns:
            Dict containing 'pipeline', 'metadata', 'feature_names', 'version'

        Raises:
            FileNotFoundError: If artifact is missing.
        """
        artifact_path = self.models_dir / task_type / "best_model.pkl"
        if not artifact_path.exists():
            # Fallback to legacy path if exists
            legacy_file = "ridge_regression_model.pkl" if task_type == "regression" else "risk_classifier_model.pkl"
            legacy_path = self.models_dir / legacy_file
            if legacy_path.exists():
                logger.warning("Using legacy artifact for %s: %s", task_type, legacy_path)
                model = joblib.load(legacy_path)
                return {
                    "pipeline": model,
                    "metadata": {"model_name": "LegacyModel", "task_type": task_type},
                    "feature_names": [],
                    "version": "legacy",
                }
            raise FileNotFoundError(f"Model bundle not found for {task_type} at {artifact_path}")

        return joblib.load(artifact_path)

    def load_pipeline(self, task_type: str) -> Any:
        """Loads just the fitted pipeline/model for the task type."""
        bundle = self.load_bundle(task_type)
        return bundle.get("pipeline", bundle)

    def get_metadata(self, task_type: str) -> Optional[ModelMetadata]:
        """Returns metadata for the active registered model."""
        reg_data = self.get_registry_data()
        item = reg_data.get(task_type)
        if item:
            return ModelMetadata.from_dict(item)
        return None
