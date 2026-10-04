# Current Architecture Snapshot — Pre-Refactor (v2.0.0-pre-refactor)

> **Captured**: 2026-10-04  
> **Branch**: main (tagged `v2.0.0-pre-refactor`)  
> **Purpose**: Đây là snapshot hiện trạng hệ thống trước khi bắt đầu refactor/v3. Không sửa file này trong quá trình refactor.

---

## 1. Cấu trúc thư mục hiện tại

```
student_analysis/
├── data/                         # Excel mẫu (du_lieu_sinh_vien_tong_hop.xlsx)
├── docker/
├── docker-compose.yml            # ⚠️ Hard-coded credentials (postgres/123456)
├── docs/
├── main.py                       # PyQt6 entry point
├── models/
│   ├── feature_names.pkl         # List[str] feature names
│   ├── preprocessor.pkl          # DataPreprocessor instance (fitted ColumnTransformer)
│   ├── ridge_regression_model.pkl# ⚠️ Tên sai — có thể là XGBoost hoặc Ridge tùy lần train
│   └── risk_classifier_model.pkl # Best classification model (509 KB, likely RandomForest)
├── requirements.txt              # Flat freeze-style deps
├── run_app.bat                   # ⚠️ Chỉ check .venv rồi chạy main.py — không làm gì khác
├── run.bat
├── scripts/
├── src/
│   ├── core/
│   │   ├── data_loader.py
│   │   ├── dataset_health.py
│   │   ├── feature_engineer.py   # Tạo composite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT
│   │   ├── insight_engine.py
│   │   ├── missing_detector.py
│   │   ├── model_trainer.py      # ⚠️ CV trên X đã transform; model selection dùng Test R²
│   │   ├── preprocessor.py       # DataPreprocessor (split + encode + scale riêng)
│   │   ├── scenario_manager.py
│   │   ├── schema_detector.py    # SchemaDetector (constants)
│   │   └── whatif_engine.py      # ⚠️ Silent fallback formula; predict_risk() dùng threshold
│   ├── db/
│   │   ├── connection.py
│   │   ├── ingest.py             # ⚠️ drop_all() khi force=True; không staging
│   │   ├── models.py             # SQLAlchemy ORM
│   │   └── repositories.py
│   └── ui/
│       ├── analysis_widget.py
│       ├── chart_widget.py
│       ├── charts/
│       ├── data_health_widget.py
│       ├── data_management_widget.py
│       ├── diagnosis_widget.py
│       ├── insight_widget.py
│       ├── main_window.py
│       ├── report_widget.py      # ⚠️ Hard-coded R²=94% Accuracy=97% trong HTML
│       ├── styles.qss
│       ├── upload_widget.py
│       └── whatif_widget.py      # 25 KB — UI gọi WhatIfEngine trực tiếp
└── tests/
    ├── test_db.py
    ├── test_insight.py
    ├── test_model.py
    ├── test_preprocessor.py
    └── test_v2_features.py       # 9 tests, không có bad-case tests
```

---

## 2. Data Flow hiện tại

