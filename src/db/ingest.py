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
    Cleans raw dataframe: strips string whitespace, coercively casts numeric types.
    Preserves raw NULL/missing values without auto-imputing fabricated data into the database.

    Args:
        df: Raw DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    cleaned = df.copy()

    # 1. Convert numerical columns safely (invalid values coerced to NaN)
    numeric_cols = [
        "diem_thpt", "diem_gk", "lms_gio_truy_cap", "lms_xem_video",
        "nop_bai_dung_han", "diem_quiz", "diem_bai_tap", "muc_do_stress",
        "dong_luc_hoc", "chuyen_can", "diem_tong_ket"
    ]
    for c in numeric_cols:
        if c in cleaned.columns:
            cleaned[c] = pd.to_numeric(cleaned[c], errors='coerce')

    # 2. Strip string whitespace and treat empty / nan string as None
    string_cols = cleaned.select_dtypes(include=['object', 'string']).columns
    for c in string_cols:
        cleaned[c] = cleaned[c].astype(str).str.strip()
        cleaned[c] = cleaned[c].replace({"nan": None, "None": None, "": None, "NaN": None, "<NA>": None})

    return cleaned


def check_data_exists() -> bool:
    """Checks if database has existing student records."""
    try:
        Base.metadata.create_all(bind=engine)
        db: Session = SessionLocal()
        count = db.query(Student).count()
        db.close()
        return count > 0
    except Exception:
        return False


def ingest_excel_to_db(file_path: Path, force: bool = False) -> int:
    """
    Reads student dataset from Excel file, cleans data, and populates PostgreSQL.
    If force=False and database already contains data, skips re-ingestion for fast startup.

    Args:
        file_path: Path to Excel data file.
        force: If True, forces dropping tables and re-ingesting data.

    Returns:
        int: Number of records in database.

    Raises:
        FileNotFoundError: If Excel file does not exist.
        ValueError: If Excel data is empty or invalid.
    """
    if not force and check_data_exists():
        db: Session = SessionLocal()
        count = db.query(Student).count()
        db.close()
        print(f"Database already contains {count} records. Skipping re-ingestion for fast startup.")
        return count

    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found at path: {file_path}")

    # Flexible sheet reading (supports 'Du_Lieu_Sinh_Vien' or first sheet, header 0 or 1)
    excel_file = pd.ExcelFile(file_path)
    sheet_name = "Du_Lieu_Sinh_Vien" if "Du_Lieu_Sinh_Vien" in excel_file.sheet_names else 0

    df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
    if "Mã SV" not in df.columns and "ma_sv" not in df.columns:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)

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

    # Ensure schema exists without dropping tables (DB-001)
    Base.metadata.create_all(bind=engine)

    # Convert DataFrame to list of dicts, setting all nulls/NaN to None for SQL NULL
    records = cleaned_df.where(pd.notnull(cleaned_df), None).to_dict(orient="records")
    students = [Student(**{k: v for k, v in r.items() if hasattr(Student, k)}) for r in records]

    db: Session = SessionLocal()
    try:
        # Transactional replacement: delete and insert within the same transaction (DB-003)
        db.query(Student).delete()
        db.bulk_save_objects(students)
        db.commit()
        inserted_count = db.query(Student).count()
        return inserted_count
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database insertion failed (transaction rolled back): {str(e)}") from e
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    force_ingest = "--force" in sys.argv
    data_file = Path(__file__).resolve().parents[2] / "data" / "du_lieu_sinh_vien_tong_hop.xlsx"
    count = ingest_excel_to_db(data_file, force=force_ingest)
    print(f"Successfully verified/ingested {count} student records into PostgreSQL database!")

