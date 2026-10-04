# 01 — RULES

## Tổng quan

5 nhóm quy tắc bắt buộc cho Agent. **Vi phạm bất kỳ quy tắc nào = fail dự án.**

| File | Nhóm | Số quy tắc |
|------|------|------------|
| [data-rules.md](./data-rules.md) | Dữ liệu | 8 |
| [model-rules.md](./model-rules.md) | Model | 8 |
| [code-rules.md](./code-rules.md) | Code | 8 |
| [communication-rules.md](./communication-rules.md) | Giao tiếp | 6 |
| [ethics-rules.md](./ethics-rules.md) | Đạo đức | 5 |

## Nguyên tắc ưu tiên

Khi có xung đột giữa các rules:
1. **Ethics** > tất cả
2. **Data** > Model > Code
3. **Communication** áp dụng cho mọi tương tác

## Format quy tắc

Mỗi quy tắc có format:
R-XXX-NN: Tên quy tắc
Bắt buộc: ...

Cấm: ...

Ngoại lệ: ...

Lý do: ...