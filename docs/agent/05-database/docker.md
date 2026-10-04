# DOCKER — Chi tiết vận hành

## 1. Kiến trúc Docker trong dự án
┌──────────────────────────────────────────────────┐
│ Windows Host │
│ ┌────────────────────────────────────────────┐ │
│ │ Docker Desktop │ │
│ │ ┌──────────────────────────────────────┐ │ │
│ │ │ Container: student_db │ │ │
│ │ │ Image: postgres:18-alpine │ │ │
│ │ │ Port: 5432 │ │ │
│ │ │ Volume: postgres_data │ │ │
│ │ │ ┌────────────────────────────────┐ │ │ │
│ │ │ │ PostgreSQL 18 │ │ │ │
│ │ │ │ Database: student_analysis │ │ │ │
│ │ │ │ 5 tables + indexes │ │ │ │
│ │ │ └────────────────────────────────┘ │ │ │
│ │ └──────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────┘ │
│ │
│ Python App (chạy trên host) │
│ │ │
│ └── Kết nối qua localhost:5432 │
└──────────────────────────────────────────────────┘

text

**Điểm quan trọng:**
- Container **cô lập** với Windows — không ảnh hưởng hệ thống.
- **Volume** lưu dữ liệu bền vững — xóa container không mất data.
- **Port mapping** cho phép Python trên host kết nối vào container.
- **Init script** chạy 1 lần khi container khởi động lần đầu.

## 2. Vòng đời container
Lần đầu:
docker-compose up -d
├── Tải image postgres:18-alpine (nếu chưa có)
├── Tạo volume postgres_data
├── Tạo container student_db
├── Chạy init_db.sql (tạo 5 bảng)
└── Container healthy

Các lần sau:
docker-compose up -d
├── Image đã có (không tải lại)
├── Volume đã có (không tạo mới)
├── Container cũ khởi động lại
└── KHÔNG chạy lại init_db.sql

text

## 3. Các lệnh Docker cơ bản

### Khởi động

