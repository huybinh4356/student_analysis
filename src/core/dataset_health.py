"""
Dataset health assessment module for dataset-level quality analysis.
Detects missing data summary, invalid value ranges, outliers via IQR method,
and computes overall health status ('good' | 'warning' | 'critical').
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class DatasetHealthChecker:
    """
    Performs comprehensive dataset health checks for uploaded student datasets.
    """

    NUMERIC_RANGE_RULES = {
        "diem_thpt": (0.0, 30.0),
        "diem_gk": (0.0, 10.0),
        "diem_quiz": (0.0, 10.0),
        "diem_bai_tap": (0.0, 10.0),
        "diem_tong_ket": (0.0, 10.0),
        "lms_gio_truy_cap": (0.0, 500.0),
        "lms_xem_video": (0.0, 300.0),
        "nop_bai_dung_han": (0.0, 100.0),
        "chuyen_can": (0.0, 100.0),
        "muc_do_stress": (1.0, 5.0),
        "dong_luc_hoc": (1.0, 5.0),
    }

    def check(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes DataFrame for missing values, duplicates, out-of-range values, and outliers.

        Args:
            df: DataFrame to inspect.

        Returns:
            Dict[str, Any]: Comprehensive health summary dictionary.
        """
        if df.empty:
            return {
                "total_rows": 0,
                "total_cols": 0,
                "duplicate_rows": 0,
                "missing_summary": {},
                "invalid_values": {},
                "outlier_summary": {},
                "overall_status": "critical",
                "recommendations": ["File dữ liệu rỗng. Vui lòng tải lên file dữ liệu hợp lệ."],
            }

        total_rows = len(df)
        total_cols = len(df.columns)
        duplicate_rows = int(df.duplicated().sum())

        # 1. Missing data summary per column
        missing_summary: Dict[str, Dict[str, Any]] = {}
        total_missing_cells = 0

        for col in df.columns:
            null_cnt = int(df[col].isna().sum())
            if null_cnt > 0:
                pct = round((null_cnt / total_rows) * 100, 2)
                missing_summary[col] = {"count": null_cnt, "percentage": pct}
                total_missing_cells += null_cnt

        # 2. Invalid value range checks
        invalid_values: Dict[str, Dict[str, Any]] = {}
        total_invalid_cnt = 0

        for col, (min_val, max_val) in self.NUMERIC_RANGE_RULES.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                invalid_mask = (series < min_val) | (series > max_val)
                invalid_cnt = int(invalid_mask.sum())
                if invalid_cnt > 0:
                    invalid_values[col] = {
                        "count": invalid_cnt,
                        "min_found": float(series.min()) if not series.empty else 0,
                        "max_found": float(series.max()) if not series.empty else 0,
                        "expected_range": [min_val, max_val],
                    }
                    total_invalid_cnt += invalid_cnt

        # 3. IQR Outlier detection for numeric columns
        outlier_summary: Dict[str, Dict[str, Any]] = {}
        for col in self.NUMERIC_RANGE_RULES.keys():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if not series.empty:
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = series[(series < lower_bound) | (series > upper_bound)]
                    cnt = int(len(outliers))
                    if cnt > 0:
                        outlier_summary[col] = {
                            "count": cnt,
                            "percentage": round((cnt / total_rows) * 100, 2),
                            "lower_bound": round(float(lower_bound), 2),
                            "upper_bound": round(float(upper_bound), 2),
                        }

        # 4. Overall status determination
        overall_missing_pct = (total_missing_cells / (total_rows * total_cols)) * 100 if total_rows > 0 else 0

        if overall_missing_pct > 10.0 or total_invalid_cnt > 15:
            overall_status = "critical"
        elif overall_missing_pct > 2.0 or total_invalid_cnt > 0 or duplicate_rows > 5:
            overall_status = "warning"
        else:
            overall_status = "good"

        # 5. Actionable recommendations
        recommendations: List[str] = []
        if missing_summary:
            recommendations.append("Nên điền khuyết missing bằng Trung vị (Median) cho số và Yếu vị (Mode) cho phân loại.")
        if total_invalid_cnt > 0:
            recommendations.append(f"Có {total_invalid_cnt} bản ghi vượt khoảng hợp lệ. Cần chuẩn hóa về thang điểm [0, 10].")
        if duplicate_rows > 0:
            recommendations.append(f"Phát hiện {duplicate_rows} dòng dữ liệu trùng lặp hoàn toàn. Cần loại bỏ trùng lặp.")
        if outlier_summary:
            recommendations.append("Cân nhắc làm mịn (winsorize) các điểm ngoại lệ thời lượng LMS để tránh làm lệch mô hình.")
        if not recommendations:
            recommendations.append("Dữ liệu đạt chuẩn chất lượng cao. Sẵn sàng cho huấn luyện và phân tích.")

        return {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "duplicate_rows": duplicate_rows,
            "missing_summary": missing_summary,
            "invalid_values": invalid_values,
            "outlier_summary": outlier_summary,
            "overall_status": overall_status,
            "recommendations": recommendations,
        }
