"""
Data Contract — canonical schema for the student dataset.

Single source of truth for column names, types, ranges, and roles.
All other modules (validator, ingestion, ML pipeline) import from here.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ColumnSpec:
    """Specification for a single dataset column."""
    name: str
    dtype: str                      # "float", "int", "str", "category"
    nullable: bool = True
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    allowed_values: Optional[tuple] = None  # for category columns
    role: str = "feature"           # "feature" | "target" | "id" | "text"
    used_at_predict: bool = True
    notes: str = ""


# ── Identity columns ─────────────────────────────────────────────────────────

ID_COLS: list[ColumnSpec] = [
    ColumnSpec("ma_sv",  dtype="str", nullable=False, role="id",   used_at_predict=False),
    ColumnSpec("ho_ten", dtype="str", nullable=True,  role="id",   used_at_predict=False),
]

# ── Numeric feature columns ───────────────────────────────────────────────────

NUMERIC_COLS: list[ColumnSpec] = [
    ColumnSpec("diem_thpt",       dtype="float", min_val=0.0,  max_val=30.0),
    ColumnSpec("diem_gk",         dtype="float", min_val=0.0,  max_val=10.0),
    ColumnSpec("diem_quiz",       dtype="float", min_val=0.0,  max_val=10.0),
    ColumnSpec("diem_bai_tap",    dtype="float", min_val=0.0,  max_val=10.0),
    ColumnSpec("lms_gio_truy_cap",dtype="float", min_val=0.0,  max_val=500.0),
    ColumnSpec("lms_xem_video",   dtype="float", min_val=0.0,  max_val=1000.0),
    ColumnSpec("nop_bai_dung_han",dtype="float", min_val=0.0,  max_val=100.0),
    ColumnSpec("muc_do_stress",   dtype="float", min_val=1.0,  max_val=5.0),
    ColumnSpec("dong_luc_hoc",    dtype="float", min_val=1.0,  max_val=5.0),
    ColumnSpec("chuyen_can",      dtype="float", min_val=0.0,  max_val=100.0),
]

# ── Ordinal feature columns ───────────────────────────────────────────────────

ORDINAL_COLS: list[ColumnSpec] = [
    ColumnSpec(
        "hoan_canh_kt",
        dtype="category",
        allowed_values=("Khó khăn", "Trung bình", "Khá giả"),
        notes="Hoàn cảnh kinh tế",
    ),
    ColumnSpec(
        "muc_tuong_tac",
        dtype="category",
        allowed_values=("Thụ động", "Bình thường", "Tích cực"),
        notes="Mức tương tác lớp học",
    ),
]

ORDINAL_MAPPINGS: dict[str, dict[str, int]] = {
    "hoan_canh_kt":  {"Khó khăn": 1, "Trung bình": 2, "Khá giả": 3},
    "muc_tuong_tac": {"Thụ động": 1, "Bình thường": 2, "Tích cực": 3},
    "nguy_co_hoc_vu":{"Rất thấp": 1, "Thấp": 2, "Trung bình": 3, "Cao": 4},
}

# ── Nominal feature columns ───────────────────────────────────────────────────

NOMINAL_COLS: list[ColumnSpec] = [
    ColumnSpec("gioi_tinh",  dtype="category", allowed_values=("Nam", "Nữ")),
    ColumnSpec("que_quan",   dtype="str"),
    ColumnSpec("nganh_hoc",  dtype="str"),
    ColumnSpec("di_lam_them",dtype="category", allowed_values=("Có", "Không")),
]

# ── Text columns (excluded from model) ───────────────────────────────────────

TEXT_COLS: list[ColumnSpec] = [
    ColumnSpec("ghi_chu_gv", dtype="str", role="text", used_at_predict=False),
]

# ── Target columns ────────────────────────────────────────────────────────────

TARGET_COLS: list[ColumnSpec] = [
    ColumnSpec(
        "diem_tong_ket",
        dtype="float",
        nullable=False,
        min_val=0.0,
        max_val=10.0,
        role="target",
        used_at_predict=False,
        notes="Regression target — điểm tổng kết cuối kỳ thực tế",
    ),
    ColumnSpec(
        "nguy_co_hoc_vu",
        dtype="category",
        nullable=False,
        allowed_values=("Rất thấp", "Thấp", "Trung bình", "Cao"),
        role="target",
        used_at_predict=False,
        notes="Classification target — nhãn nguy cơ học vụ thực tế",
    ),
]

# ── Leakage banned features ───────────────────────────────────────────────────

LEAKAGE_BANNED_FEATURES: set[str] = {
    "composite_exam_score",  # R²=0.938 vs diem_tong_ket — audit 2026-10-04
}

# ── Convenience lookups ───────────────────────────────────────────────────────

ALL_SPECS: dict[str, ColumnSpec] = {
    spec.name: spec
    for group in [ID_COLS, NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS, TEXT_COLS, TARGET_COLS]
    for spec in group
}

REQUIRED_COLS: list[str] = [
    spec.name for spec in (ID_COLS + NUMERIC_COLS + ORDINAL_COLS + NOMINAL_COLS + TARGET_COLS)
    if not spec.nullable
]

FEATURE_COLS: list[str] = [
    spec.name for spec in (NUMERIC_COLS + ORDINAL_COLS + NOMINAL_COLS)
]

TARGET_REGRESSION: str = "diem_tong_ket"
TARGET_CLASSIFICATION: str = "nguy_co_hoc_vu"
ID_COL: str = "ma_sv"

# ── Risk class definitions ────────────────────────────────────────────────────

RISK_CLASSES: dict[str, dict] = {
    "Rất thấp": {"ordinal": 1, "color": "#10b981", "label_vi": "Rất thấp (Học lực Giỏi/Xuất sắc)"},
    "Thấp":     {"ordinal": 2, "color": "#3b82f6", "label_vi": "Thấp (Học lực Khá)"},
    "Trung bình":{"ordinal": 3, "color": "#f59e0b", "label_vi": "Trung bình (Cần cố gắng)"},
    "Cao":      {"ordinal": 4, "color": "#ef4444", "label_vi": "Cao (Có nguy cơ học vụ)"},
}
