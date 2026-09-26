# 🎓 Hệ thống Phân tích & Dự đoán Kết quả Học tập Sinh viên

Ứng dụng Desktop (PyQt6) tích hợp Machine Learning và Cơ sở dữ liệu PostgreSQL 18 trong Docker, hỗ trợ Giảng viên:
- Upload file Excel/CSV chứa dữ liệu sinh viên.
- Khám phá dữ liệu (EDA) và tùy chọn biểu đồ tương tác (Cột, Tròn, Tần số, Phân tán).
- Huấn luyện và dự báo điểm số/rủi ro học vụ với 5 mô hình ML ($R^2 = 94.0\%$, Accuracy = $97.0\%$).
- Nhận lời khuyên can thiệp sư phạm tự động và chạy **Mô phỏng What-If** theo thời gian thực.
- Xuất báo cáo tổng hợp tự chọn dưới dạng PDF/HTML.

---

## 🚀 Hướng dẫn Khởi chạy 1-Click (Dành cho Người mới Clone Project)

### Bước 1: Clone Repository
```bash
git clone https://github.com/huybinh4356/student_analysis.git
cd student_analysis
```

### Bước 2: Bật Ứng dụng
Mở thư mục dự án và **nhấp đúp chuột vào file `run_app.bat`**.

Script `run_app.bat` sẽ tự động:
1. Kiểm tra Python 3.11+.
2. Tự động khởi tạo môi trường ảo `.venv` và cài đặt đủ tất cả thư viện từ `requirements.txt`.
3. Tự động bật Docker container PostgreSQL (`student_db` trên cổng `5433`).
4. Tự động nạp 1,000 bản ghi sinh viên mẫu vào PostgreSQL Database.
5. Tự động mở giao diện ứng dụng Desktop PyQt6.

---

## 🛠️ Yêu cầu Môi trường
- **Hệ điều hành:** Windows 10/11.
- **Python:** 3.11 trở lên (Đã tích hợp trong PATH).
- **Docker Desktop:** Đã cài đặt và khởi chạy.

---

## 📂 Cấu trúc Thư mục Dự án

```
student_analysis/
├── data/                       # Dữ liệu sinh viên Excel mẫu
├── docker/                     # Cấu hình khởi tạo PostgreSQL SQL
├── docs/                       # Tài liệu hướng dẫn & bộ quy tắc (Rules & Skills)
├── models/                     # Các file mô hình Machine Learning (.pkl)
├── scripts/                    # Script chạy EDA và huấn luyện mô hình ML
├── src/                        # Mã nguồn ứng dụng
│   ├── core/                   # Logic xử lý dữ liệu, ML pipeline & Insight Engine
│   ├── db/                     # SQLAlchemy ORM models, connection & repositories
│   └── ui/                     # Giao diện ứng dụng PyQt6 & custom QSS theme
├── tests/                      # Bộ kiểm thử tự động Pytest (9/9 passed)
├── .env.example                # Cấu hình mẫu môi trường
├── docker-compose.yml          # Container PostgreSQL 18 Alpine
├── main.py                     # Entry point chạy ứng dụng Desktop
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── run_app.bat                 # Script tự động cài đặt & mở ứng dụng 1-Click
└── setup_env.bat               # Script cài đặt môi trường
```
