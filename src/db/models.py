"""
SQLAlchemy ORM models for Student Performance Analysis System.
"""

from sqlalchemy import Column, Integer, BigInteger, String, Float, Text
from src.db.connection import Base


class Student(Base):
    """
    Student model representing student profile, LMS activity, survey metrics, 
    and target labels.
    """
    __tablename__ = "students"

    ma_sv = Column(BigInteger, primary_key=True, index=True)
    ho_ten = Column(String(150), nullable=False)
    gioi_tinh = Column(String(20), nullable=True)
    que_quan = Column(String(100), nullable=True)
    nganh_hoc = Column(String(100), nullable=True)
    diem_thpt = Column(Float, nullable=True)
    diem_gk = Column(Float, nullable=True)
    lms_gio_truy_cap = Column(Float, nullable=True)
    lms_xem_video = Column(Float, nullable=True)
    nop_bai_dung_han = Column(Float, nullable=True)
    diem_quiz = Column(Float, nullable=True)
    diem_bai_tap = Column(Float, nullable=True)
    hoan_canh_kt = Column(String(50), nullable=True)
    di_lam_them = Column(String(50), nullable=True)
    muc_do_stress = Column(Float, nullable=True)
    dong_luc_hoc = Column(Float, nullable=True)
    chuyen_can = Column(Float, nullable=True)
    muc_tuong_tac = Column(String(50), nullable=True)
    ghi_chu_gv = Column(Text, nullable=True)
    nguy_co_hoc_vu = Column(String(50), nullable=True)
    diem_tong_ket = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Student(ma_sv={self.ma_sv}, ho_ten='{self.ho_ten}', nguy_co='{self.nguy_co_hoc_vu}')>"
