"""
Custom exception hierarchy for the Student Analysis Platform v3.

All modules must raise these typed exceptions instead of bare Exception.
UI/service layers catch these to show user-facing messages.

Usage:
    from src.core.exceptions import PredictionError, DataValidationError
    raise PredictionError("Model artifact missing or incompatible.")
"""


class StudentAnalysisError(Exception):
    """Base exception for all platform errors."""


# ── Data Layer ──────────────────────────────────────────────────────────────

class DataValidationError(StudentAnalysisError):
    """Raised when uploaded data fails schema or quality validation."""


class SchemaError(DataValidationError):
    """Raised when required columns are missing or have wrong dtype."""


class InvalidRangeError(DataValidationError):
    """Raised when a value is outside its defined valid range."""


class DuplicateDataError(DataValidationError):
    """Raised when duplicate student IDs or rows are detected."""


class TargetMissingError(DataValidationError):
    """Raised when target column (diem_tong_ket / nguy_co_hoc_vu) has nulls."""


# ── Database Layer ───────────────────────────────────────────────────────────

class DatabaseError(StudentAnalysisError):
    """Raised for database connection or transaction failures."""


class IngestionError(DatabaseError):
    """Raised when data ingestion into PostgreSQL fails."""


# ── ML Layer ────────────────────────────────────────────────────────────────

class TrainingError(StudentAnalysisError):
    """Raised when model training fails (e.g. insufficient data, bad config)."""


class ModelNotFoundError(StudentAnalysisError):
    """Raised when a required model artifact does not exist on disk."""


class ModelCompatibilityError(StudentAnalysisError):
    """Raised when a loaded model is incompatible with current feature schema."""


class LeakageGuardError(StudentAnalysisError):
    """Raised when a banned leakage feature is detected in the pipeline."""


# ── Prediction / Service Layer ───────────────────────────────────────────────

class PredictionError(StudentAnalysisError):
    """
    Raised when prediction cannot be completed.

    Do NOT fall back to a heuristic formula.
    Surface this to the UI as "Prediction unavailable".
    """


class WhatIfError(StudentAnalysisError):
    """Raised when a What-If simulation fails (e.g. infeasible target)."""


class InfeasibleTargetError(WhatIfError):
    """Raised when the target score cannot be reached even with max interventions."""


# ── Report Layer ─────────────────────────────────────────────────────────────

class ReportGenerationError(StudentAnalysisError):
    """Raised when report rendering or export fails."""


class MetricsMissingError(ReportGenerationError):
    """Raised when metrics.json / registry.json does not exist yet (no training run)."""