```
Excel file
    │
    ▼
ingest.py
  ├── clean_and_impute_data()     # Strip + coerce numeric
  ├── Base.metadata.drop_all()   # ⚠️ DESTRUCTIVE — xóa toàn bộ DB
  ├── Base.metadata.create_all()
  └── db.bulk_save_objects()
    │
    ▼
PostgreSQL: students table
    │
    ▼
DataLoader.load_from_db()
    │
    ▼
FeatureEngineer.create_features()
  ├── composite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT   # ⚠️ Leakage risk
  ├── academic_engagement_index
  ├── stress_motivation_ratio
  ├── lms_gio_per_video
  └── low_engagement_flag
    │
    ▼
DataPreprocessor.prepare_features()
  ├── X (features)
  ├── y_reg = diem_tong_ket       # Continuous target
  └── y_cls = nguy_co_hoc_vu     # Categorical target (mapped 1-4)
    │
    ▼
DataPreprocessor.split_data()
  └── X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test
    │
    ▼
DataPreprocessor.encode_and_scale()  # Fit on X_train ✓
  └── X_train_transformed, X_test_transformed (np.ndarray)
    │
    ▼
ModelTrainer.train_evaluate_regression(X_train_transformed, ...)
  ├── model.fit(X_train_transformed, y_reg_train)
  ├── cross_val_score(model, X_train_transformed, ...)    # ⚠️ CV on already-transformed data
  ├── Model selection: if XGBoost - Ridge < 0.03 → Ridge  # ⚠️ Dùng Test R² để chọn
  └── joblib.dump(best, "ridge_regression_model.pkl")     # ⚠️ Tên sai
    │
    ▼
ModelTrainer.train_evaluate_classification(X_train_transformed, ...)
  ├── model.fit(X_train_transformed, y_cls_train)
  ├── cross_val_score(model, X_train_transformed, ...)    # ⚠️ CV on already-transformed data
  └── joblib.dump(best_F1_macro, "risk_classifier_model.pkl")
    │
    ▼
WhatIfEngine._load_artifacts()
  ├── Load ridge_regression_model.pkl   # ⚠️ May actually be XGBoost
  ├── Load risk_classifier_model.pkl
  ├── Load preprocessor.pkl
  └── Load feature_names.pkl
    │
    ▼
WhatIfEngine.predict_score()
  ├── Try: preprocessor.transform() → model.predict()
  └── Except Exception: pass             # ⚠️ Silent failure
      └── Formula: 0.4*GK + 0.3*Quiz + 0.3*BT + attendance_bonus  # ⚠️ Fake score
    │
    ▼
WhatIfEngine.predict_risk(score)         # ⚠️ Hand-written threshold, bypasses classifier
  └── score >= 8.0 → "Rất thấp"
      score >= 6.5 → "Thấp"
      score >= 5.0 → "Trung bình"
      score >= 3.5 → "Cao"
      else        → "Rất cao"
```

---

## 3. Các module chính và vấn đề đã xác nhận

| Module | File | Vấn đề |
|---|---|---|
| Ingestion | `src/db/ingest.py:124` | `Base.metadata.drop_all()` — destructive |
| ML Train | `src/core/model_trainer.py:66` | CV chạy trên `X_train_transformed` (đã transform) |
| ML Select | `src/core/model_trainer.py:87` | Chọn model dựa vào Test R², không phải CV |
| Artifact | `src/core/model_trainer.py:90` | Lưu XGBoost/Ridge đều dưới tên `ridge_regression_model.pkl` |
| WhatIf | `src/core/whatif_engine.py:99-111` | `except Exception: pass` + fallback formula |
| Risk | `src/core/whatif_engine.py:113-133` | `predict_risk()` dùng threshold, không dùng classifier |
| Report | `src/ui/report_widget.py:114-115` | Hard-coded `R²=94%`, `Accuracy=97%` |
| Docker | `docker-compose.yml:8` | Hard-coded `123456` |
| Env | `.env.example:4` | `DB_PASSWORD=123456` |
| run_app.bat | `run_app.bat` | Không làm gì ngoài check .venv và chạy main.py |
| Feature | `src/core/feature_engineer.py:43-44` | `composite_exam_score` = linear combo của GK+Quiz+BT — cần audit leakage vs target |
| Sensitivity | `src/core/whatif_engine.py:155-162` | Delta không chuẩn hóa: Attendance +10 vs Grade +1 |
| Reverse WhatIf | `src/core/whatif_engine.py:177-244` | Greedy heuristic, không phải constrained optimization |

---

## 4. Infrastructure

| Component | Detail |
|---|---|
| Database | PostgreSQL 18-alpine via Docker |
| ORM | SQLAlchemy 2.x |
| UI | PyQt6 |
| ML | scikit-learn + XGBoost |
| Container port | 5433 → 5432 |
| Credentials | Hard-coded `postgres/123456` |
| Migrations | None — dùng `drop_all/create_all` |

---

## 5. Test suite hiện tại

| File | Tests | Loại |
|---|---|---|
| `test_db.py` | ~2 | DB connection |
| `test_insight.py` | ~2 | Insight logic |
| `test_model.py` | ~2 | Model predict |
| `test_preprocessor.py` | ~2 | Preprocessing |
| `test_v2_features.py` | ~5 | Feature engineering |

- Tổng: ~13 tests, chủ yếu happy-path
- **Không có** bad-case tests
- **Không có** model contract tests
- **Không có** integration tests (ingestion pipeline, training pipeline)
