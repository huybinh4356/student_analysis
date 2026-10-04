"""
Data Loader Module for loading student data from PostgreSQL or Excel.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.db.repositories import StudentRepository


class DataLoader:
    """Utility class to load student dataset from DB or Excel source with in-memory caching."""

    _cached_df: Optional[pd.DataFrame] = None
    _db_available: Optional[bool] = None

    @classmethod
    def clear_cache(cls):
        """Clears memory cache to force re-reading from source."""
        cls._cached_df = None
        cls._db_available = None

    @classmethod
    def load_from_db(cls) -> pd.DataFrame:
        """
        Loads dataset directly from PostgreSQL database.

        Returns:
            pd.DataFrame: Student records.
        """
        if cls._db_available is False:
            return pd.DataFrame()

        repo = StudentRepository()
        try:
            df = repo.get_all_students_df()
            cls._db_available = True
            return df
        except Exception:
            cls._db_available = False
            return pd.DataFrame()
        finally:
            repo.close()

    @classmethod
    def load_from_excel(cls, file_path: Path) -> pd.DataFrame:
        """
        Loads dataset directly from Excel file with automated header detection and column normalization.

        Args:
            file_path: Path to Excel spreadsheet.

        Returns:
            pd.DataFrame: Student records with canonical column names.
        """
        from src.data.ingestion import parse_excel
        return parse_excel(file_path)

    @classmethod
    def load_data(cls, file_path: Optional[Path] = None, force_reload: bool = False) -> pd.DataFrame:
        """
        Convenience method to load student dataset with in-memory caching.
        Attempts loading from PostgreSQL DB first; if empty or offline, falls back to Excel.
        Subsequent calls return cached copy instantly.

        Args:
            file_path: Optional path to Excel file.
            force_reload: Force re-reading from source bypassing cache.

        Returns:
            pd.DataFrame: Loaded student DataFrame.
        """
        if not force_reload and cls._cached_df is not None and not cls._cached_df.empty:
            return cls._cached_df.copy()

        # 1. Try DB if not known to be offline
        if cls._db_available is not False:
            try:
                df = cls.load_from_db()
                if not df.empty:
                    cls._cached_df = df
                    return cls._cached_df.copy()
            except Exception:
                cls._db_available = False

        # 2. Fallback to local Excel file
        if file_path is None:
            file_path = Path(__file__).resolve().parents[2] / "data" / "du_lieu_sinh_vien_tong_hop.xlsx"

        if file_path.exists():
            df = cls.load_from_excel(file_path)
            cls._cached_df = df
            return cls._cached_df.copy()

        return pd.DataFrame()

