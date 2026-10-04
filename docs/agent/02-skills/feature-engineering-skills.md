# SKILLS — Feature Engineering

## S-FE-01: Tạo feature tỷ lệ
- Tỷ lệ giữa 2 biến: `A / B`.
- Tỷ lệ phần trăm: `A / (A + B)`.
- Ví dụ: `TyLeVideo = Video / Gio`.

## S-FE-02: Tạo feature hiệu
- Hiệu 2 biến: `A - B`.
- Chênh lệch so với trung bình: `A - mean(A)`.
- Ví dụ: `ChenhLech = GK - THPT`.

## S-FE-03: Tạo feature tương tác
- Tích 2 biến: `A * B`.
- Tương tác có điều kiện: `A * (B > threshold)`.
- Ví dụ: `GK_x_NopBai = GK * NopBai`.

## S-FE-04: Biến đổi phân phối
- Log transform: `log(1 + x)` cho skew phải.
- Square root: `sqrt(x)` cho count data.
- Bình phương: `x²` để bắt phi tuyến.
- Box-Cox: cho phân phối chuẩn hóa.

**Code mẫu:**
```python
import numpy as np
from scipy import stats

def transform_skewed(series):
    if series.skew() > 1:
        return np.log1p(series)
    return series
## S-FE-05: Bin biến số
Chia đều: pd.cut(x, bins=5).

Chia theo quantile: pd.qcut(x, q=5).

Chia theo ngưỡng nghiệp vụ: pd.cut(x, bins=[0, 22, 25, 30]).

## S-FE-06: Feature selection
Lọc theo correlation với target.

Lọc theo VIF (loại đa cộng tuyến).

Lọc theo Lasso (hệ số = 0).

Lọc theo Random Forest feature importance.

Code mẫu:

python
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import Lasso

def select_features_lasso(X, y, alpha=0.01):
    lasso = Lasso(alpha=alpha)
    selector = SelectFromModel(lasso, prefit=False)
    selector.fit(X, y)
    return X.columns[selector.get_support()]