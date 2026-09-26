"""
Repository pattern for querying Student data from PostgreSQL.
"""

from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.db.models import Student
from src.db.connection import engine, SessionLocal


class StudentRepository:
    """Repository providing data access operations for Student entities."""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()

    def get_all_students_df(self) -> pd.DataFrame:
        """
        Retrieves all student records from PostgreSQL into a pandas DataFrame.

        Returns:
            pd.DataFrame: Complete student dataset.
        """
        query = self.db.query(Student)
        df = pd.read_sql(query.statement, engine)
        return df

    def get_student_by_id(self, ma_sv: int) -> Optional[Student]:
        """
        Finds a student by primary key ID.

        Args:
            ma_sv: Student ID number.

        Returns:
            Optional[Student]: Student ORM object if found, else None.
        """
        return self.db.query(Student).filter(Student.ma_sv == ma_sv).first()

    def close(self):
        """Closes session."""
        if self.db:
            self.db.close()
