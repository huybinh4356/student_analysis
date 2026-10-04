"""
Leakage Audit Script — Phase 1
Kiểm tra correlation giữa composite_exam_score và diem_tong_ket
để xác định mức độ feature leakage.

Chạy: python scripts/audit_leakage.py
"""

from pathlib import Path
import sys

import pandas as pd
import numpy as np

# Locate Excel file
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
excel_files = list(DATA_DIR.glob("*.xlsx"))

if not excel_files:
    print("[LOI] Khong tim thay file Excel trong data/")
    sys.exit(1)

excel_path = excel_files[0]
print(f"File: {excel_path.name}\n")

# Read data
excel_file = pd.ExcelFile(excel_path)
sheet_name = "Du_Lieu_Sinh_Vien" if "Du_Lieu_Sinh_Vien" in excel_file.sheet_names else 0

df = pd.read_excel(excel_path, sheet_name=sheet_name, header=1)
if "Mã SV" not in df.columns and "ma_sv" not in df.columns:
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=0)

# Rename columns
column_mapping = {
    "Mã SV": "ma_sv", "Họ và Tên": "ho_ten", "Giới Tính": "gioi_tinh",
    "Quê Quán": "que_quan", "Ngành Học": "nganh_hoc", "Điểm THPT": "diem_thpt",
    "Điểm GK (Hệ 10)": "diem_gk", "LMS Giờ Truy Cập": "lms_gio_truy_cap",
    "LMS Xem Video": "lms_xem_video", "Nộp Bài Đúng Hạn (%)": "nop_bai_dung_han",
    "Điểm Quiz (Hệ 10)": "diem_quiz", "Điểm Bài Tập (Hệ 10)": "diem_bai_tap",
    "Hoàn Cảnh KT": "hoan_canh_kt", "Đi Làm Thêm": "di_lam_them",
    "Mức Độ Stress (1-5)": "muc_do_stress", "Động Lực Học (1-5)": "dong_luc_hoc",
    "Chuyên Cần (%)": "chuyen_can", "Mức Tương Tác": "muc_tuong_tac",
    "Ghi Chú & Nhận Xét GV": "ghi_chu_gv", "Nguy Cơ Học Vụ": "nguy_co_hoc_vu",
    "Điểm Tổng Kết Cuối Kỳ": "diem_tong_ket",
}
df = df.rename(columns=column_mapping)

# Convert numeric
for col in ["diem_gk", "diem_quiz", "diem_bai_tap", "diem_tong_ket", "chuyen_can"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

print(f"{'='*60}")
print(f"DATASET OVERVIEW")
print(f"{'='*60}")
print(f"Rows       : {len(df):,}")
print(f"Columns    : {len(df.columns)}")
print(f"Missing diem_tong_ket : {df['diem_tong_ket'].isna().sum()}")
print(f"Missing diem_gk       : {df['diem_gk'].isna().sum()}")
print()

# ── LEAKAGE AUDIT ──────────────────────────────────────────
print(f"{'='*60}")
print(f"LEAKAGE AUDIT — composite_exam_score vs diem_tong_ket")
print(f"{'='*60}")

# Recreate composite_exam_score as feature engineer does
valid = df[["diem_gk", "diem_quiz", "diem_bai_tap", "diem_tong_ket"]].dropna()
valid = valid.copy()
valid["composite_exam_score"] = (
    0.4 * valid["diem_gk"]
    + 0.3 * valid["diem_quiz"]
    + 0.3 * valid["diem_bai_tap"]
)

# Pearson correlation
corr = valid["composite_exam_score"].corr(valid["diem_tong_ket"])
r2_approx = corr ** 2

print(f"\ncomposite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT")
print(f"  Pearson r  : {corr:.4f}")
print(f"  R² (approx): {r2_approx:.4f}  ({r2_approx*100:.1f}%)")
print()

# Individual feature correlations with target
print("Individual feature correlations with diem_tong_ket:")
print(f"  {'Feature':<30} {'Pearson r':>10} {'R²':>8}")
print(f"  {'-'*50}")
for feat in ["diem_gk", "diem_quiz", "diem_bai_tap", "chuyen_can", "diem_thpt"]:
    if feat in df.columns:
        v = df[["diem_tong_ket", feat]].dropna()
        v[feat] = pd.to_numeric(v[feat], errors="coerce")
        v = v.dropna()
        r = v[feat].corr(v["diem_tong_ket"])
        print(f"  {feat:<30} {r:>10.4f} {r**2:>8.4f}")

print()

# Verdict
print(f"{'='*60}")
print("VERDICT")
print(f"{'='*60}")
if r2_approx > 0.90:
    print(f"[LEAKAGE SEVERE]  (R²={r2_approx:.3f} > 0.90)")
    print("   composite_exam_score là proxy gần như hoàn hảo của target.")
    print("   -> PHẢI loại bỏ composite_exam_score khỏi feature set.")
    print("   -> R²=94% trong README nhiều khả năng là giả tạo.")
elif r2_approx > 0.80:
    print(f"[LEAKAGE LIKELY]   (R²={r2_approx:.3f} > 0.80)")
    print("   composite_exam_score có thể tạo ra metric inflation.")
    print("   -> Cân nhắc loại bỏ, dùng GK/Quiz/BT riêng lẻ.")
elif r2_approx > 0.70:
    print(f"[LEAKAGE POSSIBLE] (R²={r2_approx:.3f} > 0.70)")
    print("   composite_exam_score là feature mạnh nhưng chưa phải leakage thuần túy.")
    print("   -> Giữ nhưng theo dõi; đặt tên rõ ràng hơn.")
else:
    print(f"[LEAKAGE UNLIKELY] (R²={r2_approx:.3f} <= 0.70)")
    print("   composite_exam_score không phải proxy của target.")
    print("   -> Giữ feature, R²=94% có nghĩa thực sự.")

print()

# ── TARGET DISTRIBUTION ────────────────────────────────────
print(f"{'='*60}")
print(f"TARGET DISTRIBUTION")
print(f"{'='*60}")
print("\ndiem_tong_ket:")
print(df["diem_tong_ket"].describe().to_string())

if "nguy_co_hoc_vu" in df.columns:
    print("\nnguy_co_hoc_vu (class distribution):")
    counts = df["nguy_co_hoc_vu"].value_counts()
    for cls, cnt in counts.items():
        pct = cnt / len(df) * 100
        print(f"  {cls:<20}: {cnt:>4} ({pct:.1f}%)")

print()
print("[DONE] Audit complete. Update docs/data_dictionary.md với kết quả trên.")
