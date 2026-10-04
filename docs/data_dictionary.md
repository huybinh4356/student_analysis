# Data Dictionary — Student Analysis System

> **Version**: Draft v1 (cần xác minh với dataset thực tế — Phase 1)  
> **Target Definition**: PENDING audit (xem mục "Target Generation Audit" bên dưới)

---

## Raw Features (từ Excel upload)

| Column | Type | Range | Used at Predict? | Source | Notes |
|---|---|---|---|---|---|
| `ma_sv` | string | — | ❌ ID only | Excel | Mã sinh viên, unique identifier |
| `ho_ten` | string | — | ❌ Text | Excel | Họ và tên |
| `gioi_tinh` | nominal | Nam/Nữ | ✅ | Excel | Giới tính |
| `que_quan` | nominal | Tỉnh/thành | ✅ | Excel | Quê quán |
| `nganh_hoc` | nominal | Ngành | ✅ | Excel | Ngành học |
| `diem_thpt` | float | 0–30 | ✅ | Excel | Điểm thi THPT |
| `diem_gk` | float | 0–10 | ✅ | Excel | Điểm giữa kỳ |
| `lms_gio_truy_cap` | float | 0–300 | ✅ | Excel/LMS | Giờ truy cập LMS |
| `lms_xem_video` | int | 0–∞ | ✅ | Excel/LMS | Số video đã xem |
| `nop_bai_dung_han` | float | 0–100 | ✅ | Excel | % nộp bài đúng hạn |
| `diem_quiz` | float | 0–10 | ✅ | Excel | Điểm quiz |
| `diem_bai_tap` | float | 0–10 | ✅ | Excel | Điểm bài tập |
| `hoan_canh_kt` | ordinal | Khó/TB/Khá giả | ✅ | Excel | Hoàn cảnh kinh tế |
| `di_lam_them` | nominal | Có/Không | ✅ | Excel | Đi làm thêm |
| `muc_do_stress` | ordinal | 1–5 | ✅ | Excel | Mức độ stress |
| `dong_luc_hoc` | float | 1–5 | ✅ | Excel | Động lực học |
| `chuyen_can` | float | 0–100 | ✅ | Excel | % chuyên cần |
| `muc_tuong_tac` | ordinal | Thụ động/BT/Tích cực | ✅ | Excel | Mức tương tác lớp |
| `ghi_chu_gv` | text | free | ❌ Text | Excel | Ghi chú giảng viên |
| `nguy_co_hoc_vu` | nominal | 4 classes | 🎯 TARGET | Excel/Derived | **Cần audit: do GV label hay derived từ điểm?** |
| `diem_tong_ket` | float | 0–10 | 🎯 TARGET | Excel | **Cần audit: công thức hay thực tế?** |

---

## Engineered Features (tạo trong FeatureEngineer)

| Column | Formula | Used at Predict? | Leakage Risk |
|---|---|---|---|
| `lms_gio_per_video` | `lms_gio_truy_cap / lms_xem_video` | ✅ | Thấp |
| `academic_engagement_index` | `0.5 * chuyen_can + 0.5 * nop_bai_dung_han` | ✅ | Thấp |
| `stress_motivation_ratio` | `muc_do_stress / (dong_luc_hoc + 1e-5)` | ✅ | Thấp |
| `composite_exam_score` | `0.4 * diem_gk + 0.3 * diem_quiz + 0.3 * diem_bai_tap` | ✅ | ⚠️ **CAO — cần audit** |
| `low_engagement_flag` | `(chuyen_can < 50) \| (nop_bai_dung_han < 50)` | ✅ | Thấp |

---

## ✅ Target Generation Audit — RESOLVED

> **Xác nhận (2026-10-04)**: `diem_tong_ket` và `nguy_co_hoc_vu` là **dữ liệu thực tế có nhãn** (real labeled historical data), không phải fabricated hay derived từ formula. Đây là supervised learning setup chuẩn.

