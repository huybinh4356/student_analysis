-- Chạy tự động khi container PostgreSQL khởi động lần đầu
-- Nếu sửa file này, phải chạy: docker-compose down -v && docker-compose up -d

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
CREATE INDEX IF NOT EXISTS idx_predictions_student ON predictions(student_id);
CREATE INDEX IF NOT EXISTS idx_predictions_risk ON predictions(predicted_risk);
CREATE INDEX IF NOT EXISTS idx_insights_student ON insights(student_id);
CREATE INDEX IF NOT EXISTS idx_logs_created ON analysis_logs(created_at DESC);