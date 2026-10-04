# Student Analysis — Refactor Master Plan

> **Repository:** `huybinh4356/student_analysis`  
> **Audit snapshot:** 2026-10-04  
> **Scope:** Data, Database, Machine Learning, Model Registry, Prediction, What-If, Diagnosis, EDA, Report, PyQt6 UI/UX, Error Handling, Testing, CI/CD, Security, Reproducibility, Documentation.

---

## 0. Mục tiêu của kế hoạch

Kế hoạch này dùng làm **master backlog** để đưa `student_analysis` từ một ứng dụng demo có nhiều tính năng thành một **end-to-end ML software project** có pipeline dữ liệu rõ ràng, đánh giá mô hình đúng, UI nhất quán và có thể tái lập.

Không mục tiêu nào dưới đây được phép đánh đổi tính đúng đắn của ML để giữ một KPI đẹp.

### Nguyên tắc cốt lõi

1. **Linear Regression là baseline bắt buộc**, nhưng không phải giới hạn của hệ thống. Có thể benchmark Ridge, Lasso, ElasticNet, Polynomial + Regularization, Random Forest, Gradient Boosting/XGBoost rồi chọn mô hình tốt nhất bằng quy trình đánh giá chuẩn.
2. **Không leakage.** Feature, target, prediction time và dữ liệu train/test phải có định nghĩa rõ.
3. **CV quyết định model selection; test chỉ dùng đánh giá cuối.**
4. **Một runtime path duy nhất.** UI không được vừa dùng service mới vừa bypass sang engine/loader legacy.
5. **Không có fake fallback.** Model lỗi phải báo lỗi, không âm thầm dùng công thức khác.
6. **Metrics, model metadata, dataset version và report phải đồng bộ.** Không hard-code kết quả ML.
7. **What-If là predictive simulation, không phải causal intervention.**
8. **UI phải phản ánh trạng thái thật của hệ thống:** data valid/invalid, model ready/stale/missing, training, error, report ready.
9. **Mọi destructive action phải có guard/confirmation/transaction.**
10. **Tài liệu không được đi trước implementation.** README chỉ mô tả những gì code thực sự làm và đã được kiểm thử.

---

# 1. Trạng thái hiện tại cần ghi nhận

## 1.1. Những phần v3 đã làm đúng hướng

- Đã có Data Governance layer mới (`src/data/schema.py`, `validator.py`, `quality.py`, `ingestion.py`).
- Đã loại bỏ/cấm `composite_exam_score`, một feature tổng hợp có nguy cơ leakage.
- Preprocessing đã được đưa vào `sklearn.pipeline.Pipeline` để dùng trong CV.
- Model selection hiện được thực hiện dựa trên CV thay vì chọn trực tiếp bằng test set.
- Đã có `ModelRegistry` và bundle persistence.
- Đã có `PredictionService` tập trung inference.
- Đã có `WhatIfService` với simulation, sensitivity và constrained target solver.
- Training UI đã chuyển sang worker `QThread` để tránh khóa giao diện.
- Đã có typed exceptions và logging ở một số lớp.
- README đã bổ sung methodology, leakage prevention, predictive-vs-causal disclaimer và quickstart.

## 1.2. Technical debt quan trọng còn tồn tại

### P0 / Blocking

- UI `WhatIfWidget` vẫn import và sử dụng `src.core.whatif_engine.WhatIfEngine` thay vì `WhatIfService`.
- UI `DiagnosisWidget` vẫn dùng `WhatIfEngine` và `MissingDetector` thay vì chỉ dùng `PredictionService`.
- UI `UploadWidget` vẫn dùng `src.db.ingest.ingest_excel_to_db` thay vì pipeline mới `src.data.ingestion`.
- Legacy `src/db/ingest.py` vẫn có `Base.metadata.drop_all(...)` và có thể phá dữ liệu khi ingest.
- Legacy `src/core/whatif_engine.py` vẫn tồn tại cùng silent fallback/fake formula path.
- `scripts/train_models.py` cần kiểm tra/migrate hoàn toàn theo contract mới của `ModelTrainer`.
- Regression registry hiện chọn `Lasso Regression`; điều này không sai nếu giáo viên cho phép nâng cấp mô hình, nhưng cần benchmark có phương pháp luận rõ ràng và không được coi Lasso/XGBoost là “đương nhiên tốt” chỉ vì registry chọn nó.
- Report phải tuyệt đối không còn fallback metric cứng khi registry thiếu dữ liệu.

### P1 / Important

- `dataset_version` trong registry vẫn đang là `default`, chưa phải version thực.
- `model_version` còn mang tính cố định, chưa có artifact revision/history.
- Reliability hiện dựa trên danh sách “critical features” cố định; nên đồng bộ với feature contract/registry.
- Prediction đang clip output về `[0, 10]`; internal/raw prediction nên tách khỏi display prediction để không làm sai sensitivity analysis.
- Ordinal encoding phải có justification; nếu khoảng cách giữa các category không đều, ưu tiên OneHot hoặc encoding phù hợp.
- Docker credentials còn hard-code.
- README/launcher/implementation phải được đối chiếu lại sau mỗi thay đổi.
- Cần kiểm tra CI thực sự tồn tại và chạy được, không chỉ ghi trong README.
- PDF export cần được xác minh/hoàn thiện nếu UI/README quảng bá PDF.
- Startup cần cân nhắc lazy loading; tránh mọi tab đọc DB/model ngay từ constructor.

---

# 2. Kiến trúc đích

## 2.1. Runtime architecture

```text
                         +----------------------+
                         |      PyQt6 UI        |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |   Application Layer  |
                         |  thin / no ML logic  |
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                      |                      |
             v                      v                      v
     PredictionService       WhatIfService          ReportService
             |                      |                      |
             +-----------+----------+----------------------+
                         |
                         v
                  +-------------+
                  | ML Platform  |
                  +------+------+ 
                         |
              +----------+-----------+
              |                      |
              v                      v
       Regression Model       Risk Classifier
              |                      |
              +----------+-----------+
                         |
                         v
                  Model Registry
                         |
                         v
                    Model Bundle
                         |
                         v
                 Feature / Schema
                         |
                         v
                   Data Platform
                         |
          +--------------+--------------+
          |                             |
          v                             v
    Validator / Quality          PostgreSQL / Staging
```

## 2.2. Data flow chuẩn

```text
Excel / CSV
   |
   v
Parse
   |
   v
Schema validation
   |
   v
Data quality report
   |
   +---- FAIL ----> Preview errors + no DB mutation
   |
   v
Staging
   |
   v
Transactional promotion
   |
   v
Production dataset
   |
   v
Feature engineering
   |
   v
Train / CV / model selection
   |
   v
Final test
   |
   v
Model bundle + registry metadata
   |
   v
PredictionService
   |
   +----------+-----------+-----------+
   |          |           |           |
   v          v           v           v
Diagnosis   What-If      EDA       Report
```

