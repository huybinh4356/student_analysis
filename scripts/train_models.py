"""
End-to-End Model Training Pipeline Script.
Executes data preprocessing, feature engineering, model training, evaluation, and persistence.
"""

import sys
import io
from pathlib import Path
import joblib
import pandas as pd

# Ensure root path is in sys.path
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Ensure UTF-8 printing
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.core.data_loader import DataLoader
from src.core.feature_engineer import FeatureEngineer
from src.core.preprocessor import DataPreprocessor
from src.core.model_trainer import ModelTrainer


def run_pipeline():
    print("==================================================================")
    print("   HỆ THỐNG PHÂN TÍCH KẾT QUẢ HỌC TẬP — ML TRAINING PIPELINE      ")
    print("==================================================================\n")

    # 1. Load Data
    print("1. Đọc dữ liệu từ PostgreSQL...")
    raw_df = DataLoader.load_from_db()
    print(f"   -> Đã đọc {len(raw_df)} sinh viên thành công.")

    # 2. Feature Engineering
    print("2. Tạo biến tương tác & chỉ số tổng hợp (Feature Engineering)...")
    fe_df = FeatureEngineer.create_features(raw_df)
    print(f"   -> Đã bổ sung 5 biến mới: lms_gio_per_video, academic_engagement_index, stress_motivation_ratio, composite_exam_score, low_engagement_flag.")

    # 3. Train / Test Split (R-DATA-04)
    print("3. Chia Tập Dữ liệu Train/Test (80/20) TRƯỚC khi fit Scaler/Encoder...")
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    X, y_reg, y_cls = preprocessor.prepare_features(fe_df)
    splits = preprocessor.split_data(X, y_reg, y_cls)

    # 4. Fit Encoders & Scalers ONLY on Train
    print("4. Encoding & Scaling (Fit CHỈ trên tập Train)...")
    X_train_transformed, X_test_transformed, feature_names = preprocessor.encode_and_scale(
        splits["X_train"], splits["X_test"]
    )
    print(f"   -> Tổng số tính năng sau biến đổi: {len(feature_names)} features.\n")

    models_dir = root_path / "models"
    trainer = ModelTrainer(models_dir=models_dir)

    # 5. Train Regression Models
    print("5. KẾT QUẢ HUẤN LUYỆN DỰ ĐOÁN ĐIỂM TỔNG KẾT (REGRESSION - DIEMTONGKET):")
    reg_summary = trainer.train_evaluate_regression(
        X_train_transformed,
        X_test_transformed,
        splits["y_reg_train"],
        splits["y_reg_test"],
    )
    print(reg_summary.to_string(index=False))
    print("\n")

    # 6. Train Classification Models
    print("6. KẾT QUẢ HUẤN LUYỆN DỰ BÁO RỦI RO HỌC VỤ (CLASSIFICATION - NGUY CƠ HỌC VỤ):")
    cls_summary = trainer.train_evaluate_classification(
        X_train_transformed,
        X_test_transformed,
        splits["y_cls_train"],
        splits["y_cls_test"],
    )
    print(cls_summary.to_string(index=False))
    print("\n")

    # 7. Persist Scaler & Feature Names (R-MODEL-07)
    print("7. Lưu trữ Model, Scaler & Feature Names (joblib)...")
    joblib.dump(preprocessor, models_dir / "preprocessor.pkl")
    joblib.dump(feature_names, models_dir / "feature_names.pkl")
    print(f"   -> Đã lưu các artifact thành công vào thư mục: {models_dir}\n")
    print("==================================================================")


if __name__ == "__main__":
    run_pipeline()
