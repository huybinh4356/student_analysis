# 🎓 Hệ thống Phân tích & Dự báo Nguy cơ Học vụ Sinh viên (v3.0.0)

Ứng dụng Desktop chuyên nghiệp (PyQt6) tích hợp Machine Learning, Data Governance và Cơ sở dữ liệu PostgreSQL trong Docker, phục vụ công tác cố vấn học tập và cảnh báo sớm học vụ tại trường đại học.

---

## 🏛️ Kiến Trúc Hệ Thống (Platform Architecture)

```
Student Analysis Platform v3
│
├── 🛡️ Data Governance Layer
│   ├── Schema Validation & Contract (src/data/schema.py, validator.py)
│   ├── Data Quality & Health Reporting (src/data/quality.py)
│   └── Transactional Safe Ingestion (src/data/ingestion.py)
│
├── 🧠 ML Platform Layer
│   ├── Preprocessing Pipeline (ColumnTransformer: OneHot, Imputer, Scaler)
│   ├── Zero-Leakage Cross-Validation (5-Fold CV on raw training features)
│   ├── CV-Driven Model Selection (Parsimony principle, zero test-set snooping)
│   └── Model Registry & Bundle Persistence (models/registry.json, bundles)
│
├── 🔮 Prediction Platform Layer
│   ├── Centralized Prediction Service (src/services/prediction_service.py)
│   ├── Calibrated Multi-Class Risk Probabilities
│   ├── Data Completeness & Prediction Reliability Metric
│   └── What-If Simulation & Constrained Target Solver (scipy.optimize)
│
├── 🖥️ Application Layer (PyQt6)
│   ├── Tab 1: Quản lý File Excel & CSDL PostgreSQL / Data Health
│   ├── Tab 2: Tùy chọn Biểu đồ Thống kê EDA
│   ├── Tab 3: Trung tâm Huấn luyện & Đánh giá ML (Non-blocking QThread)
│   ├── Tab 4: Chẩn đoán Sinh viên & Kiểm tra Dữ liệu Thiếu
│   ├── Tab 5: Mô phỏng Kịch bản What-If & Phân tích Độ nhạy Chuẩn hóa
│   └── Tab 6: Xuất Báo cáo Động (Dynamic Performance Reporting)
│
└── ⚙️ Engineering & DevOps
    ├── Pytest Suite (Unit, Regression & Pipeline Contracts)
    ├── pyproject.toml & GitHub Actions CI Pipeline
    ├── One-Click Launcher (run.bat / run_app.bat)
    └── Docker Compose (Biến môi trường bảo mật)
```

---

## 🔬 Phương Pháp Luận Machine Learning (ML Methodology)

### 1. Chính sách Ngăn ngừa Rò rỉ Dữ liệu (Leakage Prevention)
- **Loại bỏ `composite_exam_score`**: Audit thực nghiệm cho thấy biến tổng hợp `0.4*GK + 0.3*Quiz + 0.3*BT` có tương quan $R^2 = 0.938$ với điểm tổng kết — đây là biến gây rò rỉ dữ liệu (feature leakage) làm thổi phồng chỉ số giả tạo. Trong phiên bản 3.0, biến này **bị cấm hoàn toàn**.
- **Fit Pipeline trong từng Fold CV**: Toàn bộ quá trình impute, scale, và one-hot encode được đóng gói trong `sklearn.pipeline.Pipeline`, chỉ fit trên fold huấn luyện để đảm bảo không rò rỉ phân phối sang fold kiểm thử.

### 2. Tiêu chuẩn Lựa chọn Mô hình (CV-Based Model Selection)
- Mô hình chiến thắng được chọn **hoàn toàn dựa trên điểm Cross-Validation 5-Fold trên tập Train**, tuyệt đối không dùng tập Test để chọn mô hình.
- **Quy tắc Tinh giản (Parsimony Rule)**: Nếu mô hình tuyến tính đơn giản (Lasso/Ridge) có điểm CV $R^2$ chênh lệch không quá $0.02$ so với mô hình phi tuyến tính phức tạp (Random Forest / XGBoost), hệ thống sẽ ưu tiên chọn mô hình tuyến tính để tối ưu khả năng diễn giải.
- Tập Test chỉ được đánh giá **1 lần duy nhất** sau khi đã chọn xong mô hình tốt nhất.

### 3. Kết quả Huấn luyện Thực tế (Từ Model Registry)

| Nhiệm vụ | Mô hình Được chọn | Tiêu chí Lựa chọn | Điểm 5-Fold CV | Điểm Kiểm định Test Độc lập |
|---|---|---|---|---|
| **Hồi quy Điểm số (0–10)** | **Lasso Regression** | CV $R^2$ cao nhất (0.9366) | $R^2 = 0.9366 \pm 0.0058$<br>MAE = 0.2758 | Test $R^2 = 0.9431$<br>Test MAE = $\pm 0.26$<br>Test RMSE = 0.33 |
| **Phân loại Nguy cơ Học vụ** | **XGBoost Classifier** | CV Macro F1 cao nhất (0.9573) | Macro F1 = $0.9573 \pm 0.0260$<br>CV Acc = 96.38% | Test Acc = 98.00%<br>Test Macro F1 = 0.9724<br>Recall Nhóm Nguy cơ Cao = 90.91% |

---

## ⚖️ Tuyên Bố Về Bản Chất Dự Báo & Đạo Đức AI (Ethical Disclaimers)

> **⚠️ Lưu ý quan trọng**:
> - Tính năng **Mô phỏng What-If** là công cụ **mô phỏng kịch bản dự báo thống kê (predictive simulation)**, không đại diện cho can thiệp nhân quả thực tế (causal estimation).
> - Hệ thống tuân thủ nghiêm ngặt chuẩn mực đạo đức sư phạm: sử dụng thuật ngữ mang tính hỗ trợ ("Có nguy cơ học vụ", "Cần cố vấn"), tuyệt đối không gán nhãn tiêu cực ("Sẽ thi trượt").
> - Quyết định can thiệp học vụ chính thức luôn thuộc về Giảng viên và Hội đồng Sư phạm.

---

## 🚀 Hướng Dẫn Khởi Chạy 1-Click (Quickstart)

### Cách 1: Chạy tự động bằng file script
Nhấp đúp chuột vào file **`run.bat`** (hoặc `run_app.bat`). Script sẽ tự động:
1. Kiểm tra môi trường Python.
2. Tự động tạo `.venv` và cài đặt dependencies nếu chưa có.
3. Thiết lập file cấu hình `.env` bảo mật.
4. Bật Docker PostgreSQL (hoặc tự động chuyển sang chế độ Excel nếu Docker chưa bật).
5. Khởi động giao diện PyQt6.

### Cách 2: Khởi chạy thủ công bằng dòng lệnh
```bash
# 1. Kích hoạt môi trường ảo
.venv\Scripts\activate

# 2. Khởi động Docker PostgreSQL (Tùy chọn)
docker compose up -d

# 3. Chạy kiểm thử tự động
pytest tests/unit/ -v

# 4. Mở ứng dụng Desktop
python main.py
```

---

## 🧪 Kiểm Thử Hệ Thống (Testing)

Chạy bộ kiểm thử tự động toàn diện:
```bash
# Chạy toàn bộ unit tests (Schema, Validator, ML Pipeline, Services, What-If Optimizer)
pytest tests/unit/ -v
```

---

## 📄 Bản Quyền
Dự án phục vụ mục đích nghiên cứu và triển khai ứng dụng quản lý đào tạo đại học.