---

# 3. PHASE 0 — Freeze baseline trước khi sửa tiếp

## Issue REF-001 — Tạo baseline audit

**Priority:** P0

### Cần làm

- Tạo tag/branch cho trạng thái trước refactor tiếp theo.
- Ghi model hiện tại, dataset hiện tại, feature list, metrics hiện tại.
- Ghi các known issues vào `docs/baseline/`.
- Không lấy số từ README làm baseline nếu chưa có artifact/command chứng minh.

### Files đề xuất

```text
docs/baseline/current_metrics.json
docs/baseline/current_architecture.md
docs/baseline/current_features.md
docs/baseline/known_issues.md
```

### Definition of Done

- Có baseline reproducible bằng một command.
- Có test/data/model version được ghi rõ.
- Không có metric “ước lượng”.

---

# 4. PHASE 1 — Data Contract & Target Definition

## Issue DATA-001 — Xây Data Dictionary

**Priority:** P0

Tạo `docs/data_dictionary.md`.

Mỗi cột cần có:

- tên gốc trong Excel;
- tên nội bộ;
- kiểu dữ liệu;
- range hợp lệ;
- categorical/ordinal/continuous;
- được phép missing hay không;
- dùng cho prediction hay không;
- thời điểm dữ liệu có thể biết;
- có thể là target/derived target hay không.

## Issue DATA-002 — Xác định Prediction Time

**Priority:** P0

Phải ghi rõ hệ thống dự đoán tại thời điểm nào, ví dụ:

```text
Prediction point = cuối tuần 6
```

Sau đó chỉ những feature có thể biết trước/đúng thời điểm đó mới được dùng.

## Issue DATA-003 — Audit `diem_tong_ket`

**Priority:** P0

Xác định:

```text
source
calculation
availability time
whether derived from other input features
```

Mục tiêu: tránh model học lại công thức tính điểm cuối kỳ.

## Issue DATA-004 — Audit `nguy_co_hoc_vu`

**Priority:** P0

Xác định:

```text
source
label generation rule
whether derived from final score
class boundaries
class balance
```

Nếu risk label được tạo trực tiếp từ final score thì phải ghi rõ đây là derived label và đánh giá đúng ý nghĩa của classifier.

## Issue DATA-005 — Leakage audit tự động

**Priority:** P0

Tạo module/check:

```text
src/ml/leakage_audit.py
```

Kiểm tra:

- feature chứa target hoặc proxy target;
- feature được sinh sau prediction time;
- duplicate-derived variables;
- feature có quan hệ deterministic với target;
- preprocessing được fit ngoài fold;
- train/test contamination.

### Definition of Done

Một command kiểu:

```bash
python -m src.ml.leakage_audit
```

trả về PASS/FAIL rõ ràng.

---

# 5. PHASE 2 — Data Validation & Quality

## Issue DATA-010 — Validator đầy đủ

**Priority:** P0

Kiểm tra:

```text
missing required columns
wrong dtype
invalid numeric
invalid category
duplicate student ID
duplicate rows
missing target
out-of-range values
unexpected whitespace / encoding
```

## Issue DATA-011 — Phân loại data issue

Không gom tất cả thành “missing”. Dùng:

```text
MISSING
INVALID
OUTLIER
DUPLICATE
RISK_SIGNAL
```

Ví dụ:

```text
NULL        -> MISSING
score=-2    -> INVALID
extreme     -> OUTLIER
duplicate   -> DUPLICATE
attendance 25% -> RISK_SIGNAL
```

## Issue DATA-012 — Data Health theo tỷ lệ

Không dùng absolute threshold kiểu “15 invalid rows = bad”. Dùng:

```text
missing_rate
invalid_rate
duplicate_rate
outlier_rate
target_missing_rate
```

và ngưỡng có thể cấu hình.

## Issue DATA-013 — Upload preview

Trước khi commit dữ liệu, UI phải hiển thị:

```text
Rows
Columns
Missing
Invalid
Duplicates
Target status
Schema status
Overall status
```

User phải biết file có vấn đề gì trước khi DB thay đổi.

---

# 6. PHASE 3 — Database & Ingestion

## Issue DB-001 — Xóa đường ingest destructive

**Priority:** P0

Không để runtime gọi:

```python
Base.metadata.drop_all(...)
```

trong luồng upload bình thường.

Legacy `src/db/ingest.py` phải:

- xóa khỏi runtime;
- hoặc biến thành compatibility wrapper;
- hoặc deprecated rồi xóa trong phase cleanup.

## Issue DB-002 — Một ingestion path duy nhất

UI phải đi:

```text
UploadWidget
   ↓
IngestionService
   ↓
Validator
   ↓
Staging
   ↓
Transaction
```

Không:

```text
UploadWidget → db.ingest
```

## Issue DB-003 — Transactional ingest

Nếu insert lỗi:

```text
rollback
keep previous dataset intact
show error
```

## Issue DB-004 — Staging table / staging dataset

Khuyến nghị:

```text
student_staging
students
```

Flow:

```text
Excel
 ↓
staging
 ↓
validate
 ↓
preview
 ↓
promote
 ↓
production
```

## Issue DB-005 — Migration

Dùng Alembic hoặc cơ chế migration tương đương.

Không dùng `create_all/drop_all` để quản lý version production.

## Issue DB-006 — Repository/session consistency

Repository nên dùng một abstraction session/connection nhất quán. Không trộn session được inject với global engine nếu không có lý do rõ ràng.

---

# 7. PHASE 4 — Machine Learning Methodology

## 7.1. Chiến lược model

Không ép model cuối cùng phải là Linear Regression.

Linear Regression là **baseline bắt buộc**.

### Benchmark đề xuất

```text
Baseline
- DummyRegressor
- LinearRegression

Linear family
- Ridge
- Lasso
- ElasticNet

Feature expansion
- PolynomialFeatures + Ridge

Nonlinear / ensemble
- RandomForestRegressor
- HistGradientBoostingRegressor hoặc XGBoost
```

Không cần đưa 15 model vào chỉ để có nhiều số.

## Issue ML-001 — Chuẩn hóa Pipeline

**Priority:** P0

Mọi candidate phải là:

```text
Preprocessor
 + optional feature transform
 + estimator
```

nằm trong cùng pipeline khi CV.

## Issue ML-002 — CV trên raw train features

**Priority:** P0

Đúng:

```text
X_train raw
 ↓
Pipeline
 ↓
5-fold CV
```

Không:

```text
fit preprocessing trên toàn X_train
 ↓
CV
```