```cmd
:: Chạy nền
docker-compose up -d

:: Chạy và xem log trực tiếp
docker-compose up
Dừng
cmd
:: Dừng container (giữ data)
docker-compose stop

:: Dừng và xóa container (giữ data trong volume)
docker-compose down

:: Dừng và xóa cả volume (⚠️ MẤT DATA)
docker-compose down -v
Khởi động lại
cmd
docker-compose restart
Xem trạng thái
cmd
:: Danh sách container đang chạy
docker ps

:: Danh sách tất cả container (kể cả đã dừng)
docker ps -a

:: Danh sách volumes
docker volume ls

:: Chi tiết container
docker inspect student_db
Xem log
cmd
:: Log realtime
docker-compose logs -f postgres

:: 100 dòng cuối
docker-compose logs --tail=100 postgres
Vào trong container
cmd
:: Mở shell trong container
docker exec -it student_db sh

:: Mở psql
docker exec -it student_db psql -U postgres -d student_analysis
4. Volume — Lưu trữ dữ liệu
Volume là gì?
Volume là ổ đĩa ảo được Docker quản lý, dùng để lưu dữ liệu bền vững. Khi container bị xóa, volume vẫn còn → data không mất.

Liệt kê volumes
cmd
docker volume ls
Output:

text
DRIVER    VOLUME NAME
local     student-analysis-app_postgres_data
Xem dung lượng
cmd
docker system df -v
Xóa volume ( mất data)
cmd
:: Xóa volume cụ thể
docker volume rm student-analysis-app_postgres_data

:: Xóa tất cả volume không dùng
docker volume prune
Backup volume ra file
cmd
docker run --rm ^
  -v student-analysis-app_postgres_data:/data ^
  -v %cd%:/backup ^
  alpine tar czf /backup/postgres_data_backup.tar.gz -C /data .
5. Backup & Restore Database
Backup bằng pg_dump
cmd
:: Backup toàn bộ database
docker exec student_db pg_dump -U postgres student_analysis > backup.sql

:: Backup chỉ schema (không data)
docker exec student_db pg_dump -U postgres --schema-only student_analysis > schema.sql

:: Backup chỉ data (không schema)
docker exec student_db pg_dump -U postgres --data-only student_analysis > data.sql

:: Backup 1 bảng
docker exec student_db pg_dump -U postgres -t students student_analysis > students.sql
Restore
cmd
:: Tạo DB mới
docker exec student_db psql -U postgres -c "CREATE DATABASE student_analysis_backup;"

:: Restore
docker exec -i student_db psql -U postgres -d student_analysis_backup < backup.sql
Backup tự động hàng ngày (Windows Task Scheduler)
Tạo file scripts/backup.bat:

batch
@echo off
set BACKUP_DIR=D:\backups\student_analysis
set DATE=%date:~10,4%-%date:~4,2%-%date:~7,2%

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

docker exec student_db pg_dump -U postgres student_analysis > %BACKUP_DIR%\backup_%DATE%.sql

echo Backup completed: %BACKUP_DIR%\backup_%DATE%.sql
Đăng ký Task Scheduler chạy hàng ngày.

6. Import/Export dữ liệu
Import CSV
cmd
:: Copy file CSV vào container
docker cp data.csv student_db:/tmp/data.csv

:: Import
docker exec -it student_db psql -U postgres -d student_analysis -c "\COPY students FROM '/tmp/data.csv' CSV HEADER;"
Export CSV
cmd
docker exec student_db psql -U postgres -d student_analysis -c "\COPY (SELECT * FROM students) TO '/tmp/students.csv' CSV HEADER;"
docker cp student_db:/tmp/students.csv ./students.csv
Import SQL
cmd
docker exec -i student_db psql -U postgres -d student_analysis < init_db.sql
7. Cấu hình nâng cao
Đổi port (khi 5432 bị chiếm)
Sửa docker-compose.yml:

yaml
ports:
  - "5433:5432"    # Host:5433 → Container:5432
Cập nhật .env:

env
DB_PORT=5433
Khởi động lại:

cmd
docker-compose down
docker-compose up -d
Giới hạn tài nguyên
Thêm vào docker-compose.yml:

yaml
services:
  postgres:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M
Cấu hình PostgreSQL
Thêm vào docker-compose.yml:

yaml
services:
  postgres:
    # ...
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
      -c work_mem=16MB
8. Xử lý sự cố
Container không khởi động
cmd
:: Xem log chi tiết
docker-compose logs postgres

:: Xem sự kiện
docker events --filter container=student_db
Container bị treo
cmd
:: Restart
docker-compose restart

:: Nếu vẫn treo, xóa và tạo lại (giữ volume)
docker-compose down
docker-compose up -d
Đầy ổ đĩa
cmd
:: Xem dung lượng Docker
docker system df

:: Dọn dẹp (an toàn)
docker system prune

:: Dọn dẹp mạnh (xóa cả volume không dùng)
docker system prune -a --volumes
Quên password
cmd
:: Vào container không cần password
docker exec -it student_db psql -U postgres

:: Trong psql:
ALTER USER postgres WITH PASSWORD '12345678';
\q
Reset hoàn toàn
cmd
:: Xóa tất cả
docker-compose down -v

:: Xóa image (nếu muốn tải lại)
docker rmi postgres:18-alpine

:: Khởi động lại từ đầu
docker-compose up -d

:: Chờ healthy rồi ingest lại
python -m src.db.ingest
9. Best practices
Nguyên tắc	Chi tiết
Không dùng latest tag	Dùng postgres:18-alpine — version cố định
Không commit .env	Thêm vào .gitignore
Backup định kỳ	pg_dump hàng ngày
Volume tách biệt	Không dùng bind mount cho data
Healthcheck bắt buộc	Đảm bảo DB sẵn sàng
Đặt tên rõ ràng	Container student_db không phải db1
Không chạy với root	PostgreSQL image mặc định đã non-root
Log rotate	Giới hạn log để không đầy ổ
10. Cheat sheet
cmd
:: ============ KHỞI ĐỘNG ============
docker-compose up -d                    :: Chạy nền
docker-compose logs -f postgres         :: Xem log

:: ============ TRẠNG THÁI ============
docker ps                               :: Container đang chạy
docker inspect student_db               :: Chi tiết
docker stats student_db                 :: Tài nguyên

:: ============ DỪNG ============
docker-compose stop                     :: Dừng (giữ container)
docker-compose down                     :: Xóa container (giữ volume)
docker-compose down -v                  :: Xóa hết (mất data)

:: ============ TRUY CẬP ============
docker exec -it student_db sh           :: Shell
docker exec -it student_db psql -U postgres -d student_analysis

:: ============ BACKUP ============
docker exec student_db pg_dump -U postgres student_analysis > backup.sql

:: ============ DỌN DẸP ============
docker system prune                     :: Xóa image/container không dùng
docker volume prune                     :: Xóa volume không dùng