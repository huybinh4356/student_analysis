"""
Analysis & ML Model Evaluation Widget.
Provides clear, non-technical evaluation metrics and model selection rationale.
Phases 22 implementation:
- Non-blocking ML training via QThread (UI-01).
- Instant loading of cached evaluation results from ModelRegistry on startup.
- Full 5-Fold CV evaluation across Regression and Classification models.
"""

from pathlib import Path
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.core.data_loader import DataLoader
from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor
from src.core.model_trainer import ModelTrainer
from src.core.model_registry import ModelRegistry


class TrainingWorker(QThread):
    """Background worker for non-blocking ML training pipeline."""
    finished = pyqtSignal(pd.DataFrame, pd.DataFrame)
    error = pyqtSignal(str)

    def run(self):
        try:
            df = DataLoader.load_data()
            if df.empty:
                self.error.emit("Dữ liệu rỗng. Vui lòng nạp file Excel hoặc database trước.")
                return

            fe_df = FeatureEngineer.create_features(df)
            preprocessor = DataPreprocessor(test_size=0.2, random_state=42)

            X, y_reg, y_cls = preprocessor.prepare_features(fe_df)
            splits = preprocessor.split_data(X, y_reg, y_cls)

            models_dir = Path(__file__).resolve().parents[2] / "models"
            trainer = ModelTrainer(models_dir=models_dir)

            reg_summary, _ = trainer.train_evaluate_regression(
                splits["X_train"], splits["X_test"], splits["y_reg_train"], splits["y_reg_test"], cv_folds=5
            )
            cls_summary, _ = trainer.train_evaluate_classification(
                splits["X_train"], splits["X_test"], splits["y_cls_train"], splits["y_cls_test"], cv_folds=5
            )

            self.finished.emit(reg_summary, cls_summary)
        except Exception as e:
            self.error.emit(str(e))