## Issue ML-003 — Model selection chỉ bằng CV

**Priority:** P0

Test set không được dùng để chọn model.

Flow:

```text
Train
 ↓
5-fold CV
 ↓
rank candidates
 ↓
select winner
 ↓
fit winner on train
 ↓
ONE final test
```

## Issue ML-004 — Parsimony rule có định nghĩa rõ

Rule có thể giữ nhưng phải được giải thích.

Ví dụ:

```text
nếu model phức tạp hơn chỉ thắng < 0.02 CV R²
→ ưu tiên model đơn giản hơn nếu MAE không xấu hơn đáng kể.
```

Không gọi đây là “luật khoa học tuyệt đối”; đây là policy của project.

## Issue ML-005 — So sánh không chỉ R²

Regression metrics:

```text
CV R² mean/std
CV MAE mean/std
Test R²
Test MAE
Test RMSE
```

Optional:

```text
Adjusted R²
Residual analysis
```

## Issue ML-006 — Classification metrics

Không chỉ Accuracy.

Cần:

```text
Accuracy
Macro F1
Weighted F1
Precision per class
Recall per class
F1 per class
Confusion matrix
High-risk precision
High-risk recall
```

Nếu probability được dùng, thêm:

```text
Brier score
Calibration curve
```

## Issue ML-007 — Class imbalance audit

Trước train:

```text
class counts
class percentages
```

Nếu lệch mạnh, cân nhắc:

```text
class_weight
stratified CV
threshold adjustment
calibration
```

## Issue ML-008 — Residual analysis cho regression

Tối thiểu:

```text
predicted vs actual
residual histogram
residual vs predicted
residual vs important features
```

Mục tiêu: xem Linear Regression còn pattern có hệ thống hay không.

---

# 8. PHASE 5 — Feature Engineering

## Issue FE-001 — Feature contract

Feature engineering phải có version:

```text
feature_version = feat_3
```

## Issue FE-002 — Đánh giá feature mới

Các feature như:

```text
lms_gio_per_video
academic_engagement_index
stress_motivation_ratio
low_engagement_flag
```

phải có:

- lý do tồn tại;
- công thức;
- range;
- xử lý zero/division-by-zero;
- availability time;
- test.

## Issue FE-003 — Tránh feature khó giải thích nếu không cần

Nếu feature tạo ra ratio hoặc interaction, báo cáo phải giải thích được ý nghĩa.

Không tạo 20 feature dẫn tới model khó giải thích chỉ để tăng R² vài phần nghìn.

## Issue FE-004 — Ordinal encoding

Nếu category có thứ tự nhưng không có bằng chứng khoảng cách đều, không tự động biến:

```text
1 / 2 / 3
```

thành biến số trong Linear Regression.

Ưu tiên OneHotEncoder hoặc chứng minh assumption.

---

# 9. PHASE 6 — Model Registry & Reproducibility

## Issue REG-001 — Một model bundle chuẩn

Bundle nên chứa:

```python
{
    "pipeline": pipeline,
    "metadata": metadata,
    "feature_names": feature_names,
    "schema_version": schema_version,
    "feature_version": feature_version,
    "dataset_version": dataset_version,
    "model_version": model_version,
}
```

## Issue REG-002 — Dataset version thật

Không để:

```text
default
```

lâu dài.

Ví dụ:

```text
ds-2026-10-04-001
```

hoặc hash dataset.

## Issue REG-003 — Model version thật

Model retrain phải có artifact revision.

Ví dụ:

```text
reg-linear-v3-20261004-110634
```

## Issue REG-004 — Không ghi đè lịch sử artifact

```text
models/artifacts/regression/
    linear_001.pkl
    lasso_002.pkl
    xgb_003.pkl
```

Registry giữ `active_model`.

## Issue REG-005 — Model fingerprint

Lưu:

```text
training timestamp
code version/git SHA
dataset hash
feature version
library versions
hyperparameters
seed
```

---

# 10. PHASE 7 — PredictionService

## Issue PRED-001 — PredictionService là single source of truth

Các màn hình:

```text
Diagnosis
What-If
Report
Insight
```

chỉ gọi:

```text
PredictionService
```

Không load model riêng.

## Issue PRED-002 — Không fake fallback

Đã có typed exception là hướng đúng.

Bắt buộc:

```text
Model missing
→ PredictionUnavailable

Model incompatible
→ ModelCompatibilityError

Predict failed
→ PredictionError
```

UI phải show lỗi rõ ràng.

## Issue PRED-003 — Tách raw prediction và display prediction

Internal:

```text
raw_prediction
```

Display:

```text
clip(raw_prediction, 0, 10)
```

Sensitivity/analysis có thể cần raw prediction để tránh clipping làm sai effect.

## Issue PRED-004 — Reliability semantics

Tên “confidence” không nên được dùng cho score dựa trên completeness.

Nên dùng:

```text
Data completeness
```

hoặc:

```text
Prediction reliability indicator
```

Nếu muốn probability/confidence thật sự thì phải có calibration/statistical basis.

## Issue PRED-005 — Reliability theo feature contract

Không chỉ hard-code 8 columns. Nên lấy model input schema từ registry.

Có thể tách:

```text
Critical feature completeness
Model input completeness
```

---

# 11. PHASE 8 — Risk Classification

## Issue RISK-001 — Audit target

Phải trả lời risk label đến từ đâu.

Nếu risk sinh trực tiếp từ final score, cần ghi rõ classification đang tái hiện rule hay thực sự dự báo early warning.

## Issue RISK-002 — Probability calibration

Nếu UI hiển thị:

```text
High risk probability = 84%
```

thì cần kiểm tra calibration.

## Issue RISK-003 — Business metric

Primary operational metric nên chú ý:

```text
Recall High Risk
```

nhưng phải cân bằng với Precision để tránh cảnh báo quá mức.

## Issue RISK-004 — Fairness / subgroup sanity check

Không cần triển khai fairness framework lớn nếu dữ liệu nhỏ, nhưng tối thiểu kiểm tra performance theo subgroup hợp lý nếu project sử dụng các demographic/context fields.

Không dùng demographic feature nếu không có lý do nghiệp vụ và không đánh giá risk của bias.

---

# 12. PHASE 9 — What-If Service

## Issue WI-001 — Migrate UI sang `WhatIfService`

**Priority:** P0

`WhatIfWidget` hiện còn import `WhatIfEngine`. Đây là việc phải sửa ngay.

## Issue WI-002 — Xóa `WhatIfEngine` legacy

Sau migration, xóa:

```text
src/core/whatif_engine.py
```

hoặc deprecate trong một commit riêng rồi delete.

Không để hai implementation tồn tại lâu dài.

## Issue WI-003 — Standardized sensitivity

