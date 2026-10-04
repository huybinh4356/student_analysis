# DATABASE SCHEMA

## Sơ đồ quan hệ

┌─────────────────┐
│ students │
│─────────────────│
│ id (PK) │
│ ma_sv (UNIQUE) │
│ ho_ten │
│ ... (18 biến) │
└────────┬────────┘
│
│ 1:N
├──────────────────┬──────────────────┐
▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐
│ predictions │ │ insights │ │ │
│─────────────────│ │─────────────────│ │ │
│ id (PK) │ │ id (PK) │ │ │
│ student_id (FK) │ │ student_id (FK) │ │ │
│ model_run_id(FK)│ │ insight_type │ │ │
│ predicted_score │ │ message │ │ │
│ predicted_risk │ │ severity │ │ │
└────────┬────────┘ └─────────────────┘ │ │
│ │ │
│ N:1 │ │
▼ │ │
┌─────────────────┐ │ │
│ model_runs │ │ │
│─────────────────│ │ │
│ id (PK) │ │ │
│ model_name │ │ │
│ r2_score │ │ │
│ rmse │ │ │
│ trained_at │ │ │
└─────────────────┘ │ │
│ │
┌─────────────────┐ │ │
│ analysis_logs │ (độc lập, không FK) │ │
│─────────────────│ │ │
│ id (PK) │ │ │
│ action │ │ │
│ details (JSONB) │ │ │
└─────────────────┘ │ │


## 1. Bảng `students`

Lưu dữ liệu gốc sinh viên (18 biến thực).

```sql
CREATE TABLE students (
    -- Khóa chính
    id SERIAL PRIMARY KEY,

    -- Định danh
    ma_sv VARCHAR(20) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,

    -- SIS (Hệ thống đào tạo)
    gioi_tinh VARCHAR(10),
    que_quan VARCHAR(50),
    nganh_hoc VARCHAR(50),
    diem_thpt FLOAT,
    diem_gk FLOAT,

    -- LMS (Học trực tuyến)
    lms_gio_truy_cap FLOAT,
    lms_xem_video INTEGER,
    nop_bai_dung_han FLOAT,
    diem_quiz FLOAT,
    diem_bai_tap FLOAT,

    -- Khảo sát (Tâm lý, hoàn cảnh)
    hoan_canh_kt VARCHAR(20),
    di_lam_them VARCHAR(20),
    muc_do_stress INTEGER,
    dong_luc_hoc INTEGER,

    -- Ghi chú GV
    chuyen_can FLOAT,
    muc_tuong_tac VARCHAR(20),
    ghi_chu_gv TEXT,
    nguy_co_hoc_vu VARCHAR(20),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_students_ma_sv ON students(ma_sv);
CREATE INDEX idx_students_nganh ON students(nganh_hoc);
CREATE INDEX idx_students_nguy_co ON students(nguy_co_hoc_vu);
Ghi chú:

id là khóa chính tự tăng.

ma_sv là mã sinh viên, UNIQUE (không trùng).

18 cột tiếp theo là dữ liệu thực.

created_at, updated_at tự động.

2. Bảng model_runs
Lưu lịch sử mỗi lần train model.

sql
CREATE TABLE model_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,       -- 'Ridge', 'XGBoost'...
    model_type VARCHAR(20) NOT NULL,       -- 'regression' | 'classification'
    target VARCHAR(50) NOT NULL,           -- 'DiemTongKet' | 'NguyCoHocVu'
    n_features INTEGER,
    n_samples INTEGER,

    -- Metrics Regression
    r2_score FLOAT,
    rmse FLOAT,
    mae FLOAT,

    -- Metrics Classification
    accuracy FLOAT,
    f1_score FLOAT,

    -- Metadata
    hyperparams JSONB,
    model_path VARCHAR(255),               -- đường dẫn file .pkl
    trained_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX idx_model_runs_type ON model_runs(model_type);
CREATE INDEX idx_model_runs_trained_at ON model_runs(trained_at DESC);
3. Bảng predictions
Lưu kết quả dự đoán cho từng sinh viên.

sql
CREATE TABLE predictions (
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

CREATE INDEX idx_predictions_student ON predictions(student_id);
CREATE INDEX idx_predictions_risk ON predictions(predicted_risk);
CREATE INDEX idx_predictions_run ON predictions(model_run_id);
Ghi chú:

ON DELETE CASCADE: xóa sinh viên → xóa luôn dự đoán.

prediction_interval_low/high: khoảng tin cậy 95%.

is_anomaly: đánh dấu nếu dự đoán lệch bất thường.

4. Bảng insights
Lưu insights sinh ra cho từng sinh viên.

sql
CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,

    insight_type VARCHAR(50) NOT NULL,     -- 'warning' | 'advice' | 'anomaly'
    category VARCHAR(50),                  -- 'missing' | 'outlier' | 'risk'
    message TEXT NOT NULL,
    severity VARCHAR(20),                  -- 'low' | 'medium' | 'high'
    action_suggestion TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_insights_student ON insights(student_id);
CREATE INDEX idx_insights_type ON insights(insight_type);
CREATE INDEX idx_insights_severity ON insights(severity);
5. Bảng analysis_logs
Lưu log mọi thao tác phân tích.

sql
CREATE TABLE analysis_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,          -- 'upload' | 'train' | 'predict'
    user_session VARCHAR(100),
    details JSONB,
    duration_ms INTEGER,
    status VARCHAR(20),                    -- 'success' | 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_logs_action ON analysis_logs(action);
CREATE INDEX idx_logs_created ON analysis_logs(created_at DESC);
6. Views tiện ích
View: Sinh viên nguy cơ cao
sql
CREATE VIEW v_high_risk_students AS
SELECT
    s.ma_sv,
    s.ho_ten,
    s.nganh_hoc,
    s.chuyen_can,
    s.nop_bai_dung_han,
    p.predicted_score,
    p.predicted_risk,
    p.confidence
FROM students s
JOIN predictions p ON s.id = p.student_id
WHERE p.predicted_risk IN ('Cao', 'Trung bình')
ORDER BY p.predicted_score ASC;
View: Thống kê theo ngành
sql
CREATE VIEW v_stats_by_major AS
SELECT
    s.nganh_hoc,
    COUNT(*) AS n_students,
    ROUND(AVG(s.diem_gk)::numeric, 2) AS avg_gk,
    ROUND(AVG(s.diem_quiz)::numeric, 2) AS avg_quiz,
    ROUND(AVG(s.chuyen_can)::numeric, 2) AS avg_chuyen_can,
    COUNT(CASE WHEN p.predicted_risk = 'Cao' THEN 1 END) AS n_high_risk
FROM students s
LEFT JOIN predictions p ON s.id = p.student_id
GROUP BY s.nganh_hoc;
7. Trigger cập nhật updated_at
sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_students_updated
BEFORE UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
Cách hoạt động: Mỗi khi UPDATE dòng trong students, cột updated_at tự động cập nhật thời gian hiện tại.

