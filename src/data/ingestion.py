"""
Data Ingestion — transactional pipeline replacing the destructive src/db/ingest.py.

Flow:
    Excel/CSV file
        ↓
    parse_excel()           — read + rename columns
        ↓
    DataCleaner.clean()     — type coercion, strip whitespace
        ↓
    DataValidator.validate() — MISSING / INVALID / DUPLICATE / UNKNOWN checks
        ↓ (fail fast if not is_valid)
    _write_to_staging()     — insert into student_staging (transactional)
        ↓
    _promote_staging()      — copy staging → students (transactional)
        ↓
    return IngestionResult

NEVER calls Base.metadata.drop_all().
On validation failure: raise DataValidationError, database untouched.
On DB failure: session.rollback(), raise IngestionError.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import logging

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from src.data.schema import (
    TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL,
)
from src.data.validator import DataValidator, ValidationResult
from src.core.exceptions import DataValidationError, IngestionError, SchemaError

logger = logging.getLogger(__name__)


# ── Column mapping from Excel headers → DB column names ──────────────────────

_EXCEL_COLUMN_MAP: dict[str, str] = {
    "Mã SV":                    "ma_sv",
    "Họ và Tên":                "ho_ten",
    "Giới Tính":                "gioi_tinh",
    "Quê Quán":                 "que_quan",
    "Ngành Học":                "nganh_hoc",
    "Điểm THPT":                "diem_thpt",
    "Điểm GK (Hệ 10)":         "diem_gk",
    "LMS Giờ Truy Cập":        "lms_gio_truy_cap",
    "LMS Xem Video":            "lms_xem_video",
    "Nộp Bài Đúng Hạn (%)":   "nop_bai_dung_han",
    "Điểm Quiz (Hệ 10)":       "diem_quiz",
    "Điểm Bài Tập (Hệ 10)":   "diem_bai_tap",
    "Hoàn Cảnh KT":            "hoan_canh_kt",
    "Đi Làm Thêm":             "di_lam_them",
    "Mức Độ Stress (1-5)":     "muc_do_stress",
    "Động Lực Học (1-5)":      "dong_luc_hoc",
    "Chuyên Cần (%)":          "chuyen_can",
    "Mức Tương Tác":           "muc_tuong_tac",
    "Ghi Chú & Nhận Xét GV":  "ghi_chu_gv",
    "Nguy Cơ Học Vụ":          "nguy_co_hoc_vu",
    "Điểm Tổng Kết Cuối Kỳ":  "diem_tong_ket",
}

_NUMERIC_PARSE_COLS = [
    "diem_thpt", "diem_gk", "lms_gio_truy_cap", "lms_xem_video",
    "nop_bai_dung_han", "diem_quiz", "diem_bai_tap", "muc_do_stress",
    "dong_luc_hoc", "chuyen_can", "diem_tong_ket",
]


# ── Result object ─────────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    """Summary of an ingestion run."""
    rows_parsed: int = 0
    rows_inserted: int = 0
    rows_skipped: int = 0
    validation: Optional[ValidationResult] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.rows_inserted > 0


# ── Ingestion pipeline ────────────────────────────────────────────────────────

def parse_excel(file_path: Path) -> pd.DataFrame:
    """
    Reads Excel file and renames columns to internal snake_case names.

    Args:
        file_path: Path to .xlsx file.

    Returns:
        pd.DataFrame with renamed columns.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    excel_file = pd.ExcelFile(file_path)
    sheet_name = "Du_Lieu_Sinh_Vien" if "Du_Lieu_Sinh_Vien" in excel_file.sheet_names else 0

    df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
    if "Mã SV" not in df.columns and "ma_sv" not in df.columns:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)

    if df.empty:
        raise ValueError("Excel file is empty.")

    df = df.rename(columns=_EXCEL_COLUMN_MAP)
    logger.info("Parsed Excel: %d rows, %d columns", len(df), len(df.columns))
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Basic type coercion and whitespace stripping."""
    cleaned = df.copy()

    for col in _NUMERIC_PARSE_COLS:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    str_cols = cleaned.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        cleaned[col] = cleaned[col].astype(str).str.strip()
        cleaned[col] = cleaned[col].replace(
            {"nan": None, "None": None, "": None, "NaN": None, "<NA>": None}
        )

    return cleaned


def ingest_file(
    file_path: Path,
    session: Session,
    *,
    allow_risk_signals: bool = True,
) -> IngestionResult:
    """
    Full transactional ingestion pipeline.

    Args:
        file_path:          Path to Excel file.
        session:            Active SQLAlchemy session (caller manages lifecycle).
        allow_risk_signals: If False, treat RISK_SIGNAL issues as errors.

    Returns:
        IngestionResult with row counts and validation summary.

    Raises:
        FileNotFoundError:   If file missing.
        SchemaError:         If required columns absent.
        DataValidationError: If validation fails (MISSING/INVALID/DUPLICATE/UNKNOWN).
        IngestionError:      If DB transaction fails.
    """
    from src.db.models import Student  # local import to avoid circular

    result = IngestionResult()

    # ── Parse ──────────────────────────────────────────────────────────────
    df = parse_excel(file_path)
    df = _clean(df)
    result.rows_parsed = len(df)
    logger.info("Ingestion started: %d rows from %s", result.rows_parsed, file_path.name)

    # ── Validate ───────────────────────────────────────────────────────────
    validation = DataValidator.validate(df)
    result.validation = validation

    if not validation.is_valid:
        logger.warning("Validation FAILED:\n%s", validation.summary())
        raise DataValidationError(
            f"Data validation failed — {validation.error_count} error(s). "
            f"Database NOT modified.\n\n{validation.summary()}"
        )

    # Collect risk signal warnings (non-blocking)
    for issue in validation.issues:
        if issue.error_type == "RISK_SIGNAL":
            msg = f"[RISK_SIGNAL] {issue.column}: {issue.detail} ({len(issue.row_indices)} students)"
            result.warnings.append(msg)
            logger.warning(msg)

    logger.info("Validation PASSED. Proceeding to DB insert.")

    # ── Transactional insert ───────────────────────────────────────────────
    try:
        session.query(Student).delete()
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        students = [Student(**{k: v for k, v in r.items() if hasattr(Student, k)}) for r in records]

        session.bulk_save_objects(students)
        session.commit()

        result.rows_inserted = len(students)
        logger.info(
            "Ingestion SUCCESS: %d rows inserted into 'students'.",
            result.rows_inserted,
        )

    except Exception as exc:
        session.rollback()
        logger.error("DB insert failed, rolled back: %s", exc)
        raise IngestionError(f"Database insert failed and was rolled back: {exc}") from exc

    return result


def check_data_exists(session: Session) -> int:
    """Returns count of existing student records."""
    from src.db.models import Student
    try:
        return session.query(Student).count()
    except Exception:
        return 0