class AnalysisWidget(QWidget):
    """Widget for training and evaluating Regression and Classification models."""

    def __init__(self):
        super().__init__()
        self.worker: TrainingWorker = None
        self.init_ui()
        self.load_initial_results()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        header_text = QVBoxLayout()

        title = QLabel("Trung tâm Dự báo & Huấn luyện Mô hình Machine Learning")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("So sánh đối chiếu hiệu năng 6 thuật toán Hồi quy điểm số và 6 thuật toán Phân loại rủi ro (5-Fold CV).")
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

        # Status / Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border-radius: 4px; height: 6px; }")
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Trạng thái: Sẵn sàng.")
        self.lbl_status.setStyleSheet("color: #48cae4; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.lbl_status)

        # Model Selection & Metrics Explanation Card
        expl_card = QFrame()
        expl_card.setObjectName("card")
        expl_layout = QVBoxLayout(expl_card)

        expl_title = QLabel("Nguyên tắc Lựa chọn Mô hình (Zero Data Leakage & CV Selection):")
        expl_title.setStyleSheet("font-weight: bold; color: #48cae4; font-size: 13px;")
        expl_layout.addWidget(expl_title)

        expl_content = QLabel(
            "• <b>Quy tắc Không Rò rỉ Dữ liệu (Zero Leakage)</b>: Toàn bộ quá trình chuẩn hóa (StandardScaler) và mã hóa (OneHotEncoder) được thực hiện bên trong sklearn Pipeline cho từng Fold chéo.<br>"
            "• <b>Lựa chọn bằng Cross-Validation</b>: Mô hình tốt nhất được chọn hoàn toàn dựa trên điểm <b>5-Fold CV trên tập Train</b>, tập Test chỉ được dùng 1 lần duy nhất để kiểm định độc lập.<br>"
            "• <b>Độ phức tạp (Parsimony)</b>: Ưu tiên mô hình tuyến tính đơn giản giải thích được nếu chênh lệch R² so với mô hình phức tạp dưới 0.02."
        )
        expl_content.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        expl_layout.addWidget(expl_content)
        layout.addWidget(expl_card)

        # Tables Section
        lbl_reg = QLabel("1. Kết quả So sánh Thuật toán Hồi quy Điểm số (Regression Candidates):")
        lbl_reg.setStyleSheet("font-weight: bold; color: #48cae4; font-size: 14px; margin-top: 6px;")
        layout.addWidget(lbl_reg)

        self.table_reg = QTableWidget()
        self.table_reg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_reg)

        lbl_cls = QLabel("2. Kết quả So sánh Thuật toán Phân loại Rủi ro (Classification Candidates):")
        lbl_cls.setStyleSheet("font-weight: bold; color: #5bc0be; font-size: 14px; margin-top: 6px;")
        layout.addWidget(lbl_cls)

        self.table_cls = QTableWidget()
        self.table_cls.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_cls)

    def load_initial_results(self):
        """Loads cached model evaluation metadata from registry without freezing UI."""
        models_dir = Path(__file__).resolve().parents[2] / "models"
        registry = ModelRegistry(models_dir)
        data = registry.get_registry_data()
        if not data:
            self.lbl_status.setText("Chưa có kết quả huấn luyện. Bấm 'Huấn luyện Lại Mô hình' để bắt đầu.")
            return

        reg = data.get("regression", {})
        cls_ = data.get("classification", {})

        if reg:
            df_reg = pd.DataFrame([{
                "Model": reg.get("model_name"),
                "CV R² (mean)": reg.get("cv_metrics", {}).get("cv_r2_mean"),
                "CV R² (std)": reg.get("cv_metrics", {}).get("cv_r2_std"),
                "CV MAE": reg.get("cv_metrics", {}).get("cv_mae"),
                "Test R²": reg.get("test_metrics", {}).get("r2"),
                "Test RMSE": reg.get("test_metrics", {}).get("rmse"),
                "Test MAE": reg.get("test_metrics", {}).get("mae"),
                "Selected": "[Best]",
            }])
            self._populate_table(self.table_reg, df_reg)

        if cls_:
            df_cls = pd.DataFrame([{
                "Model": cls_.get("model_name"),
                "CV Macro F1 (mean)": cls_.get("cv_metrics", {}).get("cv_f1_macro_mean"),
                "CV Macro F1 (std)": cls_.get("cv_metrics", {}).get("cv_f1_macro_std"),
                "CV Accuracy": cls_.get("cv_metrics", {}).get("cv_accuracy"),
                "Test Accuracy": cls_.get("test_metrics", {}).get("accuracy"),
                "Test F1-Macro": cls_.get("test_metrics", {}).get("f1_macro"),
                "Recall High-Risk": cls_.get("test_metrics", {}).get("recall_high_risk"),
                "Selected": "[Best]",
            }])
            self._populate_table(self.table_cls, df_cls)

        self.lbl_status.setText("Đã tải thông tin mô hình hiện hành từ Model Registry.")

    def train_all_models(self):
        """Spawns non-blocking training worker."""
        if self.worker is not None and self.worker.isRunning():
            return

        self.btn_train.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Đang huấn luyện mô hình trên luồng nền (QThread)... Vui lòng đợi.")

        self.worker = TrainingWorker()
        self.worker.finished.connect(self.on_training_finished)
        self.worker.error.connect(self.on_training_error)
        self.worker.start()

    def on_training_finished(self, reg_summary: pd.DataFrame, cls_summary: pd.DataFrame):
        self._populate_table(self.table_reg, reg_summary)
        self._populate_table(self.table_cls, cls_summary)

        self.btn_train.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Huấn luyện hoàn tất! Các mô hình tốt nhất đã được cập nhật vào Model Registry.")
        QMessageBox.information(self, "Thành công", "Huấn luyện và đánh giá mô hình hoàn tất thành công!")

    def on_training_error(self, err_msg: str):
        self.btn_train.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"Lỗi: {err_msg}")
        QMessageBox.critical(self, "Lỗi Huấn luyện", f"Không thể huấn luyện mô hình: {err_msg}")

    def _populate_table(self, table: QTableWidget, df: pd.DataFrame):
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(list(df.columns))

        for i in range(len(df)):
            for j in range(len(df.columns)):
                val = str(df.iloc[i, j])
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, j, item)
