# REFACTOR_PLAN.md — Student Analysis v3

> **Baseline tag**: `v2.0.0-pre-refactor`  
> **Working branch**: `refactor/v3`  
> **Goal**: Đưa repo tới trạng thái mỗi con số trong UI/report đều bắt nguồn từ pipeline thực tế — không có metric giả, fallback ngầm, hay logic dự đoán thứ hai.

---

## Architecture Target

```
Student Analysis Platform v3
│
├── Data Governance
│   ├── Schema Validation       → src/data/schema.py
│   ├── Data Quality            → src/data/quality.py
│   ├── Transactional Ingestion → src/data/ingestion.py
│   └── Versioning              → dataset_version in metadata
│
├── ML Platform
│   ├── Feature Pipeline        → sklearn.Pipeline (preprocessor + model)
│   ├── CV (clean)              → cross_validate(pipeline, X_raw, y)
│   ├── Model Selection         → CV metric only
│   ├── Evaluation              → EvaluationResult (persisted)
│   └── Registry                → models/registry.json
│
├── Prediction Platform
│   ├── Score Prediction        → PredictionService.predict_score()
│   ├── Risk Prediction         → PredictionService.predict_risk()
│   ├── Calibrated Probability  → PredictionService.predict_probability()
│   └── Scenario Simulation     → WhatIfService.simulate()
│
├── Application
│   ├── Dashboard
│   ├── Diagnosis               → consumes PredictionService only
│   ├── What-If                 → consumes WhatIfService only
│   ├── EDA
│   └── Reports                 → dynamic metrics from registry.json
│
└── Engineering
    ├── Tests (unit/integration/contract)
    ├── CI/CD (.github/workflows/)
    ├── Docker (env-based credentials)
    ├── Migrations (Alembic)
    └── Documentation
```

---

## Dependency Graph (thứ tự bắt buộc)

```
[0] Freeze baseline
     ↓
[1] Data contract + target audit     ← GATING: không làm gì trước khi có
     ↓
[2] Leakage audit
     ↓
[3] Schema validator + ingestion
     ↓
[4] ML pipeline rewrite              ← sklearn.Pipeline, clean CV
     ↓
[5] Model evaluation + selection     ← CV only, no test-set selection
     ↓
[6] Model registry                   ← registry.json, correct naming
     ↓
[7] PredictionService                ← single entry point
     ↓
[8] WhatIfService rewrite            ← no fallback, constrained solver
     ↓
[9] Diagnosis + Report               ← consume service, dynamic metrics
     ↓
[10] Tests                           ← unit + integration + contract
     ↓
[11] CI/CD                           ← ruff + pytest + docker check
     ↓
[12] Docs + UX polish
     ↓
[RELEASE]
```

---

## 5 Gates — Phải pass trước khi qua phase tiếp theo

### GATE 1 — Data ✅/❌
- [ ] Data dictionary documented (`docs/data_dictionary.md`)
- [ ] Target generation audited (diem_tong_ket, nguy_co_hoc_vu)
- [ ] Leakage audit completed (composite_exam_score)
- [ ] Prediction time defined
- [ ] Schema validation tests pass

### GATE 2 — ML ✅/❌
- [ ] No preprocessing leakage (sklearn.Pipeline)
- [ ] CV is clean (raw data, not transformed)
- [ ] Test set untouched until final evaluation
- [ ] Best model selected from CV only
- [ ] Metrics persisted to metrics.json

### GATE 3 — Prediction ✅/❌
- [ ] One PredictionService (single entry point)
- [ ] Diagnosis uses PredictionService
- [ ] What-If uses WhatIfService → PredictionService
- [ ] Report uses dynamic metrics from registry
- [ ] No fallback fake model anywhere

### GATE 4 — Product ✅/❌
- [ ] Upload safe (no drop_all, transactional)
- [ ] Training non-blocking (QThread)
- [ ] Report metrics dynamic
- [ ] Errors visible (no silent except: pass)

### GATE 5 — Release ✅/❌
- [ ] Clean clone works
- [ ] Docker works (env-based credentials)
- [ ] All tests pass
- [ ] CI passes
- [ ] README matches reality

---

## Backlog (GitHub Issues)

### 🔴 P0 — Must Fix (Blockers)

