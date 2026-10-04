# Known Issues — Pre-Refactor (v2.0.0-pre-refactor)

> **Captured**: 2026-10-04  
> **Source**: Code audit của branch main, tag `v2.0.0-pre-refactor`  
> **Priority**: P0 = Blocker, P1 = High, P2 = Medium

---

## 🔴 P0 — Critical / Blocker

### ML-CV-01: Cross-validation leakage
- **File**: `src/core/model_trainer.py:66`, `model_trainer.py:142`
- **Vấn đề**: `cross_val_score(model, X_train_transformed, ...)` — CV chạy trên data đã transform. Transformer đã fit trên toàn X_train trước khi CV, gây data leakage qua preprocessor.
- **Impact**: CV metric không phản ánh generalization thực tế.
- **Fix**: Bọc preprocessor + model vào `sklearn.Pipeline`, chạy `cross_validate(pipeline, X_raw, y)`.

### ML-SEL-01: Model selection dùng Test set
- **File**: `src/core/model_trainer.py:85-87`
- **Vấn đề**: `best_name = "Ridge Regression" if (xgb_r2 - ridge_r2) < 0.03 else "XGBoost"` — so sánh trực tiếp Test R². Test set đã bị "dùng" để chọn model → test contamination.
- **Fix**: Chọn model dựa trên CV metric. Test set chỉ dùng một lần cuối cùng để đo final performance.

### ML-ART-01: Artifact naming sai
- **File**: `src/core/model_trainer.py:90`
- **Vấn đề**: Dù chọn XGBoost hay Ridge, đều lưu dưới tên `ridge_regression_model.pkl`. WhatIfEngine load đúng file này.
- **Impact**: Không biết model thực tế đang chạy là gì.
- **Fix**: Tạo model registry, lưu tên model vào metadata.

### DB-DEST-01: Destructive ingestion
- **File**: `src/db/ingest.py:124`
- **Vấn đề**: `Base.metadata.drop_all(bind=engine)` xóa toàn bộ database trước khi insert. Mọi data cũ bị mất khi upload file mới.
- **Fix**: Staging table → validation → transaction commit.

### WHATIF-FALL-01: Silent fallback
- **File**: `src/core/whatif_engine.py:99-111`
- **Vấn đề**:
  ```python
  except Exception:
      pass  # Fall through to formula
  # Formula: 0.4*GK + 0.3*Quiz + 0.3*BT + attendance_bonus
  ```
  Model lỗi nhưng UI nhận được điểm số bình thường từ formula.
- **Impact**: Không thể phát hiện model bị hỏng.
- **Fix**: Xóa fallback, raise `PredictionError`, UI hiển thị "Prediction unavailable".

### REPORT-HARD-01: Hard-coded metrics trong Report
- **File**: `src/ui/report_widget.py:114-115`
- **Vấn đề**:
  ```python
  html += "R² = 94.0%, MAE = ±0.27 điểm"
  html += "Accuracy = 97.0%, F1-Macro = 0.966"
  ```
  Metric không lấy từ evaluation thực tế, luôn hiển thị con số cố định bất kể model đang chạy.
- **Fix**: Đọc từ `metrics.json` hoặc `ModelRegistry`.

---

## 🟠 P1 — High

### ML-RISK-01: predict_risk() bypass classifier
- **File**: `src/core/whatif_engine.py:113-133`
- **Vấn đề**: `predict_risk(score)` ánh xạ score → risk bằng threshold cố định. Classifier thực tế bị bỏ qua hoàn toàn trong What-If.
- **Fix**: Dùng classifier.predict() + predict_proba() qua PredictionService.

### ML-SENS-01: Sensitivity không chuẩn hóa
- **File**: `src/core/whatif_engine.py:155-162`
- **Vấn đề**: So sánh impact của `+10% attendance` với `+1 grade` trực tiếp. Các delta khác nhau không thể so sánh được.
- **Fix**: Tính `Δprediction / Δfeature` (effect per unit) và chuẩn hóa.

### ML-REV-01: reverse_whatif() là greedy heuristic
- **File**: `src/core/whatif_engine.py:177-244`
- **Vấn đề**: Gọi là "optimal" nhưng thực ra là greedy: xếp theo sensitivity rồi tăng lần lượt. Không đảm bảo minimal intervention.
- **Fix**: Dùng `scipy.optimize.minimize` với constrained optimization.

### DB-SESS-01: Session management không nhất quán
- **File**: `src/db/ingest.py:51-53`, `repositories.py`
- **Vấn đề**: `check_data_exists()` tạo session riêng không qua dependency injection. Mix giữa `engine` và `SessionLocal`.
- **Fix**: Repository pattern thống nhất, session qua context manager.

### UI-THREAD-01: Training chạy trên main thread
- **File**: `src/ui/analysis_widget.py`
- **Vấn đề**: Training ML block UI thread, gây freeze.
- **Fix**: QThread/QRunnable với progress signal.

### REPORT-ACTUAL-01: Dùng actual score làm "predicted"
- **File**: `src/ui/report_widget.py:109`
- **Vấn đề**: `df['diem_tong_ket'].mean()` được label là "Điểm Tổng kết Dự báo TB" — đây là actual, không phải predicted.
- **Fix**: Tách ReportData, lấy predicted từ PredictionService.

---

## 🟡 P2 — Medium

### DEV-CRED-01: Hardcoded credentials trong Docker
- **File**: `docker-compose.yml:7-9`, `.env.example:3-4`
- **Vấn đề**: `POSTGRES_USER: postgres`, `POSTGRES_PASSWORD: "123456"` hard-coded. `.env.example` public trong repo chứa password thật.
- **Fix**: Dùng env variable substitution `${DB_PASSWORD}`, đổi CHANGE_ME trong example.

### DEV-BAT-01: run_app.bat không khớp README
- **File**: `run_app.bat`
- **Vấn đề**: README nói tự tạo .venv, cài deps, start Docker, seed data. Thực tế: chỉ check .venv rồi `python main.py`.
- **Fix**: Rebuild run.bat theo flow đầy đủ.

### TEST-BAD-01: Không có bad-case tests
- **Dir**: `tests/`
- **Vấn đề**: Tất cả tests là happy-path. Không test: empty Excel, missing column, invalid score, corrupt model, DB disconnected, prediction unavailable.
- **Fix**: Thêm tests/unit/ và tests/integration/ với bad-case scenarios.

### DEV-DEP-01: requirements.txt kiểu freeze
- **File**: `requirements.txt`
- **Vấn đề**: Chứa transitive dependencies, không phải direct dependencies. Khó maintain.
- **Fix**: Chuyển sang `pyproject.toml` với direct deps, lock riêng.

### ML-LEAK-01: Feature leakage cần audit (PENDING)
- **File**: `src/core/feature_engineer.py:43-44`
- **Vấn đề**: `composite_exam_score = 0.4*diem_gk + 0.3*diem_quiz + 0.3*diem_bai_tap`. Cần kiểm tra: `diem_tong_ket` (target) có được tính từ các thành phần này không? Nếu có → leakage nghiêm trọng.
- **Status**: Cần audit — xem cách dataset được sinh ra.

---

## Summary Count

| Priority | Count |
|---|---|
| P0 Blocker | 5 |
| P1 High | 6 |
| P2 Medium | 5 |
| **Total** | **16** |