Sensitivity nên biểu diễn:

```text
Δprediction / Δfeature
```

và ghi rõ unit.

Ví dụ:

```text
Attendance: +0.018 score / 1 percentage point
GK: +0.31 score / 1 point
```

## Issue WI-004 — Bound checking

Mọi feature change phải kiểm tra domain.

Ví dụ:

```text
score: 0–10
attendance: 0–100
stress: 1–5
motivation: 1–5
```

## Issue WI-005 — Không gọi “causal impact”

Wording:

```text
“Kịch bản mô phỏng dự báo”
```

không:

```text
“tăng attendance sẽ chắc chắn tăng điểm...”
```

## Issue WI-006 — Reverse solver phải có cost model rõ

Optimization objective cần giải thích:

```text
minimize intervention cost
subject to predicted score >= target
```

Cost weights phải cấu hình và có ý nghĩa sư phạm.

## Issue WI-007 — Unachievable target

UI cần hiện rõ:

```text
Không đạt được mục tiêu trong các giới hạn cho phép.
```

Không trả về một scenario vi phạm range.

## Issue WI-008 — Scenario comparison

Cho phép:

```text
Baseline
Scenario A
Scenario B
```

so sánh side-by-side.

---

# 13. PHASE 10 — Diagnosis

## Issue DG-001 — Dùng PredictionService

Không gọi `WhatIfEngine` trong diagnosis.

Flow:

```text
student
 ↓
PredictionService.predict_student()
 ↓
score
risk
probabilities
reliability
```

## Issue DG-002 — Tách “thực tế” và “dự báo”

Không viết:

```text
Điểm tổng kết = 6.42
```

nếu đó là prediction.

Dùng:

```text
Điểm tổng kết dự báo: 6.42
```

và nếu có actual:

```text
Điểm tổng kết thực tế: 6.10
```

## Issue DG-003 — Risk card không phụ thuộc màu duy nhất

Luôn có:

```text
text label
color
icon/badge shape
```

để không gây khó khăn cho người dùng khi màu không đủ rõ.

## Issue DG-004 — Explainability

Hiển thị:

```text
Top factors
Direction
Magnitude / contribution
Data quality caveat
```

Nếu model tree/boosting được chọn, cân nhắc SHAP.

---

# 14. PHASE 11 — Explainability

## Issue XAI-001 — Linear family

Nếu model là Linear/Ridge/Lasso:

```text
coefficient
standardized coefficient
contribution
```

nên được hiển thị.

## Issue XAI-002 — Tree/boosting

Nếu model winner là RF/XGBoost:

```text
SHAP summary
local explanation
feature contribution
```

không chỉ dùng feature importance global.

## Issue XAI-003 — Không biến explanation thành causal statement

Explanation nên nói:

```text
“đóng góp vào prediction theo mô hình”
```

không:

```text
“đây là nguyên nhân khiến sinh viên...”
```

---

# 15. PHASE 12 — Report

## Issue REPORT-001 — Metrics lấy từ runtime artifact

Không có fallback kiểu:

```python
0.9366
0.9431
```

Nếu metrics thiếu:

```text
MetricsMissingError
```

và UI báo “Chưa có kết quả đánh giá”.

## Issue REPORT-002 — Không hard-code model name

Không mặc định:

```text
Lasso Regression
```

nếu registry không trả về giá trị đó.

## Issue REPORT-003 — Báo cáo benchmark

Nên có bảng:

```text
Model | CV R² | CV MAE | Test R² | Test MAE | RMSE
```

để người dùng thấy quá trình nâng cấp model.

## Issue REPORT-004 — Model card

Báo cáo nên có:

```text
Selected model
Dataset version
Feature version
Model version
Training time
CV metrics
Test metrics
Limitations
```

## Issue REPORT-005 — Actual vs predicted rõ ràng

Không dùng `diem_tong_ket` thực tế nhưng đặt label “Dự báo”.

## Issue REPORT-006 — PDF/HTML phải đúng implementation

Nếu UI ghi “PDF”, phải có PDF renderer thật và test output.

---

# 16. PHASE 13 — PyQt6 UI/UX DESIGN PRINCIPLES

Đây là phần cần giữ nhất quán toàn app.

## 16.1. Nguyên tắc tổng thể

UI cần mang cảm giác:

```text
Academic Analytics Platform
```

không phải:

```text
Toolbox / Demo ML
```

### Ưu tiên

1. Trạng thái hệ thống rõ.
2. Một hành động chính trên mỗi màn hình.
3. Kết quả quan trọng nằm ở vùng nhìn đầu tiên.
4. Chi tiết kỹ thuật nằm sau lớp summary.
5. Không nhồi quá nhiều card/chart.
6. Không dùng màu để thay thế nội dung.
7. Không hiển thị số liệu có độ chính xác giả.

---

# 17. UI Shell / Navigation

## Issue UI-001 — Navigation hierarchy

6 tab hiện tại cần có vai trò rõ:

```text
1. Data
2. EDA
3. Models
4. Diagnosis
5. What-If
6. Report
```

### Recommended flow

```text
Data
 ↓
EDA
 ↓
Train / Evaluate
 ↓
Diagnosis
 ↓
What-If
 ↓
Report
```

UI không nên làm người dùng nhảy vào What-If trước khi model/data sẵn sàng.

## Issue UI-002 — Global status bar

Header/global status nên hiển thị:

```text
Dataset: Ready / Invalid / Missing
Database: Connected / Offline
Model: Ready / Stale / Missing
Last trained: timestamp
```

Đây là một trong những cải thiện UX đáng giá nhất.

---

# 18. UI Data Upload

## Flow đề xuất

```text
[Chọn file]
      ↓
[Preview]
      ↓
[Validation]
      ↓
[Confirm import]
      ↓
[Success]
```

### Không nên

```text
click upload
→ DB thay đổi ngay
```

### Trạng thái phải có

```text
Idle
Selecting
Parsing
Validating
Validation failed
Ready to import
Importing
Imported
Import failed
```

## Cảnh báo destructive action

Nếu replace dataset:

```text
Dataset hiện tại sẽ được thay thế.
Backup/version hiện tại: ds-xxxx
Bạn có chắc chắn?
```

Nên có option:

```text
Create new dataset version
```

thay vì chỉ overwrite.

---

# 19. UI Data Health

Đừng chỉ hiển thị:

```text
Healthy
```

Nên có một health summary:

```text
Dataset Health

Rows              1,000
Columns           21
Missing            1.4%
Invalid            0.2%
Duplicates         0.0%
Target available  Yes
Schema            PASS

Overall: READY
```

Nhấp vào metric sẽ mở chi tiết.

---

# 20. UI EDA

## Nguyên tắc