| ID | Issue | Phase | Branch |
|---|---|---|---|
| ML-01 | Audit target generation (diem_tong_ket, nguy_co_hoc_vu) | 1 | `fix/data-contract` |
| ML-02 | Audit feature leakage (composite_exam_score vs target) | 1 | `fix/data-contract` |
| ML-03 | Define prediction time (đầu kỳ / giữa kỳ / week 6) | 1 | `fix/data-contract` |
| ML-04 | Rebuild preprocessing into sklearn Pipeline | 4 | `refactor/ml-pipeline` |
| ML-05 | Fix CV leakage (CV on raw data, not transformed) | 4 | `refactor/ml-pipeline` |
| ML-06 | Remove test-set model selection | 5 | `refactor/ml-pipeline` |
| ML-07 | Fix regression model selection (use CV R², not Test R²) | 5 | `refactor/ml-pipeline` |
| ML-08 | Fix artifact naming (registry.json + correct filenames) | 6 | `feat/model-registry` |
| ML-09 | Persist evaluation metrics to metrics.json dynamically | 6 | `feat/model-registry` |
| ML-10 | Remove WhatIf silent fallback (except Exception: pass) | 8 | `refactor/whatif` |
| ML-11 | Unify risk prediction through classifier, not threshold | 7 | `refactor/prediction-service` |
| DATA-01 | Write data_dictionary.md | 1 | `fix/data-contract` |
| DATA-02 | Implement schema validator (missing cols, dtype, range) | 2 | `fix/ingestion` |
| DATA-03 | Validate target columns (not null, valid range/enum) | 2 | `fix/ingestion` |
| DB-01 | Make ingestion transactional (no drop_all) | 3 | `fix/ingestion` |
| DB-02 | Remove destructive re-import logic | 3 | `fix/ingestion` |
| PRED-01 | Create PredictionService (single entry point for all UI) | 7 | `refactor/prediction-service` |
| WHATIF-01 | Remove WhatIf heuristic model fallback | 8 | `refactor/whatif` |
| REPORT-01 | Remove hard-coded R²=94% Accuracy=97% from report | 9 | `fix/report` |
| REPORT-02 | Fix actual/predicted label (diem_tong_ket ≠ predicted) | 9 | `fix/report` |
| TEST-01 | Write unit tests for data layer (schema, validator) | 10 | `feat/testing-ci` |
| TEST-02 | Write unit tests for ML layer (pipeline, leakage check) | 10 | `feat/testing-ci` |

### 🟠 P1 — High

| ID | Issue | Phase | Branch |
|---|---|---|---|
| DATA-04 | Data quality engine (missing_rate, invalid_rate, outlier_rate) | 2 | `fix/ingestion` |
| DB-03 | Repository/session cleanup (consistent DI) | 3 | `fix/ingestion` |
| DB-04 | Add Alembic migrations (no more drop_all/create_all) | 29 | `feat/testing-ci` |
| PRED-02 | Model bundle (pipeline + metadata + features in one pkl) | 7 | `refactor/prediction-service` |
| PRED-03 | Prediction reliability score (data completeness metric) | 12 | `refactor/prediction-service` |
| WHATIF-02 | Standardized sensitivity (Δprediction / Δfeature per unit) | 15 | `refactor/whatif` |
| WHATIF-03 | Constrained target solver (scipy.optimize, not greedy) | 16 | `refactor/whatif` |
| WHATIF-04 | Add predictive-not-causal wording in UI | 17 | `refactor/whatif` |
| UI-01 | Move training to QThread (non-blocking) | 22 | `refactor/prediction-service` |
| UI-02 | Dynamic diagnosis (consume PredictionService) | 37 | `refactor/prediction-service` |
| REPORT-03 | Real HTML→PDF pipeline (Jinja2 + PDF engine) | 21 | `fix/report` |
| TEST-03 | Integration tests (ingestion pipeline, training pipeline) | 10 | `feat/testing-ci` |
| TEST-04 | Model contract tests (feature schema, output range) | 10 | `feat/testing-ci` |
| DEV-01 | Migrate to pyproject.toml | 30 | `feat/testing-ci` |
| DEV-02 | Add CI/CD (.github/workflows/tests.yml + lint.yml) | 33 | `feat/testing-ci` |
| DEV-03 | Add ruff + black linting | 34 | `feat/testing-ci` |
| DOC-01 | Rewrite README (matches reality, no fake KPIs) | 36 | `docs/v3` |
| DOC-02 | Document data methodology | 36 | `docs/v3` |
| DOC-03 | Document ML methodology + limitations | 36 | `docs/v3` |

