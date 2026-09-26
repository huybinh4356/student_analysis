"""
Data ingestion script for populating PostgreSQL database from Excel source.
Includes automated data cleaning, missing value imputation (R-DATA-05), and data type validation.
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from src.db.connection import engine, Base, SessionLocal
from src.db.models import Student


def clean_and_impute_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw dataframe: strips string whitespace, coercively casts types,
    and imputes missing values (median for numeric, mode for categorical - R-DATA-05).

    Args:
        df: Raw DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    cleaned = df.copy()

    # 1. Strip string whitespace
    string_cols = cleaned.select_dtypes(include=['object', 'string']).columns
    for c in string_cols:
        cleaned[c] = cleaned[c].astype(str).str.strip()

    # 2. Convert numerical columns safely
    numeric_cols = [
        "diem_thpt", "diem_gk", "lms_gio_truy_cap", "lms_xem_video",
        "nop_bai_dung_han", "diem_quiz", "diem_bai_tap", "muc_do_stress",
        "dong_luc_hoc", "chuyen_can", "diem_tong_ket"
    ]
    for c in numeric_cols:
        if c in cleaned.columns:
            cleaned[c] = pd.to_numeric(cleaned[c], errors='coerce')
            # Impute missing with median (R-DATA-05)
            median_val = cleaned[c].median()
            if pd.isna(median_val):
                median_val = 5.0
            cleaned[c] = cleaned[c].fillna(median_val)

    # 3. Categorical missing imputation with mode (R-DATA-05)
    categorical_cols = ["gioi_tinh", "que_quan", "nganh_hoc", "hoan_canh_kt", "di_lam_them", "muc_tuong_tac", "nguy_co_hoc_vu"]
    for c in categorical_cols:
        if c in cleaned.columns:
            mode_val = cleaned[c].mode()[0] if not cleaned[c].mode().empty else "Bình thường"
            cleaned[c] = cleaned[c].fillna(mode_val)

    # 4. Fill missing notes
    if "ghi_chu_gv" in cleaned.columns:
        cleaned["ghi_chu_gv"] = cleaned["ghi_chu_gv"].fillna("Có ý thức học tập.")

    return cleaned


def ingest_excel_to_db(file_path: Path) -> int:
    """
    Reads student dataset from Excel file, cleans data, and populates PostgreSQL.

    Args:
        file_path: Path to Excel data file.

    Returns:
        int: Number of records inserted.

    Raises:
        FileNotFoundError: If Excel file does not exist.
        ValueError: If Excel data is empty or invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found at path: {file_path}")

    # Read sheet with header at index 1
    df = pd.read_excel(file_path, sheet_name="Du_Lieu_Sinh_Vien", header=1)
    if df.empty:
        raise ValueError("Excel file is empty")

    column_mapping = {
        "Mã SV": "ma_sv",
        "Họ và Tên": "ho_ten",
        "Giới Tính": "gioi_tinh",
        "Quê Quán": "que_quan",
        "Ngành Học": "nganh_hoc",
        "Điểm THPT": "diem_thpt",
        "Điểm GK (Hệ 10)": "diem_gk",
        "LMS Giờ Truy Cập": "lms_gio_truy_cap",
        "LMS Xem Video": "lms_xem_video",
        "Nộp Bài Đúng Hạn (%)": "nop_bai_dung_han",
        "Điểm Quiz (Hệ 10)": "diem_quiz",
        "Điểm Bài Tập (Hệ 10)": "diem_bai_tap",
        "Hoàn Cảnh KT": "hoan_canh_kt",
        "Đi Làm Thêm": "di_lam_them",
        "Mức Độ Stress (1-5)": "muc_do_stress",
        "Động Lực Học (1-5)": "dong_luc_hoc",
        "Chuyên Cần (%)": "chuyen_can",
        "Mức Tương Tác": "muc_tuong_tac",
        "Ghi Chú & Nhận Xét GV": "ghi_chu_gv",
        "Nguy Cơ Học Vụ": "nguy_co_hoc_vu",
        "Điểm Tổng Kết Cuối Kỳ": "diem_tong_ket",
    }

    df_renamed = df.rename(columns=column_mapping)
    cleaned_df = clean_and_impute_data(df_renamed)

    # Re-create database schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Convert DataFrame to list of Student ORM objects
    students = [Student(**row.to_dict()) for _, row in cleaned_df.iterrows()]

    db: Session = SessionLocal()
    try:
        db.bulk_save_objects(students)
        db.commit()
        inserted_count = db.query(Student).count()
        return inserted_count
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database insertion failed: {str(e)}") from e
    finally:
        db.close()


if __name__ == "__main__":
    data_file = Path(__file__).resolve().parents[2] / "data" / "du_lieu_sinh_vien_tong_hop.xlsx"
    count = ingest_excel_to_db(data_file)
    print(f"Successfully ingested {count} student records into PostgreSQL database!")
