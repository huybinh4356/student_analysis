"""
Schema Detector Module for automatically categorizing feature types and target columns.
"""

from typing import Dict, List
import pandas as pd


class SchemaDetector:
    """Detects and categorizes column types in the student dataset."""

    ID_COLS = ["ma_sv", "ho_ten"]
    TARGET_CLASSIFICATION = "nguy_co_hoc_vu"
    TARGET_REGRESSION = "diem_tong_ket"
    TEXT_COLS = ["ghi_chu_gv"]

    ORDINAL_MAPPINGS = {
        "hoan_canh_kt": {"Khó khăn": 1, "Trung bình": 2, "Khá giả": 3},
        "muc_tuong_tac": {"Thụ động": 1, "Bình thường": 2, "Tích cực": 3},
        "nguy_co_hoc_vu": {"Rất thấp": 1, "Thấp": 2, "Trung bình": 3, "Cao": 4},
    }

    NOMINAL_COLS = ["gioi_tinh", "que_quan", "nganh_hoc", "di_lam_them"]

    NUMERIC_COLS = [
        "diem_thpt",
        "diem_gk",
        "lms_gio_truy_cap",
        "lms_xem_video",
        "nop_bai_dung_han",
        "diem_quiz",
        "diem_bai_tap",
        "muc_do_stress",
        "dong_luc_hoc",
        "chuyen_can",
    ]

    @classmethod
    def get_feature_schema(cls) -> Dict[str, List[str]]:
        """
        Returns dictionary of column categories.

        Returns:
            Dict[str, List[str]]: Feature type mapping.
        """
        return {
            "id": cls.ID_COLS,
            "numeric": cls.NUMERIC_COLS,
            "nominal": cls.NOMINAL_COLS,
            "ordinal": list(cls.ORDINAL_MAPPINGS.keys()),
            "text": cls.TEXT_COLS,
            "target_cls": [cls.TARGET_CLASSIFICATION],
            "target_reg": [cls.TARGET_REGRESSION],
        }