EDA không nên là “gallery of charts”.

Phân loại:

```text
Distribution
Relationship
Comparison
Risk breakdown
```

### Chart cần có

- histogram/boxplot cho điểm;
- scatter predicted/actual;
- feature vs target;
- risk class distribution;
- missingness;
- correlation nếu phù hợp.

### Tránh

- 6 chart cùng lúc không có insight;
- legend quá nhỏ;
- chart không có unit;
- pie chart cho quá nhiều category;
- màu sắc không nhất quán giữa các màn hình.

---

# 21. UI Model Training

## Issue UI-003 — Training progress có ý nghĩa

Hiện progress indefinite là chưa đủ.

Nên có:

```text
Stage 1/5 — Preparing data
Stage 2/5 — Cross-validation
Stage 3/5 — Selecting model
Stage 4/5 — Final evaluation
Stage 5/5 — Saving artifact
```

Nếu không thể tính % chính xác, dùng stage progress thay vì giả lập phần trăm.

## Issue UI-004 — Model comparison table

Nên hiển thị:

```text
Model
CV R²
CV MAE
Std
Complexity
Status
```

Model selected phải có badge rõ:

```text
SELECTED
```

## Issue UI-005 — Explain selection

Ngay bên dưới bảng:

```text
Why this model?

CV R² cao nhất.
Ridge/Lasso considered.
Complex model chỉ được chọn khi lợi ích đủ lớn.
```

Không để người dùng tự đoán.

---

# 22. UI Diagnosis

### Above the fold

```text
+------------------------------------------------+
| Student Profile       Risk: CAO               |
|                                                |
| Predicted score: 6.42 / 10                    |
| High-risk probability: 71%                     |
| Data completeness: 87.5%                       |
+------------------------------------------------+
```

Sau đó:

```text
Key factors
Data quality
Recommended support
Detailed metrics
```

### Tránh

- 10 card nhỏ bằng nhau;
- đưa toàn bộ raw data lên đầu;
- dùng “confidence 95%” khi đó chỉ là data completeness;
- wording kiểu “sẽ trượt”.

### Ngôn ngữ nên dùng

```text
Có nguy cơ học vụ
Cần theo dõi
Nên tư vấn
Dự báo
```

Không:

```text
Chắc chắn trượt
Sinh viên yếu
Không có khả năng
```

---

# 23. UI What-If — phần cần đầu tư nhất

Đây nên là **feature nổi bật nhất của app**, nhưng phải tránh gây hiểu nhầm causal.

## Layout đề xuất

```text
+----------------------------------------------------------+
| WHAT-IF SCENARIO                                         |
|----------------------------------------------------------|
| BASELINE               SCENARIO                          |
| Score 6.12             Score 6.48                       |
| Risk Medium            Risk Low/Medium                  |
|                                                          |
| [Attendance  75%] ────────────────●────                 |
| [Quiz        6.2] ───────────●────────                  |
| [Homework    7.0] ─────────────●─────                  |
| [LMS         24h] ────────────●──────                  |
|                                                          |
| Δ Score: +0.36                                      ↑   |
+----------------------------------------------------------+
| Sensitivity                                               |
| 1. GK          +0.31 / point                             |
| 2. Attendance  +0.018 / percentage point                 |
| 3. Homework    +0.14 / point                             |
+----------------------------------------------------------+
| Goal Solver                                               |
| Target score: [7.0]   [Find feasible intervention]      |
+----------------------------------------------------------+
```

## UI rules

### 1. Baseline luôn cố định

Không thay baseline khi slider thay đổi.

### 2. Scenario phải nổi bật

User phải nhìn thấy:

```text
Before
After
Delta
```

### 3. Đừng update nặng ở mỗi pixel slider

Dùng debounce/throttling; UI có thể cập nhật sau 100–250 ms sau khi user dừng kéo.

### 4. Input phải có unit

Không để:

```text
Attendance [75]
```

mà:

```text
Attendance [75%]
```

### 5. Không cho giá trị ngoài domain

Slider phải giới hạn bằng domain contract.

### 6. Có nút Reset

```text
Reset scenario
```

### 7. Hiển thị disclaimer ngắn gọn

```text
Đây là mô phỏng dự báo thống kê, không phải ước lượng tác động nhân quả.
```

Có tooltip/Help để giải thích sâu hơn.

### 8. Goal solver phải giải thích cost

Nếu trả về:

```text
+12% attendance
+0.5 quiz
```

thì phải nói vì sao đây là solution được chọn và giới hạn nào đã được áp dụng.

---

# 24. UI Risk & Color System

Không hard-code màu rải rác trong từng widget.

Tạo theme tokens:

```text
SUCCESS
WARNING
DANGER
INFO
SURFACE
TEXT_PRIMARY
TEXT_SECONDARY
BORDER
```

Risk system:

```text
Very Low
Low
Medium
High
```

Mỗi mức có:

```text
label + color + icon/badge
```

Không dùng đỏ/xanh là tín hiệu duy nhất.

---

# 25. UI Typography / Density

## Nên

- title rõ hierarchy;
- body 12–14 px;
- metric lớn 24–32 px;
- caption 11–12 px;
- line height đủ lớn;
- margin/padding nhất quán;
- bảng có sticky/resize header nếu cần.

## Tránh

- quá nhiều bold;
- toàn bộ text màu sáng mạnh;
- card có padding khác nhau;
- quá nhiều border/shadow;
- icon khác style giữa các tab.

---

# 26. UI Loading / Empty / Error / Stale States

Mỗi màn hình cần đủ 5 trạng thái:

```text
LOADING
READY
EMPTY
ERROR
STALE
```

### Ví dụ Model tab

```text
EMPTY:
Chưa có model.
[Huấn luyện mô hình]
```

```text
STALE:
Dataset đã thay đổi từ lần train cuối.
[Huấn luyện lại]
```

```text
ERROR:
Không tải được artifact X.
[Chi tiết lỗi] [Thử lại]
```

Không để UI trắng/đơ khi service lỗi.

---

# 27. UI Accessibility

Checklist:

```text
[ ] Không dùng màu duy nhất để biểu đạt status
[ ] Font đủ lớn
[ ] Contrast đủ
[ ] Keyboard navigation
[ ] Focus state
[ ] Tooltip cho thuật ngữ ML
[ ] Text thay thế cho icon
```

---

# 28. PHASE 14 — Legacy Cleanup

## Issue CLEAN-001 — Xóa duplicate runtime paths

Sau migration:

```text
src/core/whatif_engine.py     -> delete
src/db/ingest.py              -> delete/deprecate
legacy confidence logic       -> delete
legacy model loaders          -> delete
```

## Issue CLEAN-002 — Search toàn repo

Tìm:

