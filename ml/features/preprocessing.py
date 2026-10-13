import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from ml.config import CATEGORICAL_COLUMNS, IDENTITY_COLUMNS


class FrequencyEncoder:
    """
    Frequency encoder fitted on training data only.
    """

    def __init__(self, columns: list[str]):
        self.columns = columns
        self.mappings = {}

    def fit(
        self,
        df: pd.DataFrame,
    ):
        for column in self.columns:

            if column not in df.columns:
                continue

            mapping = (
                df[column]
                .value_counts(
                    normalize=True,
                    dropna=False,
                )
                .to_dict()
            )

            self.mappings[column] = mapping

        return self

    def transform(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        for column in self.columns:

            if column not in df.columns:
                continue

            mapping = self.mappings.get(
                column,
                {},
            )

            df[f"{column}_freq"] = (
                df[column]
                .map(mapping)
                .fillna(0.0)
            )

        return df


def build_preprocessor(
    train_X: pd.DataFrame,
):
    """
    Build ColumnTransformer for numeric and categorical features.

    Fits only on TRAIN data.
    """
    # Identify datetime columns to exclude
    datetime_cols = [
        c for c in train_X.columns
        if pd.api.types.is_datetime64_any_dtype(train_X[c])
    ]

    # Identify categorical features: string/object/category columns or listed in CATEGORICAL_COLUMNS
    categorical_features = [
        c for c in train_X.columns
        if c not in datetime_cols and (
            train_X[c].dtype in ("object", "string", "category") or c in CATEGORICAL_COLUMNS
        )
    ]
    categorical_features = sorted(list(set(categorical_features)))

    # Identify numeric features: remaining numeric columns
    numeric_features = [
        c for c in train_X.columns
        if c not in datetime_cols and c not in categorical_features
    ]
    numeric_features = sorted(numeric_features)

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(max_categories=30, handle_unknown="ignore", sparse_output=False, dtype=np.float32)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0,
    )

    return preprocessor


def _prepare_df_for_sklearn(
    df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    """
    Clean and cast DataFrame columns to standard numpy float32 / string dtypes.
    """
    df_clean = pd.DataFrame(index=df.index)

    for col in numeric_features:
        if col in df.columns:
            df_clean[col] = pd.to_numeric(df[col], errors="coerce").astype(np.float32)

    for col in categorical_features:
        if col in df.columns:
            df_clean[col] = df[col].astype(str).fillna("missing")

    return df_clean


def fit_transform_datasets(
    train_X: pd.DataFrame,
    val_X: pd.DataFrame,
    test_X: pd.DataFrame,
):
    """
    Fit preprocessing on TRAIN only, transform all splits.

    Returns:
        preprocessor: fitted ColumnTransformer
        train_processed: pd.DataFrame
        val_processed: pd.DataFrame
        test_processed: pd.DataFrame
    """
    preprocessor = build_preprocessor(train_X)

    # Extract feature lists used by ColumnTransformer
    numeric_features = preprocessor.transformers[0][2]
    categorical_features = preprocessor.transformers[1][2]

    train_X_clean = _prepare_df_for_sklearn(train_X, numeric_features, categorical_features)
    val_X_clean = _prepare_df_for_sklearn(val_X, numeric_features, categorical_features)
    test_X_clean = _prepare_df_for_sklearn(test_X, numeric_features, categorical_features)

    train_arr = preprocessor.fit_transform(train_X_clean)
    val_arr = preprocessor.transform(val_X_clean)
    test_arr = preprocessor.transform(test_X_clean)

    feature_names = preprocessor.get_feature_names_out()

    train_processed = pd.DataFrame(train_arr, columns=feature_names, index=train_X.index)
    val_processed = pd.DataFrame(val_arr, columns=feature_names, index=val_X.index)
    test_processed = pd.DataFrame(test_arr, columns=feature_names, index=test_X.index)

    return (
        preprocessor,
        train_processed,
        val_processed,
        test_processed,
    )