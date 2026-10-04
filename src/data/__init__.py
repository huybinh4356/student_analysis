"""src/data/__init__.py — Data governance package."""

from src.data.schema import (
    ALL_SPECS, FEATURE_COLS, TARGET_REGRESSION, TARGET_CLASSIFICATION,
    ID_COL, LEAKAGE_BANNED_FEATURES, RISK_CLASSES,
)
from src.data.validator import DataValidator, ValidationResult, ValidationIssue
from src.data.quality import DatasetHealth, compute_health
from src.data.ingestion import ingest_file, parse_excel, IngestionResult

__all__ = [
    "ALL_SPECS", "FEATURE_COLS", "TARGET_REGRESSION", "TARGET_CLASSIFICATION",
    "ID_COL", "LEAKAGE_BANNED_FEATURES", "RISK_CLASSES",
    "DataValidator", "ValidationResult", "ValidationIssue",
    "DatasetHealth", "compute_health",
    "ingest_file", "parse_excel", "IngestionResult",
]
