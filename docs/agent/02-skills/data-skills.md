# SKILLS — Dữ liệu

## S-DATA-01: Đọc và kiểm tra dữ liệu

- **Input:** File Excel/CSV
- **Output:** Báo cáo tổng quan

**Khả năng:**

- Đọc `.xlsx`, `.csv` với pandas.
- Phát hiện sheet name, header rows.
- Kiểm tra shape, dtype, missing, duplicate.
- Phát hiện encoding issues (tiếng Việt).
dưa

**Code mẫu:**

```python
def load_and_inspect(file_path: str) -> tuple:
    df = pd.read_excel(file_path, sheet_name=0)
    report = {
        'shape': df.shape,
        'dtypes': df.dtypes.to_dict(),
        'missing': df.isnull().sum().to_dict(),
        'duplicates': df.duplicated().sum(),
        'memory_mb': df.memory_usage(deep=True).sum() / 1024**2
    }
    return df, report
## S-DATA-02: Phân loại biến tự động
Input: DataFrame

Output: Dict phân loại biến

Khả năng:

Nhận diện numeric, categorical, ordinal, text, datetime.

Đề xuất cách xử lý cho từng loại.

Code mẫu:
def classify_columns(df: pd.DataFrame) -> dict:
    result = {'numeric': [], 'nominal': [], 'ordinal': [], 'text': [], 'id': []}
    for col in df.columns:
        if 'Mã' in col or 'Tên' in col:
            result['id'].append(col)
        elif df[col].dtype in ['int64', 'float64']:
            if df[col].nunique() <= 5 and df[col].min() >= 1:
                result['ordinal'].append(col)
            else:
                result['numeric'].append(col)
        elif df[col].nunique() < 20:
            result['nominal'].append(col)
        else:
            result['text'].append(col)
    return result

## S-DATA-03: Xử lý missing data
Input: DataFrame có missing

Output: DataFrame sạch + báo cáo

Khả năng:

So sánh 3 cách: xóa, mean/median, KNN.

Đề xuất cách tốt nhất dựa trên % missing.

Ghi lại quyết định.

Quy tắc:

% Missing Cách xử lý
< 5% Xóa dòng
5-20% Impute median/mode
20-50% KNN hoặc model-based
> 50% Bỏ cột
S-DATA-04: Phát hiện và xử lý outlier
Input: DataFrame

Output: Danh sách outlier + đề xuất

Khả năng:

Dùng IQR, z-score, Isolation Forest.

Phân biệt outlier thật vs lỗi nhập.

Đề xuất giữ/bỏ/winsorize.

Code mẫu:

python
def detect_outliers_iqr(df, col):
    Q1, Q3 = df[col].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
    return df[(df[col] < lower) | (df[col] > upper)]
## S-DATA-05: Encode biến phân loại
Input: DataFrame + loại biến

Output: DataFrame encoded

Khả năng:

One-hot cho nominal.

Ordinal encoding cho ordinal.

Target encoding cho high-cardinality.

Label encoding cho text đơn giản.

Quy tắc chọn:

Số giá trị Cách encode
2 Binary (0/1)
3-10 One-hot
10-50 Target encoding
> 50 Bỏ hoặc embedding
