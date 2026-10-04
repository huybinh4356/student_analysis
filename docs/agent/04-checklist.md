# 04 — CHECKLIST

## 4.1. Setup Database

- [ ] Docker đã cài đặt
- [ ] File `docker-compose.yml` có PostgreSQL 16
- [ ] Container đang chạy (`docker ps`)
- [ ] Kết nối được từ Python (`psycopg`)
- [ ] Bảng `students` đã tạo
- [ ] Bảng `predictions` đã tạo
- [ ] Bảng `insights` đã tạo
- [ ] Bảng `model_runs` đã tạo
- [ ] Đã ingest 1.000 dòng dữ liệu
- [ ] Test query cơ bản OK

## 4.2. Trước khi train model

- [ ] Đã bỏ cột ID
- [ ] Đã xử lý missing (nếu có)
- [ ] Đã encode biến phân loại
- [ ] Đã scale biến số
- [ ] Đã chia train/test
- [ ] Đã kiểm tra leakage
- [ ] Đã kiểm tra imbalance
- [ ] Đã có baseline

## 4.3. Trước khi báo cáo kết quả

- [ ] Đã cross-validate
- [ ] Đã so sánh với baseline
- [ ] Đã báo cáo nhiều metrics (R², RMSE, MAE)
- [ ] Đã kiểm tra overfitting
- [ ] Đã giải thích được model
- [ ] Đã nêu hạn chế
- [ ] Đã kiểm tra bias

## 4.4. Trước khi giao sản phẩm

- [ ] App chạy không crash
- [ ] Xử lý được file lỗi
- [ ] Có file mẫu để demo
- [ ] Đã test với người thật
- [ ] Có tài liệu hướng dẫn
- [ ] Đã đóng gói .exe
- [ ] Đã tạo installer
- [ ] Đã test cài đặt trên máy sạch

## 4.5. Trước khi bảo vệ

- [ ] Báo cáo đã in
- [ ] Slide đã chuẩn bị
- [ ] Demo đã test
- [ ] Q&A đã chuẩn bị
- [ ] Backup demo (video/photos)