```text
WhatIfEngine
joblib.load
ridge_regression_model.pkl
risk_classifier_model.pkl
preprocessor.pkl
Base.metadata.drop_all
except Exception: pass
```

Mục tiêu: mọi occurrence phải được xem xét.

## Issue CLEAN-003 — Exception swallowing

Không dùng:

```python
except Exception:
    pass
```

Nếu thực sự cần catch:

```python
except ExpectedError as exc:
    logger.exception(...)
    raise
```

---

# 29. PHASE 15 — Testing

## 29.1. Unit tests

```text
tests/unit/
    test_schema.py
    test_validator.py
    test_features.py
    test_preprocessor.py
    test_model_selection.py
    test_registry.py
    test_prediction_service.py
    test_whatif_service.py
    test_metrics.py
```

## 29.2. Integration tests

```text
tests/integration/
    test_ingestion.py
    test_training_pipeline.py
    test_prediction_flow.py
    test_report.py
    test_database.py
```

## 29.3. Contract tests

Test:

```text
raw input → pipeline → output
```

và:

```text
saved bundle → reload → same prediction
```

## 29.4. Failure-path tests

Phải test:

```text
missing file
empty Excel
missing required column
invalid range
duplicate ID
DB unavailable
model missing
corrupt model
feature mismatch
missing inference fields
unreachable target
report metric missing
```

## 29.5. Leakage tests

Phải có regression test đảm bảo:

```text
composite_exam_score never enters training features
```

và preprocessing không được fit ngoài fold.

---

# 30. PHASE 16 — Training CLI / Scripts

## Issue SCRIPT-001 — `scripts/train_models.py` dùng đúng contract mới

Không được tự preprocess trước khi gọi `ModelTrainer` nếu `ModelTrainer` chịu trách nhiệm Pipeline.

Flow:

```text
Load raw
 ↓
feature engineering
 ↓
split
 ↓
trainer
```

## Issue SCRIPT-002 — Một command để reproduce

Ví dụ:

```bash
python scripts/train_models.py --data data/sample.xlsx
```

Output phải bao gồm:

```text
Dataset version
Features
Candidate models
CV results
Selected model
Final test results
Artifact path
```

---

# 31. PHASE 17 — Environment / Docker / Launcher

## Issue ENV-001 — Docker credentials từ environment

Không hard-code:

```text
123456
```

Dùng:

```text
DB_USER
DB_PASSWORD
DB_NAME
```

## Issue ENV-002 — `.env` không commit secret

`.env.example` chỉ chứa placeholder.

## Issue ENV-003 — Healthcheck và startup readiness

Launcher nên:

```text
start docker
 ↓
wait for postgres health
 ↓
run migration
 ↓
launch app
```

Không assume DB sẵn ngay sau `docker compose up -d`.

## Issue ENV-004 — `run.bat` là source of truth

Nếu README nói one-click launcher làm X/Y/Z thì `run.bat` phải thực sự làm X/Y/Z.

Nếu không muốn launcher phức tạp, sửa README cho đúng thay vì overclaim.

## Issue ENV-005 — Fallback Excel phải rõ

Nếu Docker unavailable:

```text
UI banner:
“Database offline — running in read-only/local Excel mode.”
```

Không để user nghĩ đang dùng PostgreSQL khi thực tế không phải.

---

# 32. PHASE 18 — Dependency Management

## Issue DEV-001 — `pyproject.toml` là source of truth

Quản lý dependency trực tiếp ở `pyproject.toml`.

`requirements.txt` chỉ giữ nếu cần cho bootstrap/Windows deployment.

## Issue DEV-002 — Pin versions cần thiết

Đối với artifact ML, version của các thư viện quan trọng phải được lưu metadata vì pickle/joblib có thể phụ thuộc version.

---

# 33. PHASE 19 — CI/CD

## Issue CI-001 — GitHub Actions

Tối thiểu:

```text
.github/workflows/
    tests.yml
    lint.yml
```

## tests.yml

Chạy:

```text
pytest
```

## lint.yml

Chạy:

```text
ruff
black --check
```

Có thể thêm:

```text
mypy
pip-audit
bandit
```

## Issue CI-002 — CI smoke test

Test:

```text
import project
load fixture
train small model
load bundle
predict
```

Không nhất thiết train dataset lớn trong CI.

---

# 34. PHASE 20 — Logging / Observability

## Event categories

```text
APP_START
DB_CONNECTED
DATA_UPLOAD_STARTED
DATA_VALIDATED
DATA_IMPORT_SUCCEEDED
DATA_IMPORT_FAILED
TRAINING_STARTED
MODEL_EVALUATED
MODEL_SELECTED
MODEL_REGISTERED
PREDICTION_REQUEST
PREDICTION_FAILED
WHATIF_REQUEST
REPORT_GENERATED
```

## Logging rules

Không log dữ liệu sinh viên nhạy cảm đầy đủ nếu không cần.

Log identifiers ở mức tối thiểu.

Không log credential/token/password.

---

# 35. PHASE 21 — Security

Checklist:

```text
[ ] no hard-coded passwords
[ ] no secrets in git
[ ] .env ignored
[ ] no sensitive student data in logs
[ ] validate uploaded file type
[ ] file size limit
[ ] safe file path handling
[ ] sanitize report output
[ ] dependency audit
```

Nếu report HTML chứa dữ liệu nhập từ user, tránh raw HTML injection qua field text.

---

# 36. PHASE 22 — Performance

## Database

- index student ID;
- index fields thường truy vấn;
- tránh load toàn bộ dataset ở mỗi tab nếu không cần.

## UI

- QThread/QThreadPool cho training;
- lazy-load tab;
- debounce slider;
- cache model bundle;
- cache dataset summary;
- chart rendering chỉ khi visible.

## ML

- fixed random seed để reproducible;
- `n_jobs` có kiểm soát;
- giới hạn CV/training khi user chọn demo mode.

---

# 37. PHASE 23 — Documentation

## README phải có

```text
1. Problem statement
2. Architecture
3. Data schema
4. Prediction time
5. Target definition
6. Leakage policy
7. Model benchmark
8. Model selection rule
9. Metrics
10. What-If semantics
11. Explainability
12. Limitations
13. Installation
14. Running
15. Testing
16. Docker
17. Troubleshooting
18. Project structure
```

## Model methodology

Phải giải thích câu chuyện:

```text
Linear Regression baseline
 ↓
Regularization
 ↓
Feature expansion
 ↓
Nonlinear ensemble
 ↓
Cross-validation comparison
 ↓
Select best validated model
```

Điều này phù hợp với yêu cầu của giáo viên: hồi quy tuyến tính là nền tảng, nhưng được phép nghiên cứu nâng cấp mô hình.

---

