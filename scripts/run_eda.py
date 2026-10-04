"""
Comprehensive Exploratory Data Analysis (EDA) Script.
Calculates summary stats, distributions, correlation matrix, and VIF metrics.
"""

import sys
import io
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure root path is in sys.path
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Ensure UTF-8 printing
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.core.data_loader import DataLoader
from src.core.schema_detector import SchemaDetector


def run_eda():
    print("==================================================================")
    print("   HỆ THỐNG PHÂN TÍCH KẾT QUẢ HỌC TẬP — BÁO CÁO EDA CHI TIẾT   ")
    print("==================================================================\n")

    # 1. Load data from PostgreSQL
    df = DataLoader.load_from_db()
    print(f"1. TỔNG QUAN DỮ LIỆU:")
    print(f"   - Số lượng sinh viên: {len(df):,} bản ghi")
    print(f"   - Số lượng cột/biến: {df.shape[1]} cột")
    print(f"   - Tổng số giá trị Missing: {df.isnull().sum().sum()}")
    print(f"   - Số bản ghi trùng lặp (Duplicates): {df.duplicated(subset=['ma_sv']).sum()}\n")

    schema = SchemaDetector.get_feature_schema()

    # 2. Continuous Variables Statistics
    print("2. THỐNG KÊ MÔ TẢ BIẾN ĐỊNH LƯỢNG (NUMERIC):")
    numeric_df = df[schema["numeric"] + [SchemaDetector.TARGET_REGRESSION]]
    stats_summary = []
    for col in numeric_df.columns:
        series = numeric_df[col]
        stats_summary.append({
            "Biến": col,
            "Mean": round(series.mean(), 2),
            "Std": round(series.std(), 2),
            "Min": round(series.min(), 2),
            "Median": round(series.median(), 2),
            "Max": round(series.max(), 2),
            "Skewness": round(series.skew(), 2),
            "Kurtosis": round(series.kurtosis(), 2)
        })
    stats_df = pd.DataFrame(stats_summary)
    print(stats_df.to_string(index=False))
    print("\n")

    # 3. Categorical Variables Distributions
    print("3. PHÂN PHỐI BIẾN PHÂN LOẠI & TARGET:")
    print("--- Target 1: Nguy Cơ Học Vụ (Classification Target) ---")
    cls_dist = df[SchemaDetector.TARGET_CLASSIFICATION].value_counts(normalize=False)
    cls_pct = df[SchemaDetector.TARGET_CLASSIFICATION].value_counts(normalize=True) * 100
    for category in ["Rất thấp", "Thấp", "Trung bình", "Cao"]:
        cnt = cls_dist.get(category, 0)
        pct = cls_pct.get(category, 0.0)
        print(f"   - {category:<12}: {cnt:>4} SV ({pct:>5.1f}%)")

    print("\n--- Biến Phân Loại Khảo Sát & Ghi Chú ---")
    print(f"   - Giới tính    : Nam ({sum(df['gioi_tinh']=='Nam')}), Nữ ({sum(df['gioi_tinh']=='Nữ')})")
    print(f"   - Hoàn cảnh KT : {dict(df['hoan_canh_kt'].value_counts())}")
    print(f"   - Đi làm thêm  : {dict(df['di_lam_them'].value_counts())}")
    print(f"   - Mức tương tác: {dict(df['muc_tuong_tac'].value_counts())}\n")

    # 4. Correlation & Data Leakage Verification (R-DATA-03)
    print("4. PHÂN TÍCH TƯƠNG QUAN & KIỂM TRA DATA LEAKAGE (R-DATA-03):")
    # Encode target classification for correlation check
    encoded_df = numeric_df.copy()
    encoded_df["nguy_co_encoded"] = df[SchemaDetector.TARGET_CLASSIFICATION].map(
        SchemaDetector.ORDINAL_MAPPINGS["nguy_co_hoc_vu"]
    )

    corr_matrix = encoded_df.corr()
    print("   * Tương quan Pearson với DiemTongKet (Regression Target):")
    corr_reg = corr_matrix["diem_tong_ket"].sort_values(ascending=False)
    for var, val in corr_reg.items():
        if var != "diem_tong_ket":
            flag = "[CANH BAO LEAKAGE (>0.95)]" if abs(val) > 0.95 else "OK"
            print(f"     - {var:<20}: {val:>6.3f} [{flag}]")

    print("\n   * Tương quan Pearson với NguyCoHocVu Encoded (Classification Target):")
    corr_cls = corr_matrix["nguy_co_encoded"].sort_values(ascending=False)
    for var, val in corr_cls.items():
        if var != "nguy_co_encoded":
            flag = "[CANH BAO LEAKAGE (>0.95)]" if abs(val) > 0.95 else "OK"
            print(f"     - {var:<20}: {val:>6.3f} [{flag}]")
    print("\n")

    # 5. Multicollinearity Analysis (VIF)
    print("5. PHÂN TÍCH ĐA CỘNG TUYẾN (VARIANCE INFLATION FACTOR - VIF):")
    vif_features = numeric_df[schema["numeric"]].dropna()
    vif_data = pd.DataFrame()
    vif_data["Feature"] = vif_features.columns
    vif_data["VIF"] = [
        round(variance_inflation_factor(vif_features.values, i), 2)
        for i in range(vif_features.shape[1])
    ]
    print(vif_data.sort_values(by="VIF", ascending=False).to_string(index=False))
    print("\n==================================================================")


if __name__ == "__main__":
    run_eda()
