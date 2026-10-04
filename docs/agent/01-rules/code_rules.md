# RULES — Code

## R-CODE-01: Tách logic khỏi giao diện
- **Bắt buộc:** Core logic trong `src/core/`, UI trong `src/ui/`.
- **Lý do:** Dễ test, dễ đổi UI.
- **Cấm:** Import PyQt trong `core/`.

## R-CODE-02: Mọi hàm phải có docstring
```python
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Xử lý dữ liệu thô thành dữ liệu sạch.

    Args:
        df: Dữ liệu thô từ Excel.

    Returns:
        Dữ liệu đã xử lý.

    Raises:
        ValueError: Nếu df rỗng.
    """

## R-CODE-03: Try/except mọi nơi có thể lỗi
Bắt buộc: Bọc mọi thao tác file I/O.

Bắt buộc: Bọc mọi thao tác database.

Bắt buộc: Bọc mọi thao tác model.

Bắt buộc: Hiện thông báo lỗi thân thiện, không crash.

##R-CODE-04: Không hardcode đường dẫn
Cấm: pd.read_excel('C:/Users/.../data.xlsx')

Bắt buộc: Dùng relative path hoặc config file.

Code:
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
##R-CODE-05: Comment cho logic phức tạp
Bắt buộc: Comment tại sao, không phải làm gì.

Ví dụ tốt: # Dùng median vì cột này có outlier

Ví dụ xấu: # Tính median
##R-CODE-06: Đặt tên rõ ràng
Loại	Đúng	Sai
Biến	diem_trung_binh	x, dtb
Hàm	tinh_diem_tong_ket()	calc()
Class	DataPreprocessor	DP
Constant	MAX_ITERATIONS	mi
## R-CODE-07: Không lặp code (DRY)
Nguyên tắc: Nếu code lặp 3 lần → tách thành hàm.

Bắt buộc: Dùng pipeline cho preprocessing.

##R-CODE-08: Version control
Bắt buộc: Commit thường xuyên, message rõ ràng.

Format: [type] Mô tả ngắn

Types: feat, fix, docs, refactor, test, chore

Ví dụ: [feat] Thêm module xử lý missing data