### Semantics rõ ràng

| Target | Nguồn | Vai trò |
|---|---|---|
| `diem_tong_ket` | Điểm tổng kết thực tế từ lịch sử sinh viên | Regression label — predict cho sinh viên mới chưa thi cuối kỳ |
| `nguy_co_hoc_vu` | Nhãn thực tế (GV đánh giá / hồ sơ học vụ) | Classification label — predict risk level cho kỳ hiện tại |

### Prediction scenario

```
Dữ liệu lịch sử (có nhãn)
    diem_gk, chuyen_can, lms_gio_truy_cap, ... → diem_tong_ket
    ↓
    Train supervised model
    ↓
Sinh viên mới (chưa có kết quả cuối kỳ)
    diem_gk, chuyen_can, lms_gio_truy_cap, ... → PREDICT diem_tong_ket
                                                → PREDICT nguy_co_hoc_vu
```

### ⚠️ Leakage — ĐÃ XÁC NHẬN SEVERE

> **Kết quả chạy thực tế** trên `du_lieu_sinh_vien_khuyet_thieu_v2.xlsx` (1,200 rows):

```
composite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT
  Pearson r  : 0.9683
  R² (approx): 0.9376  (93.8%)
```

**Individual feature correlations với diem_tong_ket:**

| Feature | Pearson r | R² |
|---|---|---|
| `diem_gk` | 0.9263 | 0.858 |
| `diem_quiz` | 0.9283 | 0.862 |
| `diem_bai_tap` | 0.9442 | 0.892 |
| `chuyen_can` | 0.7371 | 0.543 |
| `diem_thpt` | 0.6658 | 0.443 |
| `composite_exam_score` | **0.9683** | **0.938** |

**Verdict**: `composite_exam_score` là proxy gần như hoàn hảo của target.

> R²=94% trong README rất có khả năng bị inflate bởi `composite_exam_score`. Feature này **PHẢI bị loại bỏ** khỏi training set.

**Quyết định:** Loại bỏ `composite_exam_score`. Dùng `diem_gk`, `diem_quiz`, `diem_bai_tap` riêng lẻ vẫn giữ được signal tốt mà không leakage.

### Prediction time

**Đã xác định**: Model predict **sau khi có điểm giữa kỳ** (mid-semester).

| Feature nhóm | Có ở prediction time? |
|---|---|
| `diem_thpt`, nhân khẩu học | ✅ Luôn có |
| `diem_gk`, `diem_quiz`, `diem_bai_tap` | ✅ Sau giữa kỳ |
| `chuyen_can`, `lms_gio_truy_cap` | ✅ Tích lũy đến thời điểm predict |
| `muc_do_stress`, `dong_luc_hoc` | ✅ Survey tại thời điểm |
| `diem_tong_ket` | ❌ Target — chỉ có sau cuối kỳ (không dùng làm feature) |

---

## Ordinal Encoding (hiện tại)

| Column | Mapping |
|---|---|
| `hoan_canh_kt` | Khó khăn→1, Trung bình→2, Khá giả→3 |
| `muc_tuong_tac` | Thụ động→1, Bình thường→2, Tích cực→3 |
| `nguy_co_hoc_vu` | Rất thấp→1, Thấp→2, Trung bình→3, Cao→4 |

---

## Risk Class Definition (cần xác minh)

| Class | Ordinal | Ý nghĩa giáo dục | WhatIf threshold |
|---|---|---|---|
| Rất thấp | 1 | Học lực Giỏi/Xuất sắc | score ≥ 8.0 |
| Thấp | 2 | Học lực Khá | score ≥ 6.5 |
| Trung bình | 3 | Cần cố gắng | score ≥ 5.0 |
| Cao | 4 | Có nguy cơ học vụ | score ≥ 3.5 |

> **Lưu ý**: WhatIf dùng threshold trên để gán risk, KHÔNG dùng classifier. Phải thống nhất về semantic.
