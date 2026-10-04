# SETUP POSTGRESQL 18 + DOCKER

## 0. Thông tin môi trường

| Trường | Giá trị |
|--------|---------|
| PostgreSQL | 18 (Alpine) |
| Container | `student_db` |
| Host | `localhost` |
| Port | `5432` |
| Database | `student_analysis` |
| User | `postgres` |
| Password | `123456` |
| Docker Desktop | Bắt buộc |

## 1. Cài Docker Desktop

### Windows

1. Tải Docker Desktop: https://www.docker.com/products/docker-desktop
2. Chạy file cài đặt → Next → Next → Install.
3. Khởi động lại máy nếu được yêu cầu.
4. Mở Docker Desktop → chấp nhận điều khoản.
5. Chờ Docker engine khởi động (icon cá voi ở taskbar chuyển xanh).

**Kiểm tra:**
```cmd
docker --version
docker-compose --version
Kết quả mong đợi:

text
Docker version 27.x.x
Docker Compose version v2.x.x
Lưu ý: Docker Desktop cần bật WSL2 trên Windows. Nếu chưa có, Docker sẽ hướng dẫn cài.

macOS
bash
brew install --cask docker
Linux (Ubuntu)
bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Logout và login lại
2. Cấu trúc thư mục cần tạo
text
student-analysis-app/
├── docker-compose.yml       ← File cấu hình Docker
├── .env                     ← Biến môi trường
├── scripts/
│   └── init_db.sql         ← Script khởi tạo DB
├── data/
│   └── du_lieu_sinh_vien_tong_hop.xlsx
└── src/
    └── db/
        ├── connection.py   ← Kết nối PostgreSQL
        └── ingest.py       ← Đọc Excel → insert DB
Tạo thư mục:

cmd
mkdir scripts src\db data
3. Tạo file docker-compose.yml
Đặt tại thư mục gốc dự án:

yaml
version: '3.8'

services:
  postgres:
    image: postgres:18-alpine
    container_name: student_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: student_analysis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 12345678
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d student_analysis"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
Giải thích chi tiết:

Dòng	Ý nghĩa
image: postgres:18-alpine	Dùng PostgreSQL 18 bản Alpine (nhẹ ~80MB)
container_name: student_db	Đặt tên container cố định
restart: unless-stopped	Tự khởi động lại khi máy reboot
POSTGRES_DB	Tên database tạo tự động
POSTGRES_USER	User mặc định
POSTGRES_PASSWORD	Password của user
ports: "5432:5432"	Map port host:container
volumes (thứ 1)	Lưu dữ liệu bền vững
volumes (thứ 2)	Mount file init_db.sql vào container
healthcheck	Kiểm tra DB sẵn sàng
4. Tạo file .env
Đặt tại thư mục gốc:

env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_analysis
DB_USER=postgres
DB_PASSWORD=12345678
Thêm vào .gitignore:

text
.env
__pycache__/
*.pyc
models/*.pkl
*.sql
!scripts/init_db.sql
5. Tạo file scripts/init_db.sql
Đây là script tự động chạy khi container khởi động lần đầu. Nội dung đầy đủ (copy từ schema.md):

sql
-- Chạy tự động khi container PostgreSQL khởi động lần đầu
-- Nếu sửa file này: docker-compose down -v && docker-compose up -d

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Bảng sinh viên
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    ma_sv VARCHAR(20) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    gioi_tinh VARCHAR(10),
    que_quan VARCHAR(50),
    nganh_hoc VARCHAR(50),
    diem_thpt FLOAT,
    diem_gk FLOAT,
    lms_gio_truy_cap FLOAT,
    lms_xem_video INTEGER,
    nop_bai_dung_han FLOAT,
    diem_quiz FLOAT,
    diem_bai_tap FLOAT,
    hoan_canh_kt VARCHAR(20),
    di_lam_them VARCHAR(20),
    muc_do_stress INTEGER,
    dong_luc_hoc INTEGER,
    chuyen_can FLOAT,
    muc_tuong_tac VARCHAR(20),
    ghi_chu_gv TEXT,
    nguy_co_hoc_vu VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bảng lịch sử training
CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    model_type VARCHAR(20) NOT NULL,
    target VARCHAR(50) NOT NULL,
    n_features INTEGER,
    n_samples INTEGER,
    r2_score FLOAT,
    rmse FLOAT,
    mae FLOAT,
    accuracy FLOAT,
    f1_score FLOAT,
    hyperparams JSONB,
    model_path VARCHAR(255),
    trained_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Bảng kết quả dự đoán
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    model_run_id INTEGER REFERENCES model_runs(id),
    predicted_score FLOAT,
    predicted_risk VARCHAR(20),
    confidence FLOAT,
    prediction_interval_low FLOAT,
    prediction_interval_high FLOAT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng insights
CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    message TEXT NOT NULL,
    severity VARCHAR(20),
    action_suggestion TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng log
CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_session VARCHAR(100),
    details JSONB,
    duration_ms INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_ma_sv ON students(ma_sv);
CREATE INDEX IF NOT EXISTS idx_students_nganh ON students(nganh_hoc);
CREATE INDEX IF NOT EXISTS idx_students_nguy_co ON students(nguy_co_hoc_vu);
CREATE INDEX IF NOT EXISTS idx_predictions_student ON predictions(student_id);
CREATE INDEX IF NOT EXISTS idx_predictions_risk ON predictions(predicted_risk);
CREATE INDEX IF NOT EXISTS idx_predictions_run ON predictions(model_run_id);
CREATE INDEX IF NOT EXISTS idx_insights_student ON insights(student_id);
CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_severity ON insights(severity);
CREATE INDEX IF NOT EXISTS idx_model_runs_type ON model_runs(model_type);
CREATE INDEX IF NOT EXISTS idx_model_runs_trained_at ON model_runs(trained_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_action ON analysis_logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_created ON analysis_logs(created_at DESC);

-- Trigger cập nhật updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_students_updated ON students;
CREATE TRIGGER trg_students_updated
BEFORE UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
6. Khởi động Docker
Mở terminal tại thư mục gốc dự án:

cmd
docker-compose up -d
Output mong đợi:

text
Creating network "student-analysis-app_default" ...
Creating volume "student-analysis-app_postgres_data" ...
Creating student_db ... done
Chờ container healthy:

cmd
docker-compose logs -f postgres
Chờ đến khi thấy dòng:

text
LOG:  database system is ready to accept connections
Nhấn Ctrl+C để thoát khỏi log.

Kiểm tra trạng thái:

cmd
docker ps
Output:

text
CONTAINER ID   IMAGE                  STATUS                    PORTS
abc123...      postgres:18-alpine     Up 2 minutes (healthy)    0.0.0.0:5432->5432/tcp
Chú ý (healthy) — nghĩa là DB sẵn sàng.

7. Kiểm tra bảng đã tạo
cmd
docker exec -it student_db psql -U postgres -d student_analysis -c "\dt"
Output:

text
            List of relations
 Schema |     Name       | Type  |  Owner
--------+----------------+-------+----------
 public | analysis_logs  | table | postgres
 public | insights       | table | postgres
 public | model_runs     | table | postgres
 public | predictions    | table | postgres
 public | students       | table | postgres
Nếu thấy đủ 5 bảng → thành công.

8. Cài Python dependencies
Tạo file requirements.txt:

txt
pandas>=2.0
numpy>=1.24
openpyxl>=3.1
psycopg[binary]>=3.1
sqlalchemy>=2.0
alembic>=1.13
python-dotenv>=1.0
scikit-learn>=1.3
xgboost>=2.0
joblib>=1.3
Cài:

cmd
pip install -r requirements.txt
9. Test kết nối từ Python
Tạo file src/db/__init__.py (rỗng).

Tạo file src/db/connection.py:

python
"""Kết nối PostgreSQL trong Docker container."""
import os
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load .env từ thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# Chuỗi kết nối
DB_URL = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Engine dùng chung cho toàn app
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session():
    """Context manager cho DB session.

    Sử dụng:
        with get_session() as session:
            session.execute(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Kiểm tra kết nối DB và liệt kê các bảng hiện có."""
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).fetchone()[0]
            print(f"✅ Kết nối OK: {version[:60]}")

            tables = [
                row[0]
                for row in conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' ORDER BY table_name"
                ))
            ]
            print(f"📋 Bảng hiện có: {tables}")
            return True
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False


if __name__ == "__main__":
    test_connection()
Chạy test:

cmd
python -m src.db.connection
Output mong đợi:

text
✅ Kết nối OK: PostgreSQL 18.x on x86_64-pc-linux-gnu...
📋 Bảng hiện có: ['analysis_logs', 'insights', 'model_runs', 'predictions', 'students']
10. Ingest dữ liệu từ Excel
Tạo file src/db/ingest.py:

python
"""Đọc Excel và insert vào bảng students."""
from pathlib import Path
import pandas as pd
from sqlalchemy import text

from src.db.connection import engine

BASE_DIR = Path(__file__).resolve().parents[2]
EXCEL_PATH = BASE_DIR / "data" / "du_lieu_sinh_vien_tong_hop.xlsx"

# Map tên cột tiếng Việt → tên cột DB
COLUMN_MAP = {
    'Mã SV': 'ma_sv',
    'Họ và Tên': 'ho_ten',
    'Giới Tính': 'gioi_tinh',
    'Quê Quán': 'que_quan',
    'Ngành Học': 'nganh_hoc',
    'Điểm THPT': 'diem_thpt',
    'Điểm GK (Hệ 10)': 'diem_gk',
    'LMS Giờ Truy Cập': 'lms_gio_truy_cap',
    'LMS Xem Video': 'lms_xem_video',
    'Nộp Bài Đúng Hạn (%)': 'nop_bai_dung_han',
    'Điểm Quiz (Hệ 10)': 'diem_quiz',
    'Điểm Bài Tập (Hệ 10)': 'diem_bai_tap',
    'Hoàn Cảnh KT': 'hoan_canh_kt',
    'Đi Làm Thêm': 'di_lam_them',
    'Mức Độ Stress (1-5)': 'muc_do_stress',
    'Động Lực Học (1-5)': 'dong_luc_hoc',
    'Chuyên Cần (%)': 'chuyen_can',
    'Mức Tương Tác': 'muc_tuong_tac',
    'Ghi Chú & Nhận Xét GV': 'ghi_chu_gv',
    'Nguy Cơ Học Vụ': 'nguy_co_hoc_vu',
}


def ingest_students(excel_path: Path = EXCEL_PATH) -> int:
    """Đọc Excel và insert vào bảng students.

    Args:
        excel_path: Đường dẫn file Excel.

    Returns:
        Số dòng đã insert.
    """
    df = pd.read_excel(excel_path, sheet_name='Du_Lieu_Sinh_Vien', skiprows=1)
    df = df.rename(columns=COLUMN_MAP)
    df = df[list(COLUMN_MAP.values())]

    # Xóa dữ liệu cũ để tránh trùng
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE students RESTART IDENTITY CASCADE"))

    df.to_sql('students', engine, if_exists='append', index=False)
    print(f"✅ Đã insert {len(df)} dòng vào bảng students")
    return len(df)


if __name__ == "__main__":
    ingest_students()
Chạy:

cmd
python -m src.db.ingest
Output: ✅ Đã insert 1000 dòng vào bảng students

11. Kiểm tra dữ liệu đã vào DB
cmd
docker exec -it student_db psql -U postgres -d student_analysis -c "SELECT COUNT(*) FROM students;"
Output:

text
 count
-------
  1000
Xem mẫu:

cmd
docker exec -it student_db psql -U postgres -d student_analysis -c "SELECT ma_sv, ho_ten, diem_gk FROM students LIMIT 5;"
12. Checklist hoàn thành setup
□ Docker Desktop đã cài
□ docker-compose.yml đã tạo
□ .env đã tạo
□ scripts/init_db.sql đã tạo
□ docker-compose up -d chạy thành công
□ Container student_db healthy
□ 5 bảng đã tạo trong DB
□ Python deps đã cài
□ python -m src.db.connection OK
□ python -m src.db.ingest insert 1000 dòng
□ SELECT COUNT(*) = 1000
