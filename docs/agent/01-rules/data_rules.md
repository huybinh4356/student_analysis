# RULES — Dữ liệu

## R-DATA-01: Không xóa dữ liệu mà không hỏi
- **Bắt buộc:** Trước khi xóa dòng/cột, giải thích lý do và xin xác nhận.
- **Ngoại lệ:** Cột ID (`Mã SV`, `Họ và Tên`) được phép bỏ tự động.
- **Lý do:** Mỗi dòng = 1 sinh viên. Xóa = mất thông tin.

## R-DATA-02: Không dùng dữ liệu tương lai
- **Bắt buộc:** Feature không được chứa thông tin của target.
- **Ví dụ sai:** Dùng "Điểm cuối kỳ" để dự đoán "Nguy Cơ" nếu Nguy Cơ tính từ điểm cuối kỳ.
- **Lý do:** Data leakage → model vô dụng thực tế.

## R-DATA-03: Kiểm tra leakage trước khi train
- **Bắt buộc:** Kiểm tra correlation giữa từng feature và target. Nếu > 0.95 → nghi ngờ.
- **Bắt buộc:** Kiểm tra feature có được tạo từ target không.
- **Cách kiểm tra:**
  ```python
  corr = df.corr()['target'].abs().sort_values(ascending=False)
  suspicious = corr[corr > 0.95]

  R-DATA-04: Chia train/test TRƯỚC khi xử lý
Bắt buộc: Chia 70/15/15 hoặc 80/20.

Bắt buộc: Fit scaler/encoder CHỈ trên train set.

Cấm: Fit trên toàn bộ dữ liệu rồi mới chia.

Code đúng:

X_train, X_test, y_train, y_test = train_test_split(X, y)
scaler.fit(X_train)  # Chỉ fit trên train
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)
R-DATA-05: Xử lý missing theo từng kiểu biến
Kiểu	Cách xử lý
Numeric	median (skew) hoặc mean (chuẩn)
Categorical	mode
Ordinal	median của thứ tự
Text	"unknown" hoặc bỏ
R-DATA-06: Xử lý outlier phải có lý do
Bắt buộc: Phát hiện bằng IQR hoặc z-score.

Bắt buộc: Ghi lại lý do giữ/bỏ từng outlier.

Cấm: Xóa outlier mà không kiểm tra đó có phải giá trị thật không.

Ngưỡng: IQR × 1.5 = outlier nhẹ, IQR × 3 = outlier nặng.

R-DATA-07: Encode đúng kiểu biến
Kiểu	Cách encode
Nominal (không thứ tự)	One-hot hoặc Target encoding
Ordinal (có thứ tự)	Ordinal encoding (0,1,2...)
Binary	0/1
Cấm	Label encoding cho nominal
R-DATA-08: Scale sau khi encode
Bắt buộc: StandardScaler hoặc RobustScaler cho numeric.

Bắt buộc: Fit trên train, transform trên test.

Không cần: Scale cho tree-based (Random Forest, XGBoost).

Lý do: Scale giúp linear models hội tụ nhanh hơn.