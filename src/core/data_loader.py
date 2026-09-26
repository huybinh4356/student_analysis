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
        Loads dataset directly from Excel file.

        Args:
            file_path: Path to Excel spreadsheet.

        Returns:
            pd.DataFrame: Student records.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        df = pd.read_excel(file_path, sheet_name="Du_Lieu_Sinh_Vien", header=1)
        return df
