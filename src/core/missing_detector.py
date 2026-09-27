"""
Missing data detection and confidence scoring module for student records.
Enforces rules R-MISS-01 through R-MISS-08 and ethical compliance R-ETH-01.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class MissingField:
    column: str
    display_name: str
    severity: str  # 'critical' | 'warning' | 'info'
    reason: str
    impact_score: float  # 0.0 to 1.0
    suggestion: str


class MissingDetector:
    """
    Detects missing or abnormal data fields for individual student records
    and calculates prediction confidence penalties based on data completeness.
    """

    # Field rule definitions with severity and suggestions
    FIELD_RULES = {
        "diem_gk": {
            "display_name": "Điểm Giữa Kỳ",
            "severity": "critical",
            "impact_score": 0.35,
            "threshold_min": 0.0,
            "threshold_max": 10.0,
            "reason": "Thiếu dữ liệu điểm thi giữa kỳ - thành phần bắt buộc (40% điểm môn).",
            "suggestion": "Cần thu thập điểm thi giữa kỳ để dự đoán chính xác kết quả môn học.",
        },
        "diem_quiz": {
            "display_name": "Điểm Quiz/Trắc Nghiệm",
            "severity": "critical",
            "impact_score": 0.25,
            "threshold_min": 0.0,
            "threshold_max": 10.0,
            "reason": "Chưa có dữ liệu bài kiểm tra nhanh (30% trọng số đánh giá).",
            "suggestion": "Tổ chức làm bù bài Quiz hoặc cập nhật điểm từ LMS.",
        },
        "diem_bai_tap": {
            "display_name": "Điểm Bài Tập Thực Hành",
            "severity": "critical",
            "impact_score": 0.25,
            "threshold_min": 0.0,
            "threshold_max": 10.0,
            "reason": "Thiếu điểm bài tập thực hành/đồ án.",
            "suggestion": "Nhắc nhở nộp bài tập và chấm điểm bổ sung.",
        },
        "chuyen_can": {
            "display_name": "Tỷ Lệ Chuyên Cần",
            "severity": "warning",
            "impact_score": 0.15,
            "threshold_min": 30.0,
            "threshold_max": 100.0,
            "reason": "Chuyên cần dưới ngưỡng an toàn (30%). Có nguy cơ không đủ điều kiện thi.",
            "suggestion": "Gặp mặt sinh viên tư vấn lý do vắng mặt và cảnh báo quy chế.",
        },
        "nop_bai_dung_han": {
            "display_name": "Tỷ Lệ Nộp Bài Đúng Hạn",
            "severity": "warning",
            "impact_score": 0.12,
            "threshold_min": 40.0,
            "threshold_max": 100.0,
            "reason": "Tỷ lệ nộp bài đúng hạn quá thấp (< 40%). Thể hiện kỷ luật kém.",
            "suggestion": "Thiết lập thông báo nhắc hạn nộp trên hệ thống LMS.",
        },
        "diem_thpt": {
            "display_name": "Điểm Đầu Vào THPT",
            "severity": "warning",
            "impact_score": 0.10,
            "threshold_min": 0.0,
            "threshold_max": 30.0,
            "reason": "Thiếu thông tin điểm xét tuyển đầu vào.",
            "suggestion": "Cập nhật hồ sơ tuyển sinh từ phòng đào tạo.",
        },
        "lms_gio_truy_cap": {
            "display_name": "Giờ Truy Cập LMS",
            "severity": "info",
            "impact_score": 0.05,
            "threshold_min": 5.0,
            "threshold_max": 500.0,
            "reason": "Thời lượng tương tác hệ thống LMS thấp (< 5 giờ).",
            "suggestion": "Khuyến khích sinh viên xem bài giảng và tài liệu trực tuyến.",
        },
        "lms_xem_video": {
            "display_name": "Thời Lượng Xem Video",
            "severity": "info",
            "impact_score": 0.05,
            "threshold_min": 2.0,
            "threshold_max": 200.0,
            "reason": "Thời lượng xem video bài giảng dưới 2 giờ.",
            "suggestion": "Gửi thông báo nhắc nhở sinh viên xem lại video bài giảng.",
        },
        "muc_do_stress": {
            "display_name": "Mức Độ Stress",
            "severity": "info",
            "impact_score": 0.05,
            "threshold_min": 1.0,
            "threshold_max": 4.0,
            "reason": "Chỉ số tâm lý ghi nhận stress ở mức cao (> 4).",
            "suggestion": "Giới thiệu sinh viên đến bộ phận tư vấn tâm lý trường.",
        },
    }

    def detect_for_student(self, student: Dict[str, Any]) -> List[MissingField]:
        """
        Detects missing or abnormal fields for a single student.

        Args:
            student: Dictionary containing student attributes.

        Returns:
            List[MissingField]: List of identified issues categorized by severity.
        """
        detected: List[MissingField] = []

        for field_key, rule in self.FIELD_RULES.items():
            val = student.get(field_key)

            # Check missing / NaN / null
            is_missing = val is None or (isinstance(val, float) and (val != val or str(val) == "nan"))
            
            if is_missing:
                detected.append(
                    MissingField(
                        column=field_key,
                        display_name=rule["display_name"],
                        severity=rule["severity"],
                        reason=f"{rule['display_name']}: Chưa ghi nhận dữ liệu.",
                        impact_score=rule["impact_score"],
                        suggestion=rule["suggestion"],
                    )
                )
            else:
                # Check abnormal / out of range values
                try:
                    num_val = float(val)
                    t_min = rule.get("threshold_min")
                    t_max = rule.get("threshold_max")
                    
                    if t_min is not None and num_val < t_min:
                        detected.append(
                            MissingField(
                                column=field_key,
                                display_name=rule["display_name"],
                                severity=rule["severity"],
                                reason=f"{rule['display_name']} ({num_val}) thấp hơn ngưỡng khuyến nghị ({t_min}).",
                                impact_score=rule["impact_score"],
                                suggestion=rule["suggestion"],
                            )
                        )
                    elif t_max is not None and num_val > t_max:
                        detected.append(
                            MissingField(
                                column=field_key,
                                display_name=rule["display_name"],
                                severity=rule["severity"],
                                reason=f"{rule['display_name']} ({num_val}) vượt quá khoảng hợp lệ ({t_max}).",
                                impact_score=rule["impact_score"],
                                suggestion="Kiểm tra lại tính chính xác của dữ liệu đầu vào.",
                            )
                        )
                except (ValueError, TypeError):
                    pass

        # Sort detected issues by severity: critical -> warning -> info
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        detected.sort(key=lambda x: severity_order.get(x.severity, 3))
        return detected

    def calculate_confidence_penalty(self, missing_fields: List[MissingField]) -> float:
        """
        Calculates prediction confidence score (0-100%) taking penalties into account.
        R-MISS-05: Confidence = Base (100%) - Penalty (min bound 30%).

        Args:
            missing_fields: List of detected missing/abnormal fields.

        Returns:
            float: Adjusted confidence percentage (30.0 to 100.0).
        """
        penalty = 0.0
        for item in missing_fields:
            if item.severity == "critical":
                penalty += 15.0
            elif item.severity == "warning":
                penalty += 8.0
            elif item.severity == "info":
                penalty += 3.0

        confidence = max(30.0, 100.0 - penalty)
        return round(confidence, 1)
