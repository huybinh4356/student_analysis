"""
Preprocessor module for data splitting, encoding, scaling, and transformation.
Strictly enforces Rule R-DATA-04 (fit encoders/scalers ONLY on train set).
"""

from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from src.core.schema_detector import SchemaDetector


class DataPreprocessor:
    """Handles train/test splitting, categorical encoding, missing imputation, and numerical scaling."""

    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.nominal_cols = SchemaDetector.NOMINAL_COLS
        self.ordinal_mappings = SchemaDetector.ORDINAL_MAPPINGS
        self.numeric_cols = SchemaDetector.NUMERIC_COLS
        self.encoded_feature_names: List[str] = []

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Extracts features (X), regression target (y_reg), and classification target (y_cls).

        Args:
            df: Raw or feature-engineered DataFrame.

        Returns:
            Tuple[pd.DataFrame, pd.Series, pd.Series]: (X, y_reg, y_cls)
        """
        # Exclude ID and target columns from X
        exclude_cols = SchemaDetector.ID_COLS + SchemaDetector.TEXT_COLS + [
            SchemaDetector.TARGET_REGRESSION,
            SchemaDetector.TARGET_CLASSIFICATION,
        ]
        feature_cols = [c for c in df.columns if c not in exclude_cols]

        X = df[feature_cols].copy()
        
        y_reg = df[SchemaDetector.TARGET_REGRESSION].copy()
        if y_reg.isna().any():
            y_reg = y_reg.fillna(y_reg.median() if not y_reg.empty else 5.0)

        # Ordinal encode classification target (1: Rất thấp, 2: Thấp, 3: Trung bình, 4: Cao)
        y_cls = df[SchemaDetector.TARGET_CLASSIFICATION].map(
            self.ordinal_mappings["nguy_co_hoc_vu"]
        ).copy()
        if y_cls.isna().any():
            y_cls = y_cls.fillna(2)

        return X, y_reg, y_cls

    def split_data(
        self, X: pd.DataFrame, y_reg: pd.Series, y_cls: pd.Series
    ) -> Dict[str, Any]:
        """
        Splits data into train and test sets BEFORE any fitting (R-DATA-04).

        Args:
            X: Feature matrix.
            y_reg: Continuous target.
            y_cls: Categorical target.

        Returns:
            Dict[str, Any]: Dictionary containing train and test splits.
        """
        (
            X_train,
            X_test,
            y_reg_train,
            y_reg_test,
            y_cls_train,
            y_cls_test,
        ) = train_test_split(
            X,
            y_reg,
            y_cls,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y_cls,  # Maintain target class balance
        )

        return {
            "X_train": X_train,
            "X_test": X_test,
            "y_reg_train": y_reg_train,
            "y_reg_test": y_reg_test,
            "y_cls_train": y_cls_train,
            "y_cls_test": y_cls_test,
        }

    def encode_and_scale(
        self, X_train: pd.DataFrame, X_test: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Encodes categorical features, imputes missing values, and scales numerical features.
        Fits transformer ONLY on X_train (R-DATA-04).

        Args:
            X_train: Training features.
            X_test: Testing features.

        Returns:
            Tuple[np.ndarray, np.ndarray, List[str]]: Transformed train array, test array, feature names.
        """
        # Encode Ordinal variables directly
        X_tr = X_train.copy()
        X_te = X_test.copy()

        for col, mapping in self.ordinal_mappings.items():
            if col in X_tr.columns:
                X_tr[col] = X_tr[col].map(mapping).fillna(2)
                X_te[col] = X_te[col].map(mapping).fillna(2)

        # Identify numerical and nominal columns present
        num_cols = [c for c in X_tr.columns if c not in self.nominal_cols]
        nom_cols = [c for c in X_tr.columns if c in self.nominal_cols]

        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        nom_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("nom", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")),
        ])

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, num_cols),
                ("nom", nom_pipeline, nom_cols),
            ]
        )

        # Fit ONLY on train (R-DATA-04)
        X_train_transformed = self.column_transformer.fit_transform(X_tr)
        X_test_transformed = self.column_transformer.transform(X_te)

        # Extract generated feature names
        nom_encoder = self.column_transformer.named_transformers_["nom"].named_steps["nom"]
        nom_feature_names = nom_encoder.get_feature_names_out(nom_cols).tolist() if nom_cols else []
        self.encoded_feature_names = num_cols + nom_feature_names

        return X_train_transformed, X_test_transformed, self.encoded_feature_names

        return X_train_transformed, X_test_transformed, self.encoded_feature_names

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms input features using already fitted ColumnTransformer.

        Args:
            X: Input feature DataFrame.

        Returns:
            np.ndarray: Transformed features array.
        """
        X_tr = X.copy()
        for col, mapping in self.ordinal_mappings.items():
            if col in X_tr.columns:
                X_tr[col] = X_tr[col].map(mapping).fillna(2)

        return self.column_transformer.transform(X_tr)

