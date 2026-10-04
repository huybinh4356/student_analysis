# 03 — WORKFLOW

## Quy trình làm việc của Agent

### 3.1. Khi nhận yêu cầu mới
Hiểu yêu cầu
└── Hỏi lại nếu chưa rõ

Kiểm tra context
└── Đã có dữ liệu chưa? Đã có model chưa? DB đã setup chưa?

Đề xuất cách làm
└── Trình bày 2-3 cách, đề xuất cách tốt nhất

Xin xác nhận
└── Không làm khi chưa được đồng ý

Thực thi
└── Code + giải thích

Kiểm tra kết quả
└── Chạy thử, báo cáo output

Đề xuất bước tiếp theo
└── "Bước tiếp theo nên làm gì?"

text

### 3.2. Khi gặp lỗi
Đọc lỗi cẩn thận

Xác định nguyên nhân

Đề xuất cách sửa

Giải thích tại sao lỗi

Sửa và chạy lại

Nếu không sửa được → hỏi user

text

### 3.3. Khi có nhiều lựa chọn
Format trả lời:
┌─────────────────────────────────────────┐
│ CÁCH 1: [Tên] │
│ • Ưu: ... │
│ • Nhược: ... │
│ • Phù hợp khi: ... │
├─────────────────────────────────────────┤
│ CÁCH 2: [Tên] │
│ • Ưu: ... │
│ • Nhược: ... │
│ • Phù hợp khi: ... │
├─────────────────────────────────────────┤
│ ĐỀ XUẤT: Cách X vì... │
└─────────────────────────────────────────┘

text

### 3.4. Luồng công việc theo giai đoạn

| Giai đoạn | Input | Output | Thời gian |
|-----------|-------|--------|-----------|
| Setup DB | Docker compose | PostgreSQL chạy | 0.5 ngày |
| Ingest | Excel | Data trong DB | 0.5 ngày |
| EDA | DB query | Báo cáo EDA | 1 ngày |
| Feature Eng | DataFrame | 50+ features | 2 ngày |
| Modeling | Features | Model + metrics | 2 ngày |
| Insight | Model + data | Insights | 1 ngày |
| UI | Core logic | PyQt6 app | 3 ngày |
| Packaging | App | .exe + installer | 1 ngày |
| Report | Tất cả | Báo cáo | 2 ngày |


## **Bắt buộc** phải tạo một file ghi dõ tuần tự các lỗi và cách xử lý 

### File `troubleshoot.md`

```markdown
# 03 — TROUBLESHOOT

## Lỗi thường gặp

### 1. Database connection

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Can't connect │ Kiểm tra docker-compose up │
| Wrong password │ Kiểm tra .env │
| DB not ready │ Thêm retry logic │

### 2. Missing data

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Missing % > 50% │ Xóa cột hoặc impute │
| Missing trong target │ Drop dòng │

### 3. Categorical encoding

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Too many categories │ Use target encoding │
| Non-string data │ Convert to string │

### 4. Model overfitting

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Train R² 0.99, Test R² 0.6 │ Regularization, reduce complexity │
| High variance │ Cross-validation │

### 5. Visualization errors

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Missing labels │ Set xlabel, ylabel │
| overlapping text │ Reduce fontsize, rotate │

### 6. PyQt6 errors

│ Lỗi │ Cách xử lý │
|-----|-----------|
| UI not updating │ Use QThread, signal/slot │
| App crashes │ Wrap in try/except, log errors │

### 7. Packaging errors

│ Lỗi │ Cách xử lý │
|-----|-----------|
| Missing dependencies │ Add --add-data │
| Icon not showing │ Check path, add --icon │
```