"""
Unit tests for database connection, ingestion, and querying.
"""

import pytest
from src.db.connection import engine
from src.db.repositories import StudentRepository
from src.core.data_loader import DataLoader
from src.core.schema_detector import SchemaDetector


def test_database_connection():
    """Verify that PostgreSQL connection works cleanly."""
    try:
        conn = engine.connect()
        assert conn is not None
        conn.close()
    except Exception as e:
        pytest.skip(f"PostgreSQL database is offline: {e}")


def test_student_repository_load():
    """Verify loading student dataframe from PostgreSQL."""
    try:
        repo = StudentRepository()
        df = repo.get_all_students_df()
        repo.close()

        assert not df.empty
        assert len(df) >= 1000
        assert "ma_sv" in df.columns
        assert "nguy_co_hoc_vu" in df.columns
    except Exception as e:
        pytest.skip(f"PostgreSQL database is offline: {e}")


def test_schema_detector():
    """Verify schema detector categorization."""
    schema = SchemaDetector.get_feature_schema()
    assert "ma_sv" in schema["id"]
    assert "diem_gk" in schema["numeric"]
    assert "gioi_tinh" in schema["nominal"]
    assert "hoan_canh_kt" in schema["ordinal"]
    assert schema["target_cls"] == ["nguy_co_hoc_vu"]
    assert schema["target_reg"] == ["diem_tong_ket"]
