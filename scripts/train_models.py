"""
End-to-End Model Training Pipeline Script.
Executes data preprocessing, feature engineering, cross-validation model selection,
and persists artifacts via ModelRegistry.
"""

from __future__ import annotations
import sys
import io
from pathlib import Path
import json
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
from src.core.model_registry import ModelRegistry


def run_pipeline():
    print("==================================================================")
    print("   HỆ THỐNG PHÂN TÍCH KẾT QUẢ HỌC TẬP — ML TRAINING PIPELINE v3   ")
    print("==================================================================\n")

    # 1. Load Data
    print("1. Đọc dữ liệu (PostgreSQL / Excel fallback)...")
    raw_df = DataLoader.load_data()
    if raw_df.empty:
        raise RuntimeError("Không thể tải dữ liệu sinh viên từ DB hoặc file Excel!")
    print(f"   -> Đã tải thành công {len(raw_df)} dòng dữ liệu.")

    # 2. Feature Engineering (without leakage)
    print("2. Tạo biến tương tác & chỉ số tổng hợp (Feature Engineering)...")
    fe_df = FeatureEngineer.create_features(raw_df)
    print(f"   -> Tổng số cột sau feature engineering: {len(fe_df.columns)} cột.")

    # 3. Train / Test Split
    print("3. Phân chia Train/Test (80/20) TRƯỚC khi fit Transformer (Zero Data Leakage)...")
    preprocessor = DataPreprocessor(test_size=0.2, random_state=42)
    X, y_reg, y_cls = preprocessor.prepare_features(fe_df)
    splits = preprocessor.split_data(X, y_reg, y_cls)
    print(f"   -> Train set: {len(splits['X_train'])} dòng, Test set: {len(splits['X_test'])} dòng.")
    print(f"   -> Số features đầu vào X: {len(splits['X_train'].columns)} features.\n")

    models_dir = root_path / "models"
    trainer = ModelTrainer(models_dir=models_dir)

    # 4. Train & Compare Regression Candidates
    print("4. HUẤN LUYỆN & SO SÁNH CÁC MÔ HÌNH DỰ ĐOÁN ĐIỂM (REGRESSION):")
    print("   (Đánh giá bằng 5-Fold Cross Validation trên tập Train, chọn model tốt nhất)")
    reg_summary, best_reg = trainer.train_evaluate_regression(
        splits["X_train"],
        splits["X_test"],
        splits["y_reg_train"],
        splits["y_reg_test"],
        cv_folds=5,
    )
    print(reg_summary.to_string(index=False))
    print(f"\n   ★ Model được chọn: {best_reg['model_name']}")
    print(f"     Lý do: {best_reg['selection_reason']}")
    print(f"     CV R²: {best_reg['cv_metrics']['cv_r2_mean']:.4f} ± {best_reg['cv_metrics']['cv_r2_std']:.4f}, CV MAE: {best_reg['cv_metrics']['cv_mae']:.4f}")
    print(f"     Test R²: {best_reg['test_metrics']['r2']:.4f}, Test RMSE: {best_reg['test_metrics']['rmse']:.4f}, Test MAE: {best_reg['test_metrics']['mae']:.4f}\n")

    # 5. Train & Compare Classification Candidates
    print("5. HUẤN LUYỆN & SO SÁNH CÁC MÔ HÌNH DỰ BÁO NGUY CƠ HỌC VỤ (CLASSIFICATION):")
    print("   (Đánh giá bằng 5-Fold Stratified CV trên tập Train theo Macro F1)")
    cls_summary, best_cls = trainer.train_evaluate_classification(
        splits["X_train"],
        splits["X_test"],
        splits["y_cls_train"],
        splits["y_cls_test"],
        cv_folds=5,
    )
    print(cls_summary.to_string(index=False))
    print(f"\n   ★ Model được chọn: {best_cls['model_name']}")
    print(f"     Lý do: {best_cls['selection_reason']}")
    print(f"     CV Macro F1: {best_cls['cv_metrics']['cv_f1_macro_mean']:.4f} ± {best_cls['cv_metrics']['cv_f1_macro_std']:.4f}")
    print(f"     Test Acc: {best_cls['test_metrics']['accuracy']:.4f}, Test Macro F1: {best_cls['test_metrics']['f1_macro']:.4f}, Recall High-Risk: {best_cls['test_metrics']['recall_high_risk']:.4f}\n")

    # 6. Update Baseline Metrics file
    metrics_file = root_path / "docs" / "baseline" / "current_metrics.json"
    updated_metrics = {
        "regression": {
            "model_name": best_reg["model_name"],
            "cv_r2": best_reg["cv_metrics"]["cv_r2_mean"],
            "r2": best_reg["test_metrics"]["r2"],
            "mae": best_reg["test_metrics"]["mae"],
            "rmse": best_reg["test_metrics"]["rmse"],
        },
        "classification": {
            "model_name": best_cls["model_name"],
            "cv_f1_macro": best_cls["cv_metrics"]["cv_f1_macro_mean"],
            "accuracy": best_cls["test_metrics"]["accuracy"],
            "f1_macro": best_cls["test_metrics"]["f1_macro"],
            "f1_weighted": best_cls["test_metrics"]["f1_weighted"],
            "recall_high_risk": best_cls["test_metrics"]["recall_high_risk"],
        },
    }
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(updated_metrics, f, indent=2)
    print(f"6. Đã cập nhật metrics thực tế vào: {metrics_file}")
    print("==================================================================")
    print("   HUẤN LUYỆN HOÀN TẤT THÀNH CÔNG VỚI ZERO LEAKAGE PIPELINES!      ")
    print("==================================================================")


if __name__ == "__main__":
    run_pipeline()