# 38. PHASE 24 — Recommended ML Research Story

Đây là hướng nên dùng để viết báo cáo/slide.

## Bước 1 — Baseline

```text
Linear Regression
```

Mục đích:

- dễ diễn giải;
- có baseline rõ;
- tạo điểm so sánh.

## Bước 2 — Regularization

```text
Ridge
Lasso
ElasticNet
```

Câu hỏi nghiên cứu:

> Có multicollinearity/noise hay không? Regularization có ổn định mô hình không?

## Bước 3 — Nonlinear feature expansion

```text
PolynomialFeatures + Ridge
```

Câu hỏi:

> Quan hệ giữa feature và điểm có phi tuyến ở mức đáng kể không?

## Bước 4 — Ensemble

```text
Random Forest
XGBoost / Gradient Boosting
```

Câu hỏi:

> Interaction và nonlinear relationship có cải thiện dự báo không?

## Bước 5 — Model selection

Không chọn chỉ vì test score.

Dựa trên:

```text
CV performance
stability
MAE
complexity
interpretability
```

## Bước 6 — Final test

Chỉ một lần.

---

# 39. What-If theo từng loại model

## Nếu winner là Linear/Ridge/Lasso

Có thể tận dụng coefficients:

```text
Δprediction ≈ coefficient × Δfeature
```

để giải thích và goal-seeking.

## Nếu winner là Polynomial + Ridge

Giải thích qua transformed features/feature contribution; không nói coefficient raw đơn giản như LinearRegression.

## Nếu winner là XGBoost/RF

What-If nên dựa trên:

```text
actual model prediction difference
+
feature contribution / SHAP
```

Không dùng công thức heuristic khác model.

---

# 40. Definition of Done cho ML

Một model chỉ được coi là release-ready khi:

```text
[ ] target documented
[ ] prediction time documented
[ ] leakage audit passed
[ ] preprocessing inside pipeline
[ ] CV clean
[ ] model selection from CV only
[ ] final test untouched until selection complete
[ ] metrics persisted
[ ] model bundle reproducible
[ ] version metadata persisted
[ ] prediction reload test passed
[ ] report reads same metrics
```

---

# 41. Definition of Done cho Data

```text
[ ] schema contract documented
[ ] validation before DB mutation
[ ] quality preview available
[ ] ingestion transactional
[ ] no drop_all in upload runtime
[ ] dataset version generated
[ ] failed import keeps previous dataset intact
```

---

# 42. Definition of Done cho UI

```text
[ ] Data/DB/model global status visible
[ ] one primary CTA per screen
[ ] loading state
[ ] empty state
[ ] error state
[ ] stale state
[ ] no fake confidence
[ ] no hidden ML errors
[ ] risk communicated by text + color/icon
[ ] units shown
[ ] What-If baseline vs scenario clear
[ ] no excessive precision
[ ] long tasks off UI thread
```

---

# 43. Definition of Done cho Release

Trên máy sạch:

```text
1. git clone
2. run.bat
3. environment created
4. Docker/Excel mode works
5. sample data imports
6. data health shown
7. train succeeds
8. model registry updated
9. diagnosis works
10. What-If works
11. report works
12. tests pass
```

README phải mô tả chính xác từng bước thực tế.

---

# 44. Backlog ưu tiên toàn repo

## P0 — Blocking

| ID | Task |
|---|---|
| REF-001 | Freeze baseline |
| DATA-001 | Data dictionary |
| DATA-002 | Prediction time |
| DATA-003 | Audit final score target |
| DATA-004 | Audit risk target |
| DATA-005 | Automated leakage audit |
| DATA-010 | Full schema validator |
| DB-001 | Remove destructive ingestion runtime |
| DB-002 | One ingestion path |
| DB-003 | Transactional import |
| ML-001 | Pipeline contract |
| ML-002 | Leakage-safe CV |
| ML-003 | CV-based model selection |
| REG-001 | Standard model bundle |
| PRED-001 | Single PredictionService path |
| WI-001 | UI → WhatIfService |
| WI-002 | Remove legacy WhatIfEngine |
| DG-001 | Audit diagnosis model path |
| REPORT-001 | Remove all hard-coded metrics/fallbacks |
| SCRIPT-001 | Migrate training script |

## P1 — Important

| ID | Task |
|---|---|
| DATA-011 | Data issue taxonomy |
| DATA-012 | Rate-based health score |
| DATA-013 | Upload preview |
| DB-004 | Staging table |
| DB-005 | Migrations |
| FE-001 | Feature versioning |
| FE-002 | Feature docs/tests |
| FE-004 | Ordinal encoding review |
| REG-002 | Real dataset version |
| REG-003 | Real model version |
| REG-004 | Artifact history |
| REG-005 | Model fingerprint |
| PRED-003 | Raw vs clipped prediction |
| PRED-005 | Reliability from feature contract |
| RISK-002 | Probability calibration |
| RISK-003 | High-risk metrics |
| WI-003 | Standard sensitivity |
| WI-004 | Bounds |
| WI-006 | Explain solver cost |
| DG-002 | Actual vs predicted terminology |
| DG-004 | Explainability |
| REPORT-003 | Benchmark table |
| REPORT-004 | Model card |
| UI-003 | Stage-based training progress |
| UI-004 | Model comparison UI |
| UI-005 | Explain selection |
| ENV-001 | Secure Docker env |
| ENV-003 | DB readiness |
| ENV-004 | Launcher/README consistency |
| DEV-001 | Dependency source of truth |
| CI-001 | GitHub Actions |
| CI-002 | CI smoke test |

## P2 — Polish

| ID | Task |
|---|---|
| UI-006 | Advanced visual polish |
| UI-007 | Lazy-loaded charts |
| UI-008 | Keyboard/accessibility improvements |
| REPORT-005 | Better report layout |
| REPORT-006 | PDF styling |
| DOC-005 | Screenshots/demo GIF |
| PERF-001 | Query/index optimization |

---

# 45. Commit/branch strategy

Không gom toàn bộ thành một commit khổng lồ.

## Branches

```text
main
  |
  +-- refactor/v3
       |
       +-- fix/data-contract
       +-- fix/ingestion
       +-- refactor/ml-pipeline
       +-- feat/model-registry
       +-- refactor/prediction-service
       +-- refactor/whatif
       +-- refactor/diagnosis
       +-- fix/report
       +-- feat/tests-ci
       +-- fix/security
       +-- docs/v3-final
```

## Commit sequence gợi ý

