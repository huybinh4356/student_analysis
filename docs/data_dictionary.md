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

## 🚨 Target Generation Audit (PENDING — Gating Item)

### Câu hỏi phải trả lời trước khi train bất cứ model nào:

**1. `diem_tong_ket` được tạo ra như thế nào?**

- [ ] Option A: Điểm cuối kỳ thực tế từ học bạ (không có leakage)
- [ ] Option B: Được tính từ `0.3*diem_gk + 0.3*diem_bai_tap + 0.4*cuoi_ky` — cần có `cuoi_ky` trong data
- [ ] Option C: **Được tính từ formula dùng chính các feature** (GK, Quiz, BT) → **LEAKAGE NGHIÊM TRỌNG**

> **Nếu là Option C**: `composite_exam_score = 0.4*GK + 0.3*Quiz + 0.3*BT` sẽ gần như predict được target hoàn toàn, giải thích R² ~94% một cách giả tạo. Feature này PHẢI bị loại bỏ hoặc target phải được redefined.

**2. `nguy_co_hoc_vu` được tạo ra như thế nào?**

- [ ] Option A: Giảng viên label thủ công từ quan sát (ground truth thực)
- [ ] Option B: Derived từ `diem_tong_ket` bằng threshold → **Vòng tròn logic**: dùng features để predict target, target được derive từ features
- [ ] Option C: Derived từ combo nhiều yếu tố (GPA + stress + attendance) → Cần biết formula

**3. Prediction time là khi nào?**

- [ ] Đầu kỳ: Chỉ có `diem_thpt`, `gioi_tinh`, `que_quan`, `nganh_hoc`
- [ ] Giữa kỳ (Week 6): Có thêm `diem_gk`, `chuyen_can` tuần 1-6, `lms_gio_truy_cap`, v.v.
- [ ] Cuối kỳ: Có đầy đủ data — không có ý nghĩa dự báo

> **Khuyến nghị**: Prediction point = sau giữa kỳ (sau khi có `diem_gk`). Phải loại bỏ bất kỳ feature nào chỉ có được sau thời điểm predict.

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
