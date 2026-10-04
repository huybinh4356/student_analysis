# Current Features — Pre-Refactor (v2.0.0-pre-refactor)

> **Captured**: 2026-10-04  
> **Purpose**: Liệt kê tất cả tính năng hiện có, trạng thái hoạt động, và mức độ khớp với README.

---

## UI Screens / Widgets

| Widget | File | Trạng thái | Vấn đề |
|---|---|---|---|
| Upload | `upload_widget.py` | Hoạt động | Gọi `ingest_excel_to_db(force=True)` — destructive |
| EDA / Chart | `chart_widget.py` | Hoạt động | OK |
| Analysis | `analysis_widget.py` | Hoạt động | Chạy training trên main thread |
| Diagnosis | `diagnosis_widget.py` | Hoạt động | Load model riêng, dùng "confidence" heuristic |
| What-If | `whatif_widget.py` | Hoạt động | Gọi WhatIfEngine trực tiếp; fallback ẩn |
| Data Health | `data_health_widget.py` | Hoạt động | Absolute counts, không phải rates |
| Insight | `insight_widget.py` | Hoạt động | OK |
| Report | `report_widget.py` | Hoạt động | Hard-coded R²=94%, Accuracy=97% |

---

## ML Features

| Feature | Trạng thái |
|---|---|
| 6 Regression models so sánh | Có |
| 6 Classification models so sánh | Có |
| Cross-validation | Có, nhưng trên data đã transform — CV leakage |
| Model selection | Dùng Test R² cho regression — sai |
| Artifact save | Tên file sai (ridge_... nhưng có thể là XGBoost) |
| sklearn Pipeline | Không có — preprocessing và model tách rời |
| Model registry | Không có |
| Calibrated probability | Không có |

---

## Data Features

| Feature | Trạng thái |
|---|---|
| Schema validation | Cơ bản — chỉ check column name |
| Data type coercion | Có |
| Duplicate detection | Không có |
| Outlier detection | Không có |
| Staging table | Không có |
| Transactional ingestion | Partial — có rollback nhưng có drop_all trước |

---

## What-If Features

| Feature | Trạng thái |
|---|---|
| Score simulation | Có (với fallback ẩn) |
| Risk simulation | Có (threshold, không dùng classifier) |
| Sensitivity analysis | Có (delta không chuẩn hóa) |
| Reverse What-If | Có (greedy, không phải constrained optimization) |
| Causal disclaimer | Có trong cuối advice text |

---

## Export / Report

| Feature | README claim | Thực tế |
|---|---|---|
| HTML export | ✅ | ✅ — Xuất HTML từ QTextEdit |
| PDF export | ✅ | ❌ — Chỉ có HTML, không có PDF engine |
| Dynamic metrics | implied | ❌ — Hard-coded numbers |
| Actual vs Predicted label | implied | ❌ — Dùng diem_tong_ket (actual) làm "dự báo" |

---

## Startup / DevOps

| Feature | README claim | Thực tế |
|---|---|---|
| 1-click run | ✅ | ⚠️ — run_app.bat chỉ check .venv rồi `python main.py` |
| Auto create venv | ✅ | ❌ — Không tự tạo |
| Auto install deps | ✅ | ❌ — Không tự cài |
| Auto start Docker | ✅ | ❌ — Không tự start |
| Auto seed data | ✅ | ❌ — Không tự seed |
| Docker healthcheck | ✅ | ✅ — Có trong docker-compose.yml |
| Env template | ✅ | ⚠️ — Chứa password thật 123456 |
