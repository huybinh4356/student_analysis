"""
Data Validator — validates uploaded student DataFrame before ingestion.

Error classification:
    MISSING   — required value is null/NaN
    INVALID   — value is wrong type or outside valid range
    DUPLICATE — duplicate student ID or duplicate row
    UNKNOWN   — category value not in allowed set
    RISK_SIGNAL — not an error, but a warning worth flagging (e.g. very low attendance)

Usage:
    from src.data.validator import DataValidator
    result = DataValidator.validate(df)
    if not result.is_valid:
        raise DataValidationError(result.summary())
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import pandas as pd

from src.data.schema import (
    ALL_SPECS, NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS, TARGET_COLS,
    ID_COL, TARGET_REGRESSION, TARGET_CLASSIFICATION,
)
from src.core.exceptions import DataValidationError, SchemaError


# ── Error record ──────────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    """A single validation finding."""
    error_type: str      # MISSING | INVALID | DUPLICATE | UNKNOWN | RISK_SIGNAL
    column: str
    row_indices: List[int]
    detail: str

    def __str__(self) -> str:
        n = len(self.row_indices)
        sample = self.row_indices[:5]
        return f"[{self.error_type}] {self.column}: {self.detail} ({n} row(s), e.g. {sample})"


@dataclass
class ValidationResult:
    """Aggregated result of a full validation run."""
    total_rows: int
    issues: List[ValidationIssue] = field(default_factory=list)

    # Aggregate rates (computed in validate())
    missing_rate: float = 0.0
    invalid_rate: float = 0.0
    duplicate_rate: float = 0.0
    unknown_rate: float = 0.0

    @property
    def is_valid(self) -> bool:
        """True only if no MISSING / INVALID / DUPLICATE / UNKNOWN errors."""
        blocking = {"MISSING", "INVALID", "DUPLICATE", "UNKNOWN"}
        return not any(i.error_type in blocking for i in self.issues)

    @property
    def error_count(self) -> int:
        blocking = {"MISSING", "INVALID", "DUPLICATE", "UNKNOWN"}
        return sum(len(i.row_indices) for i in self.issues if i.error_type in blocking)

    def summary(self) -> str:
        lines = [
            f"Validation result: {'PASS' if self.is_valid else 'FAIL'}",
            f"  Total rows  : {self.total_rows:,}",
            f"  Missing rate: {self.missing_rate:.2%}",
            f"  Invalid rate: {self.invalid_rate:.2%}",
            f"  Duplicate rt: {self.duplicate_rate:.2%}",
            f"  Unknown rate: {self.unknown_rate:.2%}",
            "",
        ]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


# ── Validator ────────────────────────────────────────────────────────────────

class DataValidator:
    """
    Validates a student DataFrame against the data contract in src/data/schema.py.

    Checks (in order):
        1. Required columns present
        2. Missing values in non-nullable columns
        3. Numeric range violations
        4. Unknown category values
        5. Duplicate student IDs
        6. Duplicate rows
        7. Target column completeness
        8. Risk signals (low attendance, high stress)
    """

    # Risk signal thresholds
    _LOW_ATTENDANCE_THRESHOLD = 50.0
    _HIGH_STRESS_THRESHOLD = 4.0

    @classmethod
    def validate(cls, df: pd.DataFrame) -> ValidationResult:
        """
        Runs full validation on the DataFrame.

        Args:
            df: Cleaned DataFrame (after column renaming, basic type coercion).

        Returns:
            ValidationResult with all issues found.

        Raises:
            SchemaError: If required columns are missing (cannot continue).
        """
        result = ValidationResult(total_rows=len(df))
        missing_cells = 0
        invalid_cells = 0
        duplicate_cells = 0
        unknown_cells = 0

        # ── 1. Schema: required columns present ──────────────────────────
        all_required = (
            [s.name for s in NUMERIC_COLS]
            + [s.name for s in ORDINAL_COLS]
            + [s.name for s in TARGET_COLS]
            + [ID_COL]
        )
        missing_cols = [c for c in all_required if c not in df.columns]
        if missing_cols:
            raise SchemaError(
                f"Required columns missing from dataset: {missing_cols}. "
                "Cannot proceed with validation."
            )

        n = len(df)

        # ── 2. Missing values (non-nullable columns) ──────────────────────
        non_nullable = [
            s for s in list(NUMERIC_COLS) + list(TARGET_COLS)
            if not s.nullable and s.name in df.columns
        ]
        for spec in non_nullable:
            null_idx = df[df[spec.name].isna()].index.tolist()
            if null_idx:
                result.issues.append(ValidationIssue(
                    error_type="MISSING",
                    column=spec.name,
                    row_indices=null_idx,
                    detail=f"Non-nullable column has {len(null_idx)} null value(s)",
                ))
                missing_cells += len(null_idx)

        # ── 3. Numeric range violations ───────────────────────────────────
        for spec in NUMERIC_COLS:
            if spec.name not in df.columns:
                continue
            col = pd.to_numeric(df[spec.name], errors="coerce")
            if spec.min_val is not None:
                below = df[col < spec.min_val].index.tolist()
                if below:
                    result.issues.append(ValidationIssue(
                        error_type="INVALID",
                        column=spec.name,
                        row_indices=below,
                        detail=f"Value below minimum {spec.min_val}",
                    ))
                    invalid_cells += len(below)
            if spec.max_val is not None:
                above = df[col > spec.max_val].index.tolist()
                if above:
                    result.issues.append(ValidationIssue(
                        error_type="INVALID",
                        column=spec.name,
                        row_indices=above,
                        detail=f"Value above maximum {spec.max_val}",
                    ))
                    invalid_cells += len(above)

        # ── 4. Target range validation ────────────────────────────────────
        if TARGET_REGRESSION in df.columns:
            col = pd.to_numeric(df[TARGET_REGRESSION], errors="coerce")
            bad = df[(col < 0) | (col > 10)].index.tolist()
            if bad:
                result.issues.append(ValidationIssue(
                    error_type="INVALID",
                    column=TARGET_REGRESSION,
                    row_indices=bad,
                    detail="Target score outside [0, 10]",
                ))
                invalid_cells += len(bad)

        # ── 5. Unknown category values ────────────────────────────────────
        for spec in list(ORDINAL_COLS) + list(NOMINAL_COLS):
            if spec.allowed_values is None or spec.name not in df.columns:
                continue
            bad_idx = df[~df[spec.name].isin(spec.allowed_values) & df[spec.name].notna()].index.tolist()
            if bad_idx:
                unique_bad = df.loc[bad_idx, spec.name].unique().tolist()[:5]
                result.issues.append(ValidationIssue(
                    error_type="UNKNOWN",
                    column=spec.name,
                    row_indices=bad_idx,
                    detail=f"Values not in allowed set: {unique_bad}",
                ))
                unknown_cells += len(bad_idx)

        # Target classification
        if TARGET_CLASSIFICATION in df.columns:
            valid_risk = {"Rất thấp", "Thấp", "Trung bình", "Cao"}
            bad_idx = df[~df[TARGET_CLASSIFICATION].isin(valid_risk) & df[TARGET_CLASSIFICATION].notna()].index.tolist()
            if bad_idx:
                result.issues.append(ValidationIssue(
                    error_type="UNKNOWN",
                    column=TARGET_CLASSIFICATION,
                    row_indices=bad_idx,
                    detail=f"Risk label not in {valid_risk}",
                ))
                unknown_cells += len(bad_idx)

        # ── 6. Duplicate student IDs ─────────────────────────────────────
        if ID_COL in df.columns:
            dup_mask = df.duplicated(subset=[ID_COL], keep=False)
            dup_idx = df[dup_mask].index.tolist()
            if dup_idx:
                result.issues.append(ValidationIssue(
                    error_type="DUPLICATE",
                    column=ID_COL,
                    row_indices=dup_idx,
                    detail=f"{len(dup_idx)} rows share duplicate student IDs",
                ))
                duplicate_cells += len(dup_idx)

        # ── 7. Duplicate rows ─────────────────────────────────────────────
        dup_rows = df.duplicated(keep=False)
        dup_row_idx = df[dup_rows].index.tolist()
        if dup_row_idx:
            result.issues.append(ValidationIssue(
                error_type="DUPLICATE",
                column="(all columns)",
                row_indices=dup_row_idx,
                detail=f"{len(dup_row_idx)} fully duplicate rows detected",
            ))
            duplicate_cells += len(dup_row_idx)

        # ── 8. Risk signals (warnings only) ──────────────────────────────
        if "chuyen_can" in df.columns:
            low_att = df[pd.to_numeric(df["chuyen_can"], errors="coerce") < cls._LOW_ATTENDANCE_THRESHOLD].index.tolist()
            if low_att:
                result.issues.append(ValidationIssue(
                    error_type="RISK_SIGNAL",
                    column="chuyen_can",
                    row_indices=low_att,
                    detail=f"Attendance below {cls._LOW_ATTENDANCE_THRESHOLD}% — early warning",
                ))

        if "muc_do_stress" in df.columns:
            high_stress = df[pd.to_numeric(df["muc_do_stress"], errors="coerce") >= cls._HIGH_STRESS_THRESHOLD].index.tolist()
            if high_stress:
                result.issues.append(ValidationIssue(
                    error_type="RISK_SIGNAL",
                    column="muc_do_stress",
                    row_indices=high_stress,
                    detail=f"Stress level >= {cls._HIGH_STRESS_THRESHOLD} — psychological support may be needed",
                ))

        # ── Compute aggregate rates ───────────────────────────────────────
        result.missing_rate   = missing_cells   / (n * len(NUMERIC_COLS)) if n > 0 else 0.0
        result.invalid_rate   = invalid_cells   / n if n > 0 else 0.0
        result.duplicate_rate = duplicate_cells / n if n > 0 else 0.0
        result.unknown_rate   = unknown_cells   / n if n > 0 else 0.0

        return result
