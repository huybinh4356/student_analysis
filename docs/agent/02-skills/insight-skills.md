# SKILLS — Insight

## S-INSIGHT-01: Sinh cảnh báo tự động
**Khả năng:**
- Cảnh báo missing > 20%.
- Cảnh báo outlier > 5%.
- Cảnh báo đa cộng tuyến > 0.8.
- Cảnh báo R² thấp < 0.5.

**Code mẫu:**
```python
def generate_warnings(df, results):
    warnings = []
    for col, pct in (df.isnull().mean()*100).items():
        if pct > 20:
            warnings.append(f" {col} thiếu {pct:.1f}%")
    if results['r2'] < 0.5:
        warnings.append(f" R² = {results['r2']:.2f} khá thấp")
    return warnings
## S-INSIGHT-02: Sinh lời khuyên
Khả năng:

Từ feature importance → lời khuyên hành động.

Từ dự đoán → nhóm sinh viên nguy cơ.

Từ what-if → đề xuất can thiệp.

Template:

python
def generate_advice(feature, coef, target):
    direction = "tăng" if coef > 0 else "giảm"
    strength = "mạnh" if abs(coef) > 1 else "nhẹ"
    return f"{feature} ảnh hưởng {strength}: cứ tăng 1 đơn vị, {target} {direction} {abs(coef):.2f}"
## S-INSIGHT-03: Phân tích what-if
Khả năng:

Thay đổi 1 biến → xem dự đoán thay đổi.

Tính "tiềm năng cải thiện" cho từng hành động.

Xếp hạng hành động theo tác động.

Code mẫu:

python
def what_if_analysis(model, student, feature, new_value):
    current = student.copy()
    modified = student.copy()
    modified[feature] = new_value
    
    pred_current = model.predict(current)[0]
    pred_modified = model.predict(modified)[0]
    
    return {
        'feature': feature,
        'change': new_value - student[feature],
        'pred_current': pred_current,
        'pred_modified': pred_modified,
        'improvement': pred_modified - pred_current
    }
## S-INSIGHT-04: Phát hiện bất thường
Khả năng:

So sánh dự đoán vs thực tế.

Phát hiện sinh viên có chênh lệch lớn.

Đề xuất kiểm tra.

Code mẫu:

python
def detect_anomalies(df, y_true, y_pred, threshold=3):
    residuals = y_true - y_pred
    anomalies = df[abs(residuals) > threshold].copy()
    anomalies['residual'] = residuals[abs(residuals) > threshold]
    return anomalies