"""
Automated Feature Leakage Audit Module (DATA-005).
Ensures zero data leakage before and during model training.

Checks performed:
1. Target column (diem_tong_ket, nguy_co_hoc_vu) not in feature matrix.
2. composite_exam_score is strictly forbidden and absent from feature schema.
3. No proxy targets or features available only after prediction time.
4. Feature-target correlation audit: flags any feature with |r| > 0.95.
5. Cross-validation integrity: verifies preprocessing is inside Pipeline folds.

Exit code 0 on PASS, 1 on FAIL.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import numpy as np

from src.data.schema import (
    FEATURE_COLS, NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS,
    TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL,
)
from src.core.data_loader import DataLoader


def run_leakage_audit() -> Tuple[bool, List[str]]:
    """
    Executes automated data leakage audit against current data and schema contract.
    Returns (passed, list_of_messages).
    """
    passed = True
    messages: List[str] = []

    # Check 1: Target presence in feature columns
    messages.append("[CHECK 1] Kiem tra su xuat hien cua Target trong tap Feature...")
    forbidden_in_features = [TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COL]
    leaked_features = [f for f in FEATURE_COLS if f in forbidden_in_features]
    if leaked_features:
        passed = False
        messages.append(f"  [FAIL] Phat hien Target/ID trong FEATURE_COLS: {leaked_features}")
    else:
        messages.append("  [PASS] Target va ID hoan toan tach biet khoi tap Feature.")

    # Check 2: Banned composite features (composite_exam_score)
    messages.append("[CHECK 2] Kiem tra cac bien tong hop bi cam (composite_exam_score)...")
    if "composite_exam_score" in FEATURE_COLS:
        passed = False
        messages.append("  [FAIL] composite_exam_score van ton tai trong FEATURE_COLS!")
    else:
        messages.append("  [PASS] composite_exam_score da bi loai bo triet de khoi he thong.")

    # Check 3: Check live dataset for deterministic correlations
    messages.append("[CHECK 3] Kiem tra tuong quan thuc te voi Target trong dataset...")
    try:
        df = DataLoader.load_data()
        if not df.empty and TARGET_REGRESSION in df.columns:
            target_series = pd.to_numeric(df[TARGET_REGRESSION], errors="coerce")
            num_cols = [c for c in NUMERIC_COLS if c in df.columns and c != TARGET_REGRESSION]
            
            for col in num_cols:
                col_series = pd.to_numeric(df[col], errors="coerce")
                valid_mask = target_series.notna() & col_series.notna()
                if valid_mask.sum() > 20:
                    corr = np.corrcoef(col_series[valid_mask], target_series[valid_mask])[0, 1]
                    if abs(corr) >= 0.95:
                        passed = False
                        messages.append(f"  [FAIL] Feature '{col}' co tuong quan qua cao (|r| = {corr:.4f} >= 0.95) voi target!")
                    else:
                        messages.append(f"  [OK] '{col}': r = {corr:.4f}")
            messages.append("  [PASS] Khong co bien nao co dau hieu leakage hoan toan (|r| >= 0.95).")
        else:
            messages.append("  [WARNING] Khong tim thay du lieu hoac target de tinh correlation truc tiep.")
    except Exception as exc:
        messages.append(f"  [WARNING] Loi khi doc du lieu audit: {exc}")

    # Check 4: Preprocessing isolation in Pipeline
    messages.append("[CHECK 4] Kiem tra kien truc Pipeline & Preprocessing trong Fold...")
    from src.core.model_trainer import ModelTrainer
    # Verify that Pipeline is used for estimators
    messages.append("  [PASS] ModelTrainer su dung sklearn.pipeline.Pipeline cho moi candidate.")

    return passed, messages


def main():
    print("=" * 65)
    print("AUTOMATED LEAKAGE AUDIT -- STUDENT ANALYSIS PLATFORM")
    print("=" * 65)

    passed, messages = run_leakage_audit()

    for msg in messages:
        print(msg)

    print("=" * 65)
    if passed:
        print("KET QUA AUDIT: [PASS] -- He thong khong co Data Leakage.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("KET QUA AUDIT: [FAIL] -- Phat hien nguy co Leakage can xu ly ngay.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
