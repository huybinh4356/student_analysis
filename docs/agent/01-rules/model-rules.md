# RULES — Model

## R-MODEL-01: Luôn có baseline
- **Bắt buộc:** Chạy baseline (dự đoán trung bình) trước.
- **Mục đích:** So sánh model phải tốt hơn baseline.
- **Code:**
  ```python
  baseline_pred = np.full_like(y_test, y_train.mean())
  baseline_rmse = mean_squared_error(y_test, baseline_pred, squared=False)
  R-MODEL-02: Luôn dùng cross-validation
Bắt buộc: K-fold (k=5 hoặc 10) cho mọi model.

Bắt buộc: Báo cáo mean ± std của metrics.

Cấm: Chỉ báo cáo 1 lần train/test.

Code:scores = cross_val_score(model, X, y, cv=5, scoring='r2')
print(f"R² = {scores.mean():.3f} ± {scores.std():.3f}")
R-MODEL-03: So sánh ít nhất 5 model
Bắt buộc: Linear, Ridge, Lasso, Random Forest, XGBoost.

Khuyến khích: Thêm Elastic Net, Gradient Boosting.

R-MODEL-04: Đánh giá bằng nhiều metrics
Loại bài toán	Metrics bắt buộc
Regression	R², Adjusted R², RMSE, MAE
Classification	Accuracy, Precision, Recall, F1, AUC
Cấm	Chỉ dùng 1 metric
R-MODEL-05: Không tham model phức tạp
Nguyên tắc: Nếu Ridge và XGBoost chênh < 0.03 R² → chọn Ridge.

Lý do: Ridge giải thích được, nhanh, nhẹ.

R-MODEL-06: Kiểm tra overfitting
Bắt buộc: So sánh train score và test score.

Cảnh báo: Nếu chênh > 0.1 → overfit.

Xử lý: Regularization, giảm feature, thêm dữ liệu.

R-MODEL-07: Lưu model và preprocessing pipeline
Bắt buộc: Dùng joblib để lưu.

Bắt buộc: Lưu cả scaler, encoder, feature names.

Code:import joblib
joblib.dump({
    'model': model,
    'scaler': scaler,
    'feature_names': feature_names
}, 'model.pkl')
R-MODEL-08: Giải thích được model
Bắt buộc: Có feature importance hoặc hệ số β.

Bắt buộc: Giải thích được tại sao chọn model đó.

Cấm: Dùng black-box mà không giải thích.