### 🟡 P2 — Medium

| ID | Issue | Phase | Branch |
|---|---|---|---|
| DEV-04 | Security audit (bandit, pip-audit) | 33 | `feat/testing-ci` |
| DOC-04 | Architecture documentation | 36 | `docs/v3` |
| DEV-CRED-01 | Fix hardcoded Docker credentials | 31 | `fix/ingestion` |
| DEV-BAT-01 | Rebuild run.bat (full setup flow) | 32 | `fix/ingestion` |

---

## Branch Strategy

```
main
└── refactor/v3                    ← Base branch cho toàn bộ refactor
    ├── fix/data-contract          ← Phase 0-1: Data dictionary, target audit
    ├── fix/ingestion              ← Phase 2-3: Validator, transactional ingestion, Docker creds
    ├── refactor/ml-pipeline       ← Phase 4-5: sklearn Pipeline, clean CV, model selection
    ├── feat/model-registry        ← Phase 6-7: registry.json, artifact naming, metrics.json
    ├── refactor/prediction-service← Phase 7: PredictionService, QThread training
    ├── refactor/whatif            ← Phase 8-17: Remove fallback, constrained solver
    ├── fix/report                 ← Phase 9, 19-21: Dynamic metrics, PDF export
    ├── feat/testing-ci            ← Phase 26-34: Tests, CI, pyproject.toml
    └── docs/v3                    ← Phase 36: README rewrite
```

**Rule**: Mỗi branch = 1 mục tiêu. Merge vào `refactor/v3`, không merge trực tiếp vào `main`.

---

## Commit Convention

```
chore: freeze pre-refactor baseline (tag v2.0.0-pre-refactor)
feat(data): introduce dataset contract and data dictionary
fix(data): implement schema validator with error classification
fix(db): make ingestion transactional (remove drop_all)
fix(db): add staging table flow for safe upload
refactor(ml): move preprocessing into sklearn Pipeline
fix(ml): prevent cross-validation leakage (CV on raw data)
fix(ml): select models using CV metric only, not test R²
feat(ml): add model registry (registry.json, correct naming)
feat(ml): persist evaluation metrics dynamically
refactor(prediction): centralize PredictionService
fix(prediction): rename confidence → data_completeness score
refactor(whatif): remove heuristic model fallback (raise PredictionError)
feat(whatif): implement constrained target solver (scipy.optimize)
fix(whatif): standardize sensitivity (Δprediction/Δfeature per unit)
fix(whatif): add predictive-not-causal wording in UI
fix(report): remove hard-coded R² and Accuracy metrics
fix(report): read metrics from registry.json at runtime
feat(report): implement Jinja2 → HTML → PDF pipeline
fix(ui): move training to QThread (non-blocking)
feat(tests): add unit tests for data layer
feat(tests): add unit tests for ML pipeline (leakage check)
feat(tests): add integration tests (ingestion + training)
feat(tests): add model contract tests
feat(ci): add GitHub Actions (tests + lint + docker check)
fix(docker): use env variable substitution for credentials
feat(dev): migrate to pyproject.toml
docs: rewrite README (remove fake KPIs, add limitations)
docs: document ML methodology and leakage prevention
```

---

## File Structure Target (v3)

