# 00 — CONTEXT

## 1. Tổng quan dự án

### 1.1. Mục tiêu
Xây dựng **ứng dụng desktop** phân tích và dự đoán kết quả học tập sinh viên, cho phép giảng viên:
- Upload file Excel/CSV.
- Tự động khám phá dữ liệu (EDA).
- Chạy mô hình hồi quy/phân loại.
- Nhận lời khuyên hành động cho từng sinh viên.

### 1.2. Đầu ra
- Desktop app (PyQt6) đóng gói `.exe` + installer.
- Dashboard trực quan.
- Báo cáo PDF tự động.
- Danh sách sinh viên nguy cơ + gợi ý can thiệp.

### 1.3. Đối tượng dùng
- Giảng viên phụ trách môn.
- Cố vấn học tập.
- Phòng đào tạo.

### 1.4. Thời gian & chi phí
| Hạng mục | Giá trị |
|----------|---------|
| Thời gian | 6-7 tuần |
| Chi phí | 0đ |
| Nhân lực | 1 sinh viên |

---

## 2. Dữ liệu

### 2.1. File nguồn
- **Tên:** `du_lieu_sinh_vien_tong_hop.xlsx`
- **Sheet 1:** `Du_Lieu_Sinh_Vien` — dữ liệu chính
- **Sheet 2:** `Tu_Dien_Bien_&_Thong_Ke` — data dictionary

### 2.2. Quy mô
| Chỉ tiêu | Giá trị |
|----------|---------|
| Số mẫu | 1.000 sinh viên |
| Số biến gốc | 20 cột |
| Số biến thực | 18 (bỏ ID) |
| Missing | 0% |
| Duplicate | 0 |

### 2.3. Nguồn dữ liệu
| Nguồn | Số biến | Ví dụ |
|-------|---------|-------|
| SIS (Hệ thống đào tạo) | 7 | Điểm THPT, Điểm GK, Ngành |
| LMS (Học trực tuyến) | 5 | Giờ truy cập, Nộp bài, Quiz |
| Khảo sát | 4 | Stress, Động lực, Hoàn cảnh |
| Ghi chú GV | 4 | Chuyên cần, Nhận xét, Nguy cơ |

### 2.4. Biến mục tiêu
| Target | Kiểu | Dùng cho |
|--------|------|----------|
| Nguy Cơ Học Vụ | Ordinal 4 mức | Classification |
| DiemTongKet (tạo mới) | Continuous | Regression |

### 2.5. Công thức tạo DiemTongKet

DiemTongKet = 0.4 × Điểm GK + 0.3 × Điểm Quiz + 0.3 × Điểm Bài Tập

---

## 3. Tech Stack

### 3.1. Ngôn ngữ & môi trường
| Thành phần | Công cụ | Version |
|------------|---------|---------|
| Ngôn ngữ | Python | 3.11+ |
| Quản lý package | pip + venv | — |
| IDE | VS Code / PyCharm | — |

### 3.2. Xử lý dữ liệu
| Thư viện | Vai trò |
|----------|---------|
| pandas | Đọc, xử lý bảng |
| numpy | Tính toán số |
| openpyxl | Đọc Excel |

### 3.3. Machine Learning
| Thư viện | Vai trò |
|----------|---------|
| scikit-learn | Model cơ bản |
| xgboost | Model mạnh |
| joblib | Lưu model |

### 3.4. Giao diện
| Thư viện | Vai trò |
|----------|---------|
| PyQt6 | Desktop UI |
| pyqtgraph | Biểu đồ tương tác |
| matplotlib | Biểu đồ báo cáo |

### 3.5. Database (PostgreSQL)
| Thành phần | Công cụ | Version |
|------------|---------|---------|
| Database | PostgreSQL | 16+ |
| Driver | psycopg | 3.x |
| ORM | SQLAlchemy | 2.x |
| Migration | Alembic | 1.x |
| Container | Docker | 24+ |

### 3.6. Đóng gói
| Công cụ | Vai trò |
|---------|---------|
| PyInstaller | Đóng gói .exe |
| Inno Setup | Tạo installer |

---

## 4. Ràng buộc

### 4.1. Kỹ thuật
- Không dùng API trả tiền.
- Không cần GPU.
- Chạy offline được (sau khi setup).
- Hỗ trợ Windows 10/11.

### 4.2. Dữ liệu
- Ẩn danh khi phân tích.
- Bảo mật thông tin sinh viên.
- Chỉ giảng viên dạy lớp xem được.

### 4.3. Hiệu năng
- Load 1.000 dòng < 2 giây.
- Train model < 30 giây.
- Dự đoán < 1 giây.

---

## 5. Kiến trúc tổng thể
┌─────────────────────────────────────────────────────────┐
│ DESKTOP APP (PyQt6) │
│ ┌───────────────────────────────────────────────────┐ │
│ │ Main Window: Sidebar + Tabs + Toolbar │ │
│ └───────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ CORE LAYER (Python) │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Data │ │ Model │ │ Insight │ │
│ │ Layer │ │ Layer │ │ Layer │ │
│ └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────┬──────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ POSTGRESQL DATABASE (Docker) │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Tables: students, predictions, insights, logs │ │
│ └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

---

## 6. Lộ trình

| Tuần | Việc | Output |
|------|------|--------|
| 1 | Setup PostgreSQL + xử lý dữ liệu | DB + dataset sạch |
| 2 | EDA + Feature Engineering | 50+ features |
| 3 | Train 5 model + đánh giá | Bảng so sánh |
| 4 | Insight Engine + rule-based | Insights |
| 5 | PyQt6 UI + kết nối DB | App chạy được |
| 6 | Threading + polish + PDF | App hoàn chỉnh |
| 7 | Đóng gói .exe + installer + báo cáo | Sản phẩm cuối |