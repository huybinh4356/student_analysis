# MIGRATIONS — Quản lý phiên bản schema

## 1. Tại sao cần migrations?

Khi dự án phát triển, schema sẽ thay đổi:

- Thêm cột mới (ví dụ: `email`).
- Đổi kiểu dữ liệu.
- Thêm bảng.

**Không dùng migrations:**

- Phải drop và tạo lại DB mỗi lần đổi → mất data.
- Không có lịch sử thay đổi.
- Không rollback được.

**Dùng migrations:**

- Thay đổi có kiểm soát.
- Có lịch sử.
- Rollback được.

## 2. Cài đặt Alembic

```cmd
pip install alembic
3. Khởi tạo Alembic
Từ thư mục gốc dự án:

cmd
cd src
alembic init alembic
Cấu trúc tạo ra:

text
src/
├── alembic/
│   ├── versions/          ← Chứa các file migration
│   ├── env.py            ← Cấu hình
│   ├── script.py.mako    ← Template
│   └── README
└── alembic.ini           ← Config chính
4. Cấu hình alembic.ini
Mở file src/alembic.ini, sửa dòng:

ini
sqlalchemy.url = driver://user:pass@localhost/dbname
Thành:

ini
# Để trống, sẽ đọc từ env.py
sqlalchemy.url =
5. Cấu hình alembic/env.py
Mở file src/alembic/env.py, sửa:

python
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
from pathlib import Path

# Load .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Đọc URL từ .env
DB_URL = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
config.set_main_option('sqlalchemy.url', DB_URL)

# Import Base từ models
from src.db.models import Base
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
6. Tạo file src/db/models.py
Đây là SQLAlchemy models tương ứng với schema DB:

python
"""SQLAlchemy models cho dự án."""
from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, TIMESTAMP,
    ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    ma_sv = Column(String(20), unique=True, nullable=False)
    ho_ten = Column(String(100), nullable=False)
    gioi_tinh = Column(String(10))
    que_quan = Column(String(50))
    nganh_hoc = Column(String(50))
    diem_thpt = Column(Float)
    diem_gk = Column(Float)
    lms_gio_truy_cap = Column(Float)
    lms_xem_video = Column(Integer)
    nop_bai_dung_han = Column(Float)
    diem_quiz = Column(Float)
    diem_bai_tap = Column(Float)
    hoan_canh_kt = Column(String(20))
    di_lam_them = Column(String(20))
    muc_do_stress = Column(Integer)
    dong_luc_hoc = Column(Integer)
    chuyen_can = Column(Float)
    muc_tuong_tac = Column(String(20))
    ghi_chu_gv = Column(Text)
    nguy_co_hoc_vu = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    predictions = relationship("Prediction", back_populates="student")
    insights = relationship("Insight", back_populates="student")


class ModelRun(Base):
    __tablename__ = 'model_runs'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(50), nullable=False)
    model_type = Column(String(20), nullable=False)
    target = Column(String(50), nullable=False)
    n_features = Column(Integer)
    n_samples = Column(Integer)
    r2_score = Column(Float)
    rmse = Column(Float)
    mae = Column(Float)
    accuracy = Column(Float)
    f1_score = Column(Float)
    hyperparams = Column(JSON)
    model_path = Column(String(255))
    trained_at = Column(TIMESTAMP, server_default=func.now())
    notes = Column(Text)

    predictions = relationship("Prediction", back_populates="model_run")


class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'))
    model_run_id = Column(Integer, ForeignKey('model_runs.id'))
    predicted_score = Column(Float)
    predicted_risk = Column(String(20))
    confidence = Column(Float)
    prediction_interval_low = Column(Float)
    prediction_interval_high = Column(Float)
    is_anomaly = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship("Student", back_populates="predictions")
    model_run = relationship("ModelRun", back_populates="predictions")


class Insight(Base):
    __tablename__ = 'insights'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'))
    insight_type = Column(String(50), nullable=False)
    category = Column(String(50))
    message = Column(Text, nullable=False)
    severity = Column(String(20))
    action_suggestion = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship("Student", back_populates="insights")


class AnalysisLog(Base):
    __tablename__ = 'analysis_logs'

    id = Column(Integer, primary_key=True)
    action = Column(String(100), nullable=False)
    user_session = Column(String(100))
    details = Column(JSON)
    duration_ms = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
7. Tạo migration đầu tiên
Vì bảng đã tồn tại (tạo từ init_db.sql), ta cần đánh dấu Alembic rằng schema hiện tại đã match. Chạy:

cmd
cd src
alembic stamp head
Sau đó, từ lần sau mới tạo migration mới:

cmd
alembic revision --autogenerate -m "Initial schema"
8. Tạo migration khi có thay đổi
Ví dụ: Thêm cột email vào bảng students
Bước 1: Sửa src/db/models.py:

python
class Student(Base):
    # ...
    email = Column(String(100))  # Thêm dòng này
Bước 2: Tạo migration:

cmd
cd src
alembic revision --autogenerate -m "Add email column to students"
Alembic sẽ tạo file trong alembic/versions/:

python
"""Add email column to students

Revision ID: abc123
Revises: def456
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('students', sa.Column('email', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('students', 'email')
Bước 3: Áp dụng:

cmd
alembic upgrade head
9. Các lệnh Alembic thường dùng
cmd
:: Xem version hiện tại
alembic current

:: Xem lịch sử
alembic history

:: Lên version mới nhất
alembic upgrade head

:: Lên 1 version
alembic upgrade +1

:: Xuống 1 version
alembic downgrade -1

:: Xuống version cụ thể
alembic downgrade abc123

:: Xem SQL mà migration sẽ chạy (không apply)
alembic upgrade head --sql

:: Đánh dấu version hiện tại (không chạy migration)
alembic stamp head
10. Ví dụ migration phức tạp
Thêm cột có giá trị mặc định
python
def upgrade():
    op.add_column('students',
        sa.Column('diem_tong_ket', sa.Float(), nullable=True))

    # Cập nhật giá trị cho dữ liệu cũ
    op.execute("""
        UPDATE students
        SET diem_tong_ket = 0.4 * diem_gk + 0.3 * diem_quiz + 0.3 * diem_bai_tap
    """)

def downgrade():
    op.drop_column('students', 'diem_tong_ket')
Đổi tên cột
python
def upgrade():
    op.alter_column('students', 'ma_sv', new_column_name='mssv')

def downgrade():
    op.alter_column('students', 'mssv', new_column_name='ma_sv')
Thêm index
python
def upgrade():
    op.create_index('idx_students_email', 'students', ['email'])

def downgrade():
    op.drop_index('idx_students_email', table_name='students')
Thêm bảng mới
python
def upgrade():
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(),
                  sa.ForeignKey('students.id', ondelete='CASCADE')),
        sa.Column('content', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('notes')
11. Workflow chuẩn
cmd
:: 1. Sửa models.py
:: 2. Tạo migration
cd src
alembic revision --autogenerate -m "Mô tả thay đổi"

:: 3. Kiểm tra file migration vừa tạo trong alembic/versions/
:: 4. Test trên DB local
alembic upgrade head

:: 5. Kiểm tra DB
docker exec -it student_db psql -U postgres -d student_analysis -c "\d students"

:: 6. Nếu OK, commit file migration
git add src/alembic/versions/
git commit -m "[feat] Add email column"
12. Best practices
Nguyên tắc Chi tiết
Mỗi migration = 1 thay đổi Không gộp nhiều thay đổi vào 1 file
Luôn có downgrade() Phải rollback được
Test trên DB riêng Không test trên production
Backup trước upgrade pg_dump trước khi upgrade
Đặt tên rõ ràng add_composite_score không phải update_1
Không sửa migration cũ Tạo migration mới để sửa
Commit migration cùng code Migration và models phải đồng bộ
Không drop cột ngay Đánh dấu deprecated, xóa sau vài version
13. Troubleshooting
Lỗi Nguyên nhân Cách sửa
Target database is not up to date Migration chưa chạy alembic upgrade head
Can't locate revision File migration bị xóa Restore từ git
Multiple heads Có nhiều nhánh migration alembic merge heads
Duplicate column Cột đã tồn tại alembic stamp head để đánh dấu
Cannot drop column Có FK constraint Xóa FK trước