```
src/
├── core/                        # Existing (keep, refactor)
│   ├── exceptions.py            # NEW: Custom exception hierarchy
│   ├── schema_detector.py       # Keep (rename to data_contract.py later)
│   ├── feature_engineer.py      # Modify: remove/flag leaking features
│   ├── preprocessor.py          # Deprecate: move logic into sklearn Pipeline
│   └── model_trainer.py         # Rewrite: use Pipeline + clean CV
│
├── data/                        # NEW module
│   ├── __init__.py
│   ├── schema.py                # Schema constants and column specs
│   ├── validator.py             # DataValidator: MISSING/INVALID/OUTLIER/DUPLICATE
│   ├── cleaner.py               # DataCleaner: type coercion, normalization
│   ├── quality.py               # DataQuality: rates, overall_status
│   └── ingestion.py             # Transactional ingestion (replaces db/ingest.py)
│
├── ml/                          # NEW module (or refactor core/)
│   ├── __init__.py
│   ├── pipeline.py              # sklearn.Pipeline builder
│   ├── trainer.py               # ModelTrainer: CV on pipeline, clean selection
│   ├── evaluator.py             # EvaluationResult: all metrics
│   └── registry.py              # ModelRegistry: load/save/version
│
├── services/                    # NEW module
│   ├── __init__.py
│   ├── prediction_service.py    # PredictionService: single entry for all UI
│   └── whatif_service.py        # WhatIfService: simulate/compare/sensitivity/solve
│
├── db/                          # Existing (refactor)
│   ├── connection.py
│   ├── models.py                # Add: student_staging table
│   └── repositories.py          # Fix: consistent session DI
│
└── ui/                          # Existing (refactor after backend done)
    ├── workers/                 # NEW: QThread workers
    │   └── training_worker.py
    └── ...

models/
├── registry.json                # NEW: model metadata + artifact paths
├── regression/
│   └── best_model.pkl           # sklearn Pipeline (preprocessor + model)
├── classification/
│   └── best_model.pkl           # sklearn Pipeline (preprocessor + model)
└── metrics/
    └── evaluation_results.json  # Full metrics from last training run

tests/
├── unit/
│   ├── test_schema.py
│   ├── test_validator.py
│   ├── test_features.py
│   ├── test_pipeline.py
│   ├── test_metrics.py
│   └── test_whatif.py
├── integration/
│   ├── test_ingestion.py
│   ├── test_training.py
│   ├── test_prediction.py
│   └── test_report.py
└── regression/
    └── test_model_contract.py

.github/
└── workflows/
    ├── tests.yml
    ├── lint.yml
    └── build.yml

docs/
├── baseline/                    # ← Frozen, do not modify
│   ├── current_architecture.md
│   ├── current_metrics.json
│   ├── current_features.md
│   └── known_issues.md
├── data_dictionary.md           # Phase 1
├── ml_methodology.md            # Phase 36
├── architecture.md              # Phase 36
└── agent/                       # Existing
```

---

## What NOT to do

```
❌ Thêm feature UI mới trước khi backend/ML ổn
❌ Giữ R²=94% / Accuracy=97% bằng cách tối ưu metric
❌ Viết thêm heuristic để "chữa cháy" model lỗi
❌ Merge trực tiếp vào main
❌ Tạo commit "fix project" gộp nhiều thứ
❌ Dùng drop_all/create_all cho production data
❌ Hard-code credentials trong bất kỳ file nào vào git
❌ Gọi model.predict() trực tiếp từ UI widget
```

---

## Critical Principles

1. **Data trước, code sau**: Không train model trước khi biết target được tạo ra như thế nào.
2. **Một PredictionService**: Tất cả UI đều phải gọi qua service. Không widget nào được load model riêng.
3. **Không có fallback ẩn**: Model lỗi → PredictionError → UI hiển thị "Prediction unavailable".
4. **Test set untouched**: Chỉ dùng test set một lần duy nhất để đo final performance.
5. **Metric từ runtime**: Mọi con số trong report/UI phải đọc từ `registry.json` hoặc `evaluation_results.json`.
6. **Wording đúng**: "Simulation scenario" không phải "causal intervention". Nói rõ đây là dự báo.

---

## Estimated Effort

| Phase | Effort | Priority |
|---|---|---|
| Phase 0: Freeze baseline | Done ✅ | P0 |
| Phase 1: Data contract | 1-2 ngày | P0 |
| Phase 2-3: Validation + Ingestion | 2-3 ngày | P0 |
| Phase 4-6: ML Pipeline + Registry | 3-4 ngày | P0 |
| Phase 7: PredictionService | 1-2 ngày | P0 |
| Phase 8-17: WhatIf rewrite | 2-3 ngày | P0-P1 |
| Phase 18-21: Report + Export | 2 ngày | P0-P1 |
| Phase 22-25: Threading + Logging | 2 ngày | P1 |
| Phase 26-29: Tests | 3-4 ngày | P0-P1 |
| Phase 30-35: CI/CD + Docker + Deps | 2 ngày | P1 |
| Phase 36-38: Docs + Release validation | 2 ngày | P1 |
| **Total** | **~22-30 ngày** | |

---

*Tài liệu này là kế hoạch sống — cập nhật khi hoàn thành mỗi phase.*
