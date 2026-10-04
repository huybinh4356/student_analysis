"""
Data Quality report — computes dataset-level health metrics.

Output:
    DatasetHealth dataclass with rates and overall_status.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import pandas as pd

from src.data.schema import NUMERIC_COLS, TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL


@dataclass
class DatasetHealth:
    """Dataset-level health metrics (all rates, not absolute counts)."""
    total_rows: int
    total_cols: int

    # Rate metrics (0.0 – 1.0)
    missing_rate: float         # null cells / (rows × numeric_cols)
    invalid_rate: float         # out-of-range values / rows
    duplicate_row_rate: float   # fully duplicate rows / rows
    duplicate_id_rate: float    # rows with dup student IDs / rows
    target_missing_rate: float  # null target rows / rows
    low_attendance_rate: float  # attendance < 50% / rows

    schema_status: Literal["OK", "INCOMPLETE"]
    overall_status: Literal["HEALTHY", "WARNING", "CRITICAL"]

    def as_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "total_cols": self.total_cols,
            "missing_rate": round(self.missing_rate, 4),
            "invalid_rate": round(self.invalid_rate, 4),
            "duplicate_row_rate": round(self.duplicate_row_rate, 4),
            "duplicate_id_rate": round(self.duplicate_id_rate, 4),
            "target_missing_rate": round(self.target_missing_rate, 4),
            "low_attendance_rate": round(self.low_attendance_rate, 4),
            "schema_status": self.schema_status,
            "overall_status": self.overall_status,
        }


def compute_health(df: pd.DataFrame) -> DatasetHealth:
    """
    Computes dataset health metrics from a cleaned DataFrame.

    Args:
        df: Cleaned student DataFrame (post-rename, post-coercion).

    Returns:
        DatasetHealth with all rates computed.
    """
    n = len(df)
    if n == 0:
        return DatasetHealth(
            total_rows=0, total_cols=len(df.columns),
            missing_rate=1.0, invalid_rate=0.0,
            duplicate_row_rate=0.0, duplicate_id_rate=0.0,
            target_missing_rate=1.0, low_attendance_rate=0.0,
            schema_status="INCOMPLETE", overall_status="CRITICAL",
        )

    num_col_names = [s.name for s in NUMERIC_COLS if s.name in df.columns]

    # Missing rate across numeric feature columns
    if num_col_names:
        missing_cells = df[num_col_names].isna().sum().sum()
        missing_rate = missing_cells / (n * len(num_col_names))
    else:
        missing_rate = 0.0

    # Invalid rate: numeric values outside schema range
    invalid_count = 0
    for spec in NUMERIC_COLS:
        if spec.name not in df.columns:
            continue
        col = pd.to_numeric(df[spec.name], errors="coerce")
        if spec.min_val is not None:
            invalid_count += (col < spec.min_val).sum()
        if spec.max_val is not None:
            invalid_count += (col > spec.max_val).sum()
    invalid_rate = invalid_count / n

    # Duplicate rows
    dup_rows = df.duplicated(keep=False).sum()
    duplicate_row_rate = dup_rows / n

    # Duplicate IDs
    dup_ids = df.duplicated(subset=[ID_COL], keep=False).sum() if ID_COL in df.columns else 0
    duplicate_id_rate = dup_ids / n

    # Target missing
    target_null = 0
    for col in [TARGET_REGRESSION, TARGET_CLASSIFICATION]:
        if col in df.columns:
            target_null = max(target_null, df[col].isna().sum())
    target_missing_rate = target_null / n

    # Low attendance
    low_att = 0
    if "chuyen_can" in df.columns:
        low_att = (pd.to_numeric(df["chuyen_can"], errors="coerce") < 50.0).sum()
    low_attendance_rate = low_att / n

    # Schema status
    required = [s.name for s in NUMERIC_COLS] + [TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL]
    schema_status: Literal["OK", "INCOMPLETE"] = (
        "OK" if all(c in df.columns for c in required) else "INCOMPLETE"
    )

    # Overall status
    if (
        schema_status == "INCOMPLETE"
        or missing_rate > 0.20
        or invalid_rate > 0.10
        or target_missing_rate > 0.05
    ):
        overall_status: Literal["HEALTHY", "WARNING", "CRITICAL"] = "CRITICAL"
    elif missing_rate > 0.05 or invalid_rate > 0.02 or duplicate_id_rate > 0.01:
        overall_status = "WARNING"
    else:
        overall_status = "HEALTHY"

    return DatasetHealth(
        total_rows=n,
        total_cols=len(df.columns),
        missing_rate=missing_rate,
        invalid_rate=invalid_rate,
        duplicate_row_rate=duplicate_row_rate,
        duplicate_id_rate=duplicate_id_rate,
        target_missing_rate=target_missing_rate,
        low_attendance_rate=low_attendance_rate,
        schema_status=schema_status,
        overall_status=overall_status,
    )
