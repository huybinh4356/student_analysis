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
    gioi_tinh = Column(String(20), nullable=False)
    que_quan = Column(String(100), nullable=False)
    nganh_hoc = Column(String(100), nullable=False)
    diem_thpt = Column(Float, nullable=False)
    diem_gk = Column(Float, nullable=False)
    lms_gio_truy_cap = Column(Float, nullable=False)
    lms_xem_video = Column(Integer, nullable=False)
    nop_bai_dung_han = Column(Float, nullable=False)
    diem_quiz = Column(Float, nullable=False)
    diem_bai_tap = Column(Float, nullable=False)
    hoan_canh_kt = Column(String(50), nullable=False)
    di_lam_them = Column(String(50), nullable=False)
    muc_do_stress = Column(Integer, nullable=False)
    dong_luc_hoc = Column(Integer, nullable=False)
    chuyen_can = Column(Float, nullable=False)
    muc_tuong_tac = Column(String(50), nullable=False)
    ghi_chu_gv = Column(Text, nullable=True)
    nguy_co_hoc_vu = Column(String(50), nullable=False)
    diem_tong_ket = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Student(ma_sv={self.ma_sv}, ho_ten='{self.ho_ten}', nguy_co='{self.nguy_co_hoc_vu}')>"
