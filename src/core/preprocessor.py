"""
Preprocessor module for data splitting, encoding, scaling, and transformation.
Phase 4 & 5 implementation: provides modular ColumnTransformer and Pipeline integration,
strictly preventing data leakage during training and cross-validation (R-DATA-04).
"""

from __future__ import annotations
from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from src.data.schema import (
    NUMERIC_COLS, ORDINAL_COLS, NOMINAL_COLS, ORDINAL_MAPPINGS,
    TARGET_REGRESSION, TARGET_CLASSIFICATION, ID_COLS, TEXT_COLS,
    LEAKAGE_BANNED_FEATURES,
)


class OrdinalMapper(BaseEstimator, TransformerMixin):
    """
    Transforms categorical text columns into ordinal numbers based on domain mappings.
    Handles unseen categories by falling back to a median default (e.g. 2).
    """

    def __init__(self, mappings: Optional[Dict[str, Dict[str, int]]] = None, default_val: float = 2.0):
        self.mappings = mappings or ORDINAL_MAPPINGS
        self.default_val = default_val

    def fit(self, X: Any, y: Any = None) -> OrdinalMapper:
        return self

    def transform(self, X: Any) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            df = X.copy()
        else:
            df = pd.DataFrame(X)

        for col, mapping in self.mappings.items():
            if col in df.columns:
                df[col] = df[col].map(mapping).fillna(self.default_val)

        return df.values.astype(float)

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> np.ndarray:
        if input_features is not None:
            return np.array(input_features)
        return np.array([f"ordinal_{i}" for i in range(len(self.mappings))])


def build_column_preprocessor(feature_columns: List[str]) -> ColumnTransformer:
    """
    Factory creating a robust scikit-learn ColumnTransformer for arbitrary student feature subsets.

    Args:
        feature_columns: Names of feature columns present in the input DataFrame.

    Returns:
        ColumnTransformer ready to be embedded into an end-to-end Pipeline.
    """
    ord_names = [col.name for col in ORDINAL_COLS]
    nom_names = [col.name for col in NOMINAL_COLS]

    numeric_cols = [
        c for c in feature_columns
        if c not in ord_names and c not in nom_names and c not in LEAKAGE_BANNED_FEATURES
    ]
    ordinal_cols = [c for c in feature_columns if c in ord_names]
    nominal_cols = [c for c in feature_columns if c in nom_names]

    transformers = []

    if numeric_cols:
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("num", num_pipeline, numeric_cols))

    if ordinal_cols:
        ord_pipeline = Pipeline([
            ("mapper", OrdinalMapper(mappings=ORDINAL_MAPPINGS, default_val=2.0)),
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("ord", ord_pipeline, ordinal_cols))

    if nominal_cols:
        nom_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")),
        ])
        transformers.append(("nom", nom_pipeline, nominal_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


class DataPreprocessor:
    """Handles train/test splitting, pipeline assembly, encoding, and scaling."""

    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.column_transformer: Optional[ColumnTransformer] = None
        self.encoded_feature_names: List[str] = []

        # Cached schema reference names for compatibility
        self.nominal_cols = [c.name for c in NOMINAL_COLS]
        self.ordinal_mappings = ORDINAL_MAPPINGS
        self.numeric_cols = [c.name for c in NUMERIC_COLS]

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Extracts features (X), continuous regression target (y_reg), and classification target (y_cls).
        Guarantees that target columns, ID columns, and leakage features are excluded from X.

        Args:
            df: Raw or feature-engineered DataFrame.

        Returns:
            Tuple of (X, y_reg, y_cls)
        """
        exclude_cols = set(
            [c.name for c in ID_COLS] +
            [c.name for c in TEXT_COLS] +
            [TARGET_REGRESSION, TARGET_CLASSIFICATION] +
            list(LEAKAGE_BANNED_FEATURES)
        )

        feature_cols = [c for c in df.columns if c not in exclude_cols]
        X = df[feature_cols].copy()

        # Regression target
        if TARGET_REGRESSION in df.columns:
            y_reg = df[TARGET_REGRESSION].copy()
            if y_reg.isna().any():
                y_reg = y_reg.fillna(y_reg.median() if not y_reg.empty else 5.0)
        else:
            y_reg = pd.Series(dtype=float)

        # Classification target (mapped to 1-4 ordinals)
        if TARGET_CLASSIFICATION in df.columns:
            y_cls = df[TARGET_CLASSIFICATION].map(self.ordinal_mappings["nguy_co_hoc_vu"]).copy()
            if y_cls.isna().any():
                y_cls = y_cls.fillna(2)
            y_cls = y_cls.astype(int)
        else:
            y_cls = pd.Series(dtype=int)

        return X, y_reg, y_cls

    def split_data(
        self, X: pd.DataFrame, y_reg: pd.Series, y_cls: pd.Series
    ) -> Dict[str, Any]:
        """
        Splits data into train and test sets BEFORE any fitting (R-DATA-04).
        """
        stratify_col = y_cls if len(y_cls) > 0 and y_cls.nunique() > 1 else None

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
            stratify=stratify_col,
        )

        return {
            "X_train": X_train,
            "X_test": X_test,
            "y_reg_train": y_reg_train,
            "y_reg_test": y_reg_test,
            "y_cls_train": y_cls_train,
            "y_cls_test": y_cls_test,
        }

    def build_pipeline(self, model: Any, feature_cols: List[str]) -> Pipeline:
        """
        Constructs an end-to-end Pipeline combining preprocessing and model estimator.
        """
        preprocessor = build_column_preprocessor(feature_cols)
        return Pipeline([
            ("preprocessor", preprocessor),
            ("model", model),
        ])

    def encode_and_scale(
        self, X_train: pd.DataFrame, X_test: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Fits column transformer on X_train and transforms both train and test.
        Kept for backward compatibility with existing tests and scripts.
        """
        feature_cols = list(X_train.columns)
        self.column_transformer = build_column_preprocessor(feature_cols)

        X_train_t = self.column_transformer.fit_transform(X_train)
        X_test_t = self.column_transformer.transform(X_test)

        # Get generated feature names
        try:
            self.encoded_feature_names = self.column_transformer.get_feature_names_out().tolist()
        except Exception:
            self.encoded_feature_names = feature_cols

        return X_train_t, X_test_t, self.encoded_feature_names

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms input features using fitted ColumnTransformer.
        """
        if self.column_transformer is None:
            raise RuntimeError("ColumnTransformer is not fitted yet. Call encode_and_scale() first.")
        return self.column_transformer.transform(X)
