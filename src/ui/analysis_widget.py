"""
Analysis & ML Model Evaluation Widget.
Provides clear, non-technical evaluation metrics and model selection rationale.
Clean corporate styling without emojis.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt

from src.core.data_loader import DataLoader
from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor
from src.core.model_trainer import ModelTrainer


class AnalysisWidget(QWidget):
    """Widget for training and evaluating 5 Regression and 5 Classification models."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        header_text = QVBoxLayout()

        title = QLabel("Trung tâm Dự báo & Huấn luyện Mô hình Machine Learning")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("So sánh đối chiếu hiệu năng 5 thuật toán Hồi quy điểm số và 5 thuật toán Phân loại rủi ro.")
        subtitle.setObjectName("sectionSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        self.btn_train = QPushButton("Huấn luyện Lại Mô hình")
        self.btn_train.setObjectName("primary-btn")
        self.btn_train.clicked.connect(self.train_all_models)
        header.addWidget(self.btn_train)

        layout.addLayout(header)

        # Model Selection & Metrics Explanation Card
        expl_card = QFrame()
        expl_card.setObjectName("card")
        expl_layout = QVBoxLayout(expl_card)

        expl_title = QLabel("Giải thích Chỉ số Đánh giá cho Người dùng:")
        expl_title.setStyleSheet("font-weight: bold; color: #48cae4; font-size: 13px;")
        expl_layout.addWidget(expl_title)

        expl_content = QLabel(
            "• Độ chính xác dự báo (Test R² / Accuracy): Tỷ lệ % mô hình đoán đúng trên dữ liệu kiểm thử thực tế.\n"
            "• Độ lệch điểm số (RMSE / MAE): Khoảng chênh lệch trung bình giữa điểm số dự báo và điểm số thực tế (Ví dụ: ±0.27 điểm).\n"
            "• Kiểm tra Chéo (5-Fold CV): Kiểm tra độ ổn định của mô hình trên 5 tập dữ liệu độc lập để đảm bảo không bị học vẹt (Overfitting)."
        )
        expl_content.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        expl_layout.addWidget(expl_content)

        layout.addWidget(expl_card)

        # Table 1: Regression Models (Grade Prediction)
        lbl_reg = QLabel("1. Kết quả Thuật toán Hồi quy Điểm số (Regression Model Comparison):")
        lbl_reg.setStyleSheet("font-weight: bold; color: #48cae4; font-size: 14px; margin-top: 8px;")
        layout.addWidget(lbl_reg)

        self.table_reg = QTableWidget()
        self.table_reg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_reg)

        # Table 2: Classification Models (Risk Category Prediction)
        lbl_cls = QLabel("2. Kết quả Thuật toán Phân loại Rủi ro (Classification Model Comparison):")
        lbl_cls.setStyleSheet("font-weight: bold; color: #5bc0be; font-size: 14px; margin-top: 8px;")
        layout.addWidget(lbl_cls)

        self.table_cls = QTableWidget()
        self.table_cls.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_cls)

        self.train_all_models()

    def train_all_models(self):
        """Runs the complete ML training pipeline and populates evaluation tables."""
        try:
            df = DataLoader.load_from_db()
            if df.empty:
                QMessageBox.warning(self, "Cảnh báo", "Database rỗng. Vui lòng nạp dữ liệu trước.")
                return

            fe_df = FeatureEngineer.create_features(df)
            preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

            X, y_reg, y_cls = preprocessor.prepare_features(fe_df)
            splits = preprocessor.split_data(X, y_reg, y_cls)
            X_tr, X_te, feature_names = preprocessor.encode_and_scale(splits["X_train"], splits["X_test"])

            models_dir = Path(__file__).resolve().parents[2] / "models"
            trainer = ModelTrainer(models_dir=models_dir)

            reg_summary = trainer.train_evaluate_regression(X_tr, X_te, splits["y_reg_train"], splits["y_reg_test"])
            cls_summary = trainer.train_evaluate_classification(X_tr, X_te, splits["y_cls_train"], splits["y_cls_test"])

            self._populate_table(self.table_reg, reg_summary)
            self._populate_table(self.table_cls, cls_summary)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi Huấn luyện", f"Không thể huấn luyện mô hình: {str(e)}")

    def _populate_table(self, table: QTableWidget, df):
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j in range(len(df.columns)):
                val = str(df.iloc[i, j])
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, j, item)
