# SKILLS — EDA (Exploratory Data Analysis)

## S-EDA-01: Thống kê mô tả
- **Output:** Bảng thống kê đầy đủ

**Khả năng:**
- Mean, median, std, min, max, quartiles.
- Skewness, kurtosis.
- Unique count, missing count.

**Code mẫu:**
```python
def describe_data(df: pd.DataFrame) -> pd.DataFrame:
    stats = df.describe(include='all').T
    stats['skew'] = df.select_dtypes('number').skew()
    stats['missing_pct'] = df.isnull().mean() * 100
    stats['unique'] = df.nunique()
    return stats
## S-EDA-02: Vẽ biểu đồ tự động
Input: DataFrame + loại biến

Output: Biểu đồ phù hợp

Khả năng:

Histogram cho numeric.

Bar chart cho categorical.

Boxplot cho outlier.

Scatter cho quan hệ 2 biến.

Heatmap cho correlation.

Logic chọn chart:

python
def suggest_chart(col_type: str, n_unique: int) -> list:
    if col_type == 'numeric':
        return ['histogram', 'boxplot', 'violin']
    elif col_type == 'ordinal':
        return ['bar', 'boxplot']
    elif col_type == 'nominal':
        return ['pie', 'bar'] if n_unique <= 5 else ['bar']
    return ['bar']
## S-EDA-03: Phân tích tương quan
Output: Correlation matrix + insight

Khả năng:

Pearson cho numeric-numeric.

Spearman cho ordinal.

Cramér's V cho categorical-categorical.

Phát hiện đa cộng tuyến (VIF > 10).

Code mẫu:

python
from statsmodels.stats.outliers_influence import variance_inflation_factor

def check_multicollinearity(X: pd.DataFrame) -> pd.DataFrame:
    vif = pd.DataFrame()
    vif['feature'] = X.columns
    vif['VIF'] = [variance_inflation_factor(X.values, i) 
                  for i in range(X.shape[1])]
    return vif[vif['VIF'] > 10]
## S-EDA-04: Phân tích target
Output: Báo cáo về target

Khả năng:

Phân phối target.

Kiểm tra imbalance.

Quan hệ giữa feature và target.

Đề xuất xử lý imbalance (SMOTE, class weight).