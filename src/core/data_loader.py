"""
Data Loader Module for loading student data from PostgreSQL or Excel.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.db.repositories import StudentRepository


class DataLoader:
    """Utility class to load student dataset from DB or Excel source."""

    @staticmethod
    def load_from_db() -> pd.DataFrame:
        """
        Loads dataset directly from PostgreSQL database.

        Returns:
            pd.DataFrame: Student records.
        """
        repo = StudentRepository()
        try:
            df = repo.get_all_students_df()
            return df
        finally:
            repo.close()

    @staticmethod
    def load_from_excel(file_path: Path) -> pd.DataFrame:
        """
        Loads dataset directly from Excel file with automated header detection and column normalization.

        Args:
            file_path: Path to Excel spreadsheet.

        Returns:
            pd.DataFrame: Student records with canonical column names.
        """
        from src.data.ingestion import parse_excel
        return parse_excel(file_path)

    @staticmethod
    def load_data(file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Convenience method to load student dataset.
        Attempts loading from PostgreSQL DB first; if empty or fails, falls back to Excel.

        Args:
            file_path: Optional path to Excel file.

        Returns:
            pd.DataFrame: Loaded student DataFrame.
        """
        try:
            df = DataLoader.load_from_db()
            if not df.empty:
                return df
        except Exception:
            pass

        if file_path is None:
            file_path = Path(__file__).resolve().parents[2] / "data" / "du_lieu_sinh_vien_tong_hop.xlsx"

        if file_path.exists():
            return DataLoader.load_from_excel(file_path)

        return pd.DataFrame()

