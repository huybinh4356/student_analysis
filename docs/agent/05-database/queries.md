# CÁC QUERY THƯỜNG DÙNG

## 1. Query cơ bản

### Đếm sinh viên

```sql
SELECT COUNT(*) AS total FROM students;
Xem 10 dòng đầu
sql
SELECT * FROM students LIMIT 10;
Sinh viên theo ngành
sql
SELECT
    nganh_hoc,
    COUNT(*) AS n
FROM students
GROUP BY nganh_hoc
ORDER BY n DESC;
Điểm trung bình theo ngành
sql
SELECT
    nganh_hoc,
    ROUND(AVG(diem_gk)::numeric, 2) AS avg_gk,
    ROUND(AVG(diem_quiz)::numeric, 2) AS avg_quiz,
    ROUND(AVG(chuyen_can)::numeric, 2) AS avg_chuyen_can
FROM students
GROUP BY nganh_hoc;
2. Query theo điều kiện
Sinh viên có chuyên cần thấp
sql
SELECT ma_sv, ho_ten, chuyen_can, nop_bai_dung_han
FROM students
WHERE chuyen_can < 50
ORDER BY chuyen_can ASC;
Sinh viên vừa vắng vừa nộp bài thấp
sql
SELECT ma_sv, ho_ten, chuyen_can, nop_bai_dung_han
FROM students
WHERE chuyen_can < 50
  AND nop_bai_dung_han < 50
ORDER BY chuyen_can ASC;
Sinh viên stress cao nhưng động lực thấp
sql
SELECT ma_sv, ho_ten, muc_do_stress, dong_luc_hoc
FROM students
WHERE muc_do_stress >= 4
  AND dong_luc_hoc <= 2
ORDER BY muc_do_stress DESC;
Sinh viên nguy cơ cao (theo cột có sẵn)
sql
SELECT ma_sv, ho_ten, nganh_hoc, chuyen_can, nop_bai_dung_han
FROM students
WHERE nguy_co_hoc_vu = 'Cao'
ORDER BY chuyen_can ASC;
3. Query cho dashboard
Phân phối mức nguy cơ
sql
SELECT
    nguy_co_hoc_vu,
    COUNT(*) AS n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM students
GROUP BY nguy_co_hoc_vu
ORDER BY
    CASE nguy_co_hoc_vu
        WHEN 'Cao' THEN 1
        WHEN 'Trung bình' THEN 2
        WHEN 'Thấp' THEN 3
        WHEN 'Rất thấp' THEN 4
    END;
Thống kê theo giới tính và ngành
sql
SELECT
    gioi_tinh,
    nganh_hoc,
    COUNT(*) AS n,
    ROUND(AVG(diem_gk)::numeric, 2) AS avg_gk
FROM students
GROUP BY gioi_tinh, nganh_hoc
ORDER BY gioi_tinh, n DESC;
Xu hướng theo quê quán
sql
SELECT
    que_quan,
    COUNT(*) AS n,
    ROUND(AVG(diem_gk)::numeric, 2) AS avg_gk,
    ROUND(AVG(chuyen_can)::numeric, 2) AS avg_chuyen_can
FROM students
GROUP BY que_quan
HAVING COUNT(*) >= 5
ORDER BY avg_gk DESC;
4. Query cho Model
So sánh các lần train
sql
SELECT
    model_name,
    model_type,
    target,
    ROUND(r2_score::numeric, 3) AS r2,
    ROUND(rmse::numeric, 3) AS rmse,
    ROUND(mae::numeric, 3) AS mae,
    trained_at
FROM model_runs
WHERE model_type = 'regression'
ORDER BY trained_at DESC
LIMIT 10;
Model tốt nhất mỗi loại
sql
SELECT DISTINCT ON (model_type)
    model_type,
    model_name,
    target,
    ROUND(r2_score::numeric, 3) AS r2,
    trained_at
FROM model_runs
WHERE r2_score IS NOT NULL
ORDER BY model_type, r2_score DESC;
Lịch sử training 30 ngày gần nhất
sql
SELECT
    DATE(trained_at) AS day,
    COUNT(*) AS n_models,
    MAX(r2_score) AS best_r2
FROM model_runs
WHERE trained_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(trained_at)
ORDER BY day DESC;
5. Query cho Predictions
Top 10 sinh viên nguy cơ cao nhất
sql
SELECT
    s.ma_sv,
    s.ho_ten,
    s.nganh_hoc,
    s.chuyen_can,
    s.nop_bai_dung_han,
    ROUND(p.predicted_score::numeric, 2) AS predicted,
    p.predicted_risk
FROM students s
JOIN predictions p ON s.id = p.student_id
WHERE p.predicted_risk = 'Cao'
ORDER BY p.predicted_score ASC
LIMIT 10;
Sinh viên bất thường (dự đoán lệch)
sql
SELECT
    s.ma_sv,
    s.ho_ten,
    ROUND(p.predicted_score::numeric, 2) AS predicted,
    p.predicted_risk,
    p.confidence
FROM students s
JOIN predictions p ON s.id = p.student_id
WHERE p.is_anomaly = TRUE
ORDER BY p.confidence DESC;
Dự đoán mới nhất cho mỗi sinh viên
sql
SELECT DISTINCT ON (student_id)
    student_id,
    predicted_score,
    predicted_risk,
    created_at
FROM predictions
ORDER BY student_id, created_at DESC;
6. Query cho Insights
Sinh viên cần can thiệp ngay
sql
SELECT
    s.ma_sv,
    s.ho_ten,
    s.chuyen_can,
    s.nop_bai_dung_han,
    s.muc_do_stress,
    i.message,
    i.action_suggestion
FROM students s
JOIN insights i ON s.id = i.student_id
WHERE i.severity = 'high'
ORDER BY s.chuyen_can ASC;
Các loại insight phổ biến
sql
SELECT
    insight_type,
    category,
    severity,
    COUNT(*) AS n
FROM insights
GROUP BY insight_type, category, severity
ORDER BY n DESC;
Sinh viên có nhiều cảnh báo
sql
SELECT
    s.ma_sv,
    s.ho_ten,
    COUNT(*) AS n_warnings
FROM students s
JOIN insights i ON s.id = i.student_id
WHERE i.insight_type = 'warning'
GROUP BY s.ma_sv, s.ho_ten
HAVING COUNT(*) >= 3
ORDER BY n_warnings DESC;
7. Query phân tích nâng cao
Tương quan giữa chuyên cần và điểm GK
sql
SELECT
    CASE
        WHEN chuyen_can < 50 THEN '1. Dưới 50%'
        WHEN chuyen_can < 70 THEN '2. 50-70%'
        WHEN chuyen_can < 90 THEN '3. 70-90%'
        ELSE '4. Trên 90%'
    END AS nhom_chuyen_can,
    COUNT(*) AS n,
    ROUND(AVG(diem_gk)::numeric, 2) AS avg_gk,
    ROUND(AVG(diem_quiz)::numeric, 2) AS avg_quiz
FROM students
GROUP BY nhom_chuyen_can
ORDER BY nhom_chuyen_can;
Sinh viên giỏi nhưng chuyên cần thấp (bất thường)
sql
SELECT ma_sv, ho_ten, diem_gk, chuyen_can
FROM students
WHERE diem_gk >= 8.0
  AND chuyen_can < 60
ORDER BY diem_gk DESC;
Phân tích ảnh hưởng của đi làm thêm
sql
SELECT
    di_lam_them,
    COUNT(*) AS n,
    ROUND(AVG(diem_gk)::numeric, 2) AS avg_gk,
    ROUND(AVG(chuyen_can)::numeric, 2) AS avg_chuyen_can,
    ROUND(AVG(muc_do_stress)::numeric, 2) AS avg_stress
FROM students
GROUP BY di_lam_them
ORDER BY avg_gk DESC;
8. Query export
Export sinh viên nguy cơ ra CSV
sql
\COPY (
    SELECT
        s.ma_sv, s.ho_ten, s.nganh_hoc,
        p.predicted_score, p.predicted_risk
    FROM students s
    JOIN predictions p ON s.id = p.student_id
    WHERE p.predicted_risk IN ('Cao', 'Trung bình')
) TO '/tmp/high_risk_students.csv' WITH CSV HEADER;
Sau đó copy ra ngoài:

cmd
docker cp student_db:/tmp/high_risk_students.csv ./high_risk_students.csv
9. Query maintenance
Kích thước các bảng
sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
Số dòng trong mỗi bảng
sql
SELECT
    'students' AS table_name, COUNT(*) FROM students
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'insights', COUNT(*) FROM insights
UNION ALL
SELECT 'model_runs', COUNT(*) FROM model_runs
UNION ALL
SELECT 'analysis_logs', COUNT(*) FROM analysis_logs;
Query đang chạy
sql
SELECT
    pid,
    NOW() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
Vacuum database
sql
VACUUM ANALYZE;
10. Cheat sheet
sql
-- Đếm
SELECT COUNT(*) FROM students;

-- Xem mẫu
SELECT * FROM students LIMIT 5;

-- Group
SELECT nganh_hoc, COUNT(*) FROM students GROUP BY nganh_hoc;

-- Join
SELECT s.ma_sv, p.predicted_score
FROM students s
JOIN predictions p ON s.id = p.student_id;

-- Sắp xếp
SELECT * FROM students ORDER BY diem_gk DESC LIMIT 10;

-- Filter
SELECT * FROM students WHERE chuyen_can < 50;

-- Update
UPDATE students SET nguy_co_hoc_vu = 'Cao' WHERE chuyen_can < 30;

-- Delete
DELETE FROM predictions WHERE created_at < NOW() - INTERVAL '30 days';

-- Aggregate
SELECT AVG(diem_gk), MAX(diem_gk), MIN(diem_gk) FROM students;