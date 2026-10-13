"""
Phase 15 - Fraud Detection Data Preparation.

Pipeline:

1. Load data from PostgreSQL.
2. Join transaction and identity data.
3. Validate transaction grain.
4. Engineer deterministic features.
5. Split 70/15/15 using stratification.
6. Fit frequency encoders on TRAIN only.
7. Fit preprocessing on TRAIN only.
8. Transform TRAIN / VAL / TEST.
9. Validate final datasets.
10. Save Parquet and metadata.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split

from ml.config import (
    DATABASE_URL,
    FEATURE_METADATA_OUTPUT,
    ID_COLUMN,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    TEST_OUTPUT,
    TRAIN_SIZE,
    TRAIN_OUTPUT,
    VALIDATION_OUTPUT,
    VALIDATION_SIZE,
)

from ml.features.engineering import (
    add_all_engineered_features,
)

from ml.features.preprocessing import (
    FrequencyEncoder,
    fit_transform_datasets,
)


def load_data() -> pd.DataFrame:
    """
    Load transaction + identity data.

    Grain:
        one row = one transaction.
    """

    engine = create_engine(
        DATABASE_URL
    )

    query = text(
        """
        SELECT
            t.*

        FROM marts.fact_transactions AS t
        """
    )

    try:
        df = pd.read_sql(
            query,
            engine,
        )
    finally:
        engine.dispose()

    return df


def validate_base_dataset(
    df: pd.DataFrame,
) -> None:
    """
    Validate basic ML dataset integrity.
    """

    if ID_COLUMN not in df.columns:
        raise ValueError(
            f"Missing required column: {ID_COLUMN}"
        )

    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Missing required column: {TARGET_COLUMN}"
        )

    total_rows = len(df)

    distinct_ids = (
        df[ID_COLUMN]
        .nunique(dropna=True)
    )

    null_ids = (
        df[ID_COLUMN]
        .isna()
        .sum()
    )

    duplicate_ids = (
        df[ID_COLUMN]
        .duplicated()
        .sum()
    )

    print("\nBase dataset validation")
    print("-----------------------")
    print(f"Rows:              {total_rows:,}")
    print(f"Distinct IDs:      {distinct_ids:,}")
    print(f"Null IDs:          {null_ids:,}")
    print(f"Duplicate IDs:     {duplicate_ids:,}")

    if total_rows != distinct_ids:
        raise ValueError(
            "Grain violation: "
            "rows != distinct transaction_id."
        )

    if null_ids != 0:
        raise ValueError(
            "transaction_id contains NULL values."
        )

    if duplicate_ids != 0:
        raise ValueError(
            "Duplicate transaction_id detected."
        )


def split_data(
    df: pd.DataFrame,
):
    """
    Stratified 70/15/15 split.
    """

    train_df, temp_df = train_test_split(
        df,
        test_size=(
            VALIDATION_SIZE
            + TEST_SIZE
        ),
        stratify=df[TARGET_COLUMN],
        random_state=RANDOM_STATE,
    )

    val_df, test_df = train_test_split(
        temp_df,
        test_size=(
            TEST_SIZE
            / (
                VALIDATION_SIZE
                + TEST_SIZE
            )
        ),
        stratify=temp_df[TARGET_COLUMN],
        random_state=RANDOM_STATE,
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def validate_split(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """
    Validate split sizes, class distribution and ID overlap.
    """

    total = (
        len(train_df)
        + len(val_df)
        + len(test_df)
    )

    print("\nSplit validation")
    print("----------------")
    print(
        f"Train: {len(train_df):,} "
        f"({len(train_df) / total:.2%}) "
        f"fraud={train_df[TARGET_COLUMN].mean():.4%}"
    )

    print(
        f"Val:   {len(val_df):,} "
        f"({len(val_df) / total:.2%}) "
        f"fraud={val_df[TARGET_COLUMN].mean():.4%}"
    )

    print(
        f"Test:  {len(test_df):,} "
        f"({len(test_df) / total:.2%}) "
        f"fraud={test_df[TARGET_COLUMN].mean():.4%}"
    )

    train_ids = set(
        train_df[ID_COLUMN]
    )

    val_ids = set(
        val_df[ID_COLUMN]
    )

    test_ids = set(
        test_df[ID_COLUMN]
    )

    if not train_ids.isdisjoint(val_ids):
        raise ValueError(
            "TRAIN/VAL transaction overlap detected."
        )

    if not train_ids.isdisjoint(test_ids):
        raise ValueError(
            "TRAIN/TEST transaction overlap detected."
        )

    if not val_ids.isdisjoint(test_ids):
        raise ValueError(
            "VAL/TEST transaction overlap detected."
        )


def build_features(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
):
    """
    Build deterministic features first,
    then fit frequency encoding on TRAIN only.
    """

    train_df = add_all_engineered_features(
        train_df
    )

    val_df = add_all_engineered_features(
        val_df
    )

    test_df = add_all_engineered_features(
        test_df
    )

    frequency_columns = [
        "device_type",
        "product_cd",
        "p_emaildomain",
        "card1",
        "card2",
        "card3",
        "card4",
        "card5",
        "card6",
    ]

    frequency_encoder = FrequencyEncoder(
        frequency_columns
    )

    frequency_encoder.fit(
        train_df
    )

    train_df = frequency_encoder.transform(
        train_df
    )

    val_df = frequency_encoder.transform(
        val_df
    )

    test_df = frequency_encoder.transform(
        test_df
    )

    return (
        train_df,
        val_df,
        test_df,
    )


def prepare_target_and_features(
    df: pd.DataFrame,
):
    """
    Separate target from feature matrix.

    transaction_id is retained separately for validation,
    but is NOT used as an ML feature.
    """

    y = df[TARGET_COLUMN].astype("int8")

    X = df.drop(
        columns=[
            TARGET_COLUMN,
            ID_COLUMN,
        ],
        errors="ignore",
    )

    return X, y


def save_processed_data(
    train_processed: pd.DataFrame,
    val_processed: pd.DataFrame,
    test_processed: pd.DataFrame,
    train_y: pd.Series,
    val_y: pd.Series,
    test_y: pd.Series,
):
    """
    Save processed datasets.
    """

    TRAIN_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_output = train_processed.copy()
    val_output = val_processed.copy()
    test_output = test_processed.copy()

    train_output[TARGET_COLUMN] = (
        train_y.to_numpy()
    )

    val_output[TARGET_COLUMN] = (
        val_y.to_numpy()
    )

    test_output[TARGET_COLUMN] = (
        test_y.to_numpy()
    )

    train_output.to_parquet(
        TRAIN_OUTPUT,
        index=False,
    )

    val_output.to_parquet(
        VALIDATION_OUTPUT,
        index=False,
    )

    test_output.to_parquet(
        TEST_OUTPUT,
        index=False,
    )

    feature_names = train_processed.columns.tolist()

    metadata = {
        "phase": 15,
        "target": TARGET_COLUMN,
        "id_column": ID_COLUMN,
        "random_state": RANDOM_STATE,
        "split": {
            "train": TRAIN_SIZE,
            "validation": VALIDATION_SIZE,
            "test": TEST_SIZE,
        },
        "rows": {
            "train": len(train_output),
            "validation": len(val_output),
            "test": len(test_output),
        },
        "features": {
            "count": len(feature_names),
            "names": feature_names,
        },
    }

    with open(
        FEATURE_METADATA_OUTPUT,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main():
    print("=" * 70)
    print("PHASE 15 - FRAUD DETECTION DATA PREPARATION")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Load
    # ---------------------------------------------------------------

    print("\n[1/7] Loading data...")

    df = load_data()

    print(
        f"Loaded rows: {len(df):,}"
    )

    print(
        f"Loaded columns: {len(df.columns):,}"
    )

    # ---------------------------------------------------------------
    # 2. Validate
    # ---------------------------------------------------------------

    print("\n[2/7] Validating base dataset...")

    validate_base_dataset(df)

    # ---------------------------------------------------------------
    # 3. Feature engineering
    # ---------------------------------------------------------------

    print("\n[3/7] Splitting data...")

    train_df, val_df, test_df = split_data(
        df
    )

    validate_split(
        train_df,
        val_df,
        test_df,
    )

    # ---------------------------------------------------------------
    # 4. Feature engineering
    # ---------------------------------------------------------------

    print(
        "\n[4/7] Engineering features..."
    )

    (
        train_df,
        val_df,
        test_df,
    ) = build_features(
        train_df,
        val_df,
        test_df,
    )

    # ---------------------------------------------------------------
    # 5. Separate X/y
    # ---------------------------------------------------------------

    print(
        "\n[5/7] Separating features and target..."
    )

    train_X, train_y = prepare_target_and_features(
        train_df
    )

    val_X, val_y = prepare_target_and_features(
        val_df
    )

    test_X, test_y = prepare_target_and_features(
        test_df
    )

    print(
        f"Raw ML features before preprocessing: "
        f"{train_X.shape[1]:,}"
    )

    # ---------------------------------------------------------------
    # 6. Fit preprocessing ONLY on TRAIN
    # ---------------------------------------------------------------

    print(
        "\n[6/7] Fitting preprocessing on TRAIN only..."
    )

    (
        preprocessor,
        train_processed,
        val_processed,
        test_processed,
    ) = fit_transform_datasets(
        train_X,
        val_X,
        test_X,
    )

    print(
        f"Processed feature count: "
        f"{train_processed.shape[1]:,}"
    )

    if (
        train_processed.shape[1]
        != val_processed.shape[1]
        or
        train_processed.shape[1]
        != test_processed.shape[1]
    ):
        raise ValueError(
            "Feature count mismatch between "
            "TRAIN/VAL/TEST."
        )

    # ---------------------------------------------------------------
    # 7. Save
    # ---------------------------------------------------------------

    print(
        "\n[7/7] Saving processed datasets..."
    )

    save_processed_data(
        train_processed,
        val_processed,
        test_processed,
        train_y,
        val_y,
        test_y,
    )

    print("\n" + "=" * 70)
    print("PHASE 15 COMPLETED")
    print("=" * 70)

    print(
        f"Train: {len(train_processed):,}"
    )

    print(
        f"Validation: {len(val_processed):,}"
    )

    print(
        f"Test: {len(test_processed):,}"
    )

    print(
        f"Features: {train_processed.shape[1]:,}"
    )

    print(
        f"Saved to: {TRAIN_OUTPUT.parent}"
    )


if __name__ == "__main__":
    main()