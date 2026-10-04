# SKILLS — Modeling

## S-MODEL-01: Train model regression
- Linear Regression, Ridge, Lasso, Elastic Net.
- Cross-validation.
- Đánh giá: R², RMSE, MAE.

## S-MODEL-02: Train model classification
- Logistic Regression, Random Forest, XGBoost.
- Xử lý imbalance.
- Đánh giá: Accuracy, F1, AUC.

## S-MODEL-03: So sánh model tự động
- **Output:** Bảng so sánh

**Khả năng:**
- Chạy 5+ model.
- Cross-validation cho mỗi model.
- Xếp hạng theo metric chính.
- Đề xuất model tốt nhất kèm lý do.

**Code mẫu:**
```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score

def compare_models(X, y, cv=5):
    models = {
        'Linear': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.01),
        'RF': RandomForestRegressor(n_estimators=200),
        'XGB': XGBRegressor(n_estimators=200)
    }
    results = {}
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        results[name] = {
            'mean': scores.mean(),
            'std': scores.std()
        }
    return pd.DataFrame(results).T.sort_values('mean', ascending=False)
##  S-MODEL-04: Hyperparameter tuning
GridSearchCV.

RandomizedSearchCV.

Optuna (nếu cần).

Cross-validation trong tuning.

##S-MODEL-05: Giải thích model
Hệ số β cho linear models.

Feature importance cho tree-based.

SHAP values (nếu cần).

Partial dependence plots.

## S-MODEL-06: Lưu và load model
Lưu pipeline hoàn chỉnh.

Load và predict dữ liệu mới.

Versioning model.

Code mẫu:

python
import joblib

def save_model(model, scaler, feature_names, path):
    joblib.dump({
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names
    }, path)

def load_model(path):
    bundle = joblib.load(path)
    return bundle['model'], bundle['scaler'], bundle['feature_names']