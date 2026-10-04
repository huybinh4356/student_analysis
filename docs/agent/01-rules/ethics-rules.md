# RULES — Đạo đức

## R-ETH-01: Không dán nhãn sinh viên
- **Cấm:** "Sinh viên này sẽ rớt".
- **Đúng:** "Sinh viên này có nguy cơ, cần hỗ trợ".
- **Lý do:** Tránh gây áp lực tâm lý, định kiến.

## R-ETH-02: Bảo mật dữ liệu
- **Bắt buộc:** Ẩn danh khi phân tích.
- **Bắt buộc:** Không chia sẻ dữ liệu ra ngoài.
- **Bắt buộc:** Chỉ giảng viên dạy lớp đó xem được.
- **Lý do:** Bảo vệ quyền riêng tư sinh viên.

## R-ETH-03: Không thay thế phán đoán con người
- **Bắt buộc:** Nêu rõ "Hệ thống chỉ gợi ý, giảng viên quyết định".
- **Cấm:** Khuyến nghị hành động cứng nhắc.
- **Lý do:** AI không hiểu hoàn cảnh cá nhân.

## R-ETH-04: Kiểm tra bias
- **Bắt buộc:** Kiểm tra model có thiên vị giới tính, vùng miền không.
- **Bắt buộc:** Báo cáo nếu có bias.
- **Cách kiểm tra:**
  ```python
  for group in df['Giới Tính'].unique():
      subset = df[df['Giới Tính'] == group]
      print(f"{group}: RMSE = {calculate_rmse(subset)}")
## R-ETH-05: Minh bạch về sai số
Bắt buộc: Luôn báo cáo RMSE, MAE, khoảng tin cậy.

Cấm: Nói "dự đoán chính xác 100%".

Ví dụ đúng: "Dự đoán 6.5 ± 0.5 điểm với độ tin cậy 95%."