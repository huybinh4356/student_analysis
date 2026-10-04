# 06 — DATABASE (PostgreSQL 18 + Docker)

## Tổng quan

Dự án sử dụng **PostgreSQL 18** chạy trong **Docker container** để lưu trữ:
- Dữ liệu sinh viên gốc.
- Kết quả dự đoán từ model.
- Insights sinh ra.
- Lịch sử training model.
- Log thao tác phân tích.

## Cấu trúc tài liệu

| File | Nội dung |
|------|----------|
| [schema.md](./schema.md) | Thiết kế bảng, quan hệ, indexes |
| [setup.md](./setup.md) | Cài đặt PostgreSQL + Docker từ A-Z |
| [docker.md](./docker.md) | Chi tiết Docker: lệnh, volume, backup |
| [queries.md](./queries.md) | Các query SQL thường dùng |
| [migrations.md](./migrations.md) | Quản lý phiên bản schema với Alembic |

## Thông tin kết nối

| Trường | Giá trị |
|--------|---------|
| Image | `postgres:18-alpine` |
| Container | `student_db` |
| Host | `localhost` |
| Port | `5432` |
| Database | `student_analysis` |
| User | `postgres` |
| Password | `123456` |

## Lý do chọn PostgreSQL + Docker

| Tiêu chí | SQLite | PostgreSQL + Docker |
|----------|--------|---------------------|
| Setup | 5 phút | 15 phút |
| Cô lập hệ thống | ❌ Ảnh hưởng Windows | ✅ Hoàn toàn cô lập |
| Xóa/reset | Khó | `docker-compose down -v` |
| Concurrent | ❌ | ✅ |
| JSON support | Hạn chế | Tốt (JSONB) |
| Window functions | Hạn chế | Đầy đủ |
| Production-ready | ❌ | ✅ |
| Portable | Tệ | Tốt (mọi máy có Docker) |

## Quy trình tổng quan

Cài Docker Desktop

Tạo docker-compose.yml + .env

docker-compose up -d

Chờ container healthy

Python kết nối qua psycopg

Ingest dữ liệu từ Excel

Sẵn sàng phân tích

text

## Backup & Restore nhanh

```bash
# Backup
docker exec student_db pg_dump -U postgres student_analysis > backup.sql

# Restore
docker exec -i student_db psql -U postgres -d student_analysis < backup.sql
Reset toàn bộ (⚠️ xóa dữ liệu)
bash
docker-compose down -v
docker-compose up -d
# Chờ healthy rồi ingest lại
python -m src.db.ingest