```text
chore: freeze pre-refactor baseline
feat(data): introduce dataset contract
fix(data): validate before ingestion
fix(db): make ingestion transactional
refactor(ml): unify preprocessing pipeline
fix(ml): prevent cross-validation leakage
feat(ml): add benchmark candidates
fix(ml): select models from CV only
feat(registry): version model bundles
refactor(prediction): centralize inference
refactor(whatif): migrate UI to WhatIfService
fix(diagnosis): use PredictionService
fix(report): remove hard-coded metrics
chore(cleanup): remove legacy runtime paths
feat(test): add integration and contract tests
feat(ci): add GitHub Actions
fix(security): move DB credentials to env
fix(ui): add stale/loading/error states
docs: align README with implementation
```

---

# 46. Search checklist sau mỗi phase

Chạy toàn repo và kiểm tra các pattern sau:

```text
WhatIfEngine
joblib.load
ridge_regression_model.pkl
risk_classifier_model.pkl
preprocessor.pkl
Base.metadata.drop_all
except Exception:
pass
0.9366
0.9431
0.9724
123456
confidence
predicted score
```

Mục tiêu là mỗi occurrence phải có lý do tồn tại.

---

# 47. Final architecture checklist

Trước release v3.x, source tree nên tiến gần:

```text
student_analysis/
├── data/
│   ├── raw/
│   ├── staging/
│   └── sample/
├── docker/
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── target_definition.md
│   ├── ml_methodology.md
│   ├── whatif_methodology.md
│   └── baseline/
├── models/
│   ├── registry.json
│   └── artifacts/
├── scripts/
├── src/
│   ├── data/
│   ├── db/
│   ├── ml/
│   ├── services/
│   └── ui/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
├── .github/
│   └── workflows/
├── .env.example
├── pyproject.toml
├── docker-compose.yml
├── run.bat
└── README.md
```

---

# 48. Release Gate — chỉ release khi tất cả PASS

## Data

- [ ] Schema contract PASS
- [ ] Target definition PASS
- [ ] Prediction time PASS
- [ ] Leakage audit PASS
- [ ] Import validation PASS
- [ ] Transaction PASS

## ML

- [ ] Linear Regression baseline exists
- [ ] Candidate models benchmarked
- [ ] CV leakage prevented
- [ ] Model selected from CV
- [ ] Test untouched until final evaluation
- [ ] Metrics reproducible
- [ ] Registry consistent
- [ ] Artifact reload gives same prediction

## Prediction

- [ ] One PredictionService
- [ ] Risk probabilities valid/calibrated if displayed
- [ ] Reliability semantics correct
- [ ] No fake fallback

## What-If

- [ ] Uses WhatIfService
- [ ] No legacy engine
- [ ] Bounds enforced
- [ ] Sensitivity units correct
- [ ] Predictive disclaimer visible
- [ ] Reverse solver respects target and bounds

## UI

- [ ] Loading/empty/error/stale states
- [ ] Model/data status visible
- [ ] No misleading terminology
- [ ] Units visible
- [ ] Baseline/scenario comparison clear
- [ ] No excessive precision
- [ ] Long training is non-blocking

## Engineering

- [ ] Tests pass
- [ ] CI pass
- [ ] Docker config valid
- [ ] No secrets in repo
- [ ] Launcher matches README
- [ ] Documentation matches code

---

# 49. Mục tiêu chất lượng cuối cùng

Không đặt mục tiêu đơn giản là:

```text
R² cao nhất
Accuracy cao nhất
Nhiều feature nhất
Nhiều tab nhất
```

Mục tiêu cuối phải là:

```text
Correct data
    +
Leakage-safe ML
    +
Validated model improvement
    +
Consistent prediction path
    +
Explainable results
    +
Safe data ingestion
    +
Reliable What-If
    +
Clear UI states
    +
Reproducible artifacts
    +
Automated tests
    +
Documentation = implementation
```

## Cách trình bày đề tài sau khi hoàn thiện

Nên kể câu chuyện:

```text
Bài toán
  ↓
Dữ liệu sinh viên
  ↓
Data quality & leakage audit
  ↓
Linear Regression baseline
  ↓
Regularization / nonlinear feature expansion / ensemble
  ↓
Cross-validation benchmark
  ↓
Model selection
  ↓
Final independent test
  ↓
Model registry
  ↓
Prediction + Risk
  ↓
Explainability
  ↓
What-If predictive simulation
  ↓
Diagnosis / Report
```

Đây là câu chuyện kỹ thuật có chiều sâu hơn nhiều so với việc chỉ trình bày “app có 6 tab và model đạt X%”.

---

# 50. Audit references — repo hiện tại

Các điểm trong master plan được xây dựng dựa trên snapshot code hiện tại của repository:

- Repository: https://github.com/huybinh4356/student_analysis
- README: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/README.md
- Model training: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/core/model_trainer.py
- Prediction service: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/services/prediction_service.py
- What-If service: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/services/whatif_service.py
- What-If UI: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/ui/whatif_widget.py
- Diagnosis UI: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/ui/diagnosis_widget.py
- Upload UI: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/ui/upload_widget.py
- New ingestion: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/data/ingestion.py
- Legacy ingestion: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/db/ingest.py
- Model registry: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/models/registry.json
- Analysis UI: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/src/ui/analysis_widget.py
- Training script: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/scripts/train_models.py
- Docker: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/docker-compose.yml
- Launcher: https://raw.githubusercontent.com/huybinh4356/student_analysis/main/run.bat

---

# 51. One-page execution order

Nếu cần thực hiện ngay, hãy đi đúng thứ tự này:

```text
01. Freeze baseline
02. Define target + prediction time
03. Finish leakage audit
04. Finish schema/data validation
05. Migrate upload to new ingestion
06. Remove destructive DB path
07. Fix training script contract
08. Finalize benchmark pipeline
09. Linear baseline + Ridge/Lasso/ElasticNet
10. Polynomial + Ridge
11. RF/XGBoost benchmark
12. CV-based selection
13. Final test
14. Version model/data/features
15. PredictionService as single source of truth
16. Migrate Diagnosis
17. Migrate What-If
18. Delete legacy engines/loaders
19. Fix Report
20. Add explainability
21. Add tests
22. Add CI
23. Fix Docker/env/security
24. Fix launcher
25. Fix UI loading/error/stale states
26. Polish UX
27. Update README
28. Clean repo-wide legacy references
29. Clean-clone validation
30. Release
```

> **Rule:** Không thêm feature UI mới trước khi bước 18 hoàn thành. Không tối ưu KPI trước khi bước 12–13 hoàn thành.

---

## Final acceptance statement

`student_analysis` được coi là hoàn thiện khi **một đường chạy duy nhất từ upload → validation → database → feature engineering → CV/model selection → registry → prediction → What-If → diagnosis → report** không còn đi qua implementation legacy, không có hard-coded ML result, không có silent fallback và mọi kết quả có thể truy nguyên về dataset/model version tương ứng.
