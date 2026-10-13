"""
Save fitted preprocessing artifacts for API inference.

This script loads the training data, fits the preprocessing pipeline
(identical to Phase 15/16), and saves the fitted artifacts:
- FrequencyEncoder mappings
- ColumnTransformer (preprocessor)
- Feature column names (already in feature_columns.json)
"""

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.config import (
    DATABASE_URL,
    FEATURE_METADATA_OUTPUT,
    ID_COLUMN,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    VALIDATION_SIZE,
)
from ml.features.engineering import add_all_engineered_features
from ml.features.preprocessing import (
    FrequencyEncoder,
    build_preprocessor,
    fit_transform_datasets,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

MODEL_DIR = Path(__file__).resolve().parent / "models"
FREQ_ENCODER_PATH = MODEL_DIR / "frequency_encoder.pkl"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.pkl"


def load_raw_data():
    """Load raw transaction data from PostgreSQL."""
    engine = create_engine(DATABASE_URL)
    query = text("SELECT t.* FROM marts.fact_transactions AS t")
    try:
        df = pd.read_sql(query, engine)
    finally:
        engine.dispose()
    return df


def main():
    print("Loading raw data from PostgreSQL...")
    df = load_raw_data()
    print(f"Loaded {len(df):,} rows")

    # Split data (same as Phase 15)
    train_df, temp_df = train_test_split(
        df,
        test_size=(VALIDATION_SIZE + TEST_SIZE),
        stratify=df[TARGET_COLUMN],
        random_state=RANDOM_STATE,
    )

    val_df, test_df = train_test_split(
        temp_df,
        test_size=(TEST_SIZE / (VALIDATION_SIZE + TEST_SIZE)),
        stratify=temp_df[TARGET_COLUMN],
        random_state=RANDOM_STATE,
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    print(f"Train: {len(train_df):,}, Val: {len(val_df):,}, Test: {len(test_df):,}")

    # Apply feature engineering
    print("Applying feature engineering...")
    train_df = add_all_engineered_features(train_df)
    val_df = add_all_engineered_features(val_df)
    test_df = add_all_engineered_features(test_df)

    # Fit frequency encoder on TRAIN only
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

    frequency_encoder = FrequencyEncoder(frequency_columns)
    frequency_encoder.fit(train_df)

    train_df = frequency_encoder.transform(train_df)
    val_df = frequency_encoder.transform(val_df)
    test_df = frequency_encoder.transform(test_df)

    # Save frequency encoder
    joblib.dump(frequency_encoder, FREQ_ENCODER_PATH)
    print(f"Saved frequency encoder to {FREQ_ENCODER_PATH}")

    # Prepare X/y
    X_train = train_df.drop(columns=[TARGET_COLUMN, ID_COLUMN])
    y_train = train_df[TARGET_COLUMN]
    X_val = val_df.drop(columns=[TARGET_COLUMN, ID_COLUMN])
    X_test = test_df.drop(columns=[TARGET_COLUMN, ID_COLUMN])

    # Build and fit preprocessor on TRAIN only
    print("Building and fitting preprocessor...")
    preprocessor = build_preprocessor(X_train)
    
    # Fit the preprocessor
    # Need to prepare data for sklearn first
    from ml.features.preprocessing import _prepare_df_for_sklearn
    
    numeric_features = preprocessor.transformers[0][2]
    categorical_features = preprocessor.transformers[1][2]
    
    X_train_clean = _prepare_df_for_sklearn(X_train, numeric_features, categorical_features)
    preprocessor.fit(X_train_clean)

    # Save preprocessor
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Saved preprocessor to {PREPROCESSOR_PATH}")

    # Verify by transforming
    print("Verifying artifacts...")
    X_train_processed = preprocessor.transform(X_train)
    print(f"Transformed train shape: {X_train_processed.shape}")

    # Check feature names match
    feature_names = preprocessor.get_feature_names_out()
    with open(MODEL_DIR / "feature_columns.json", "r") as f:
        expected_features = json.load(f)

    if list(feature_names) == expected_features:
        print("✓ Feature names match feature_columns.json")
    else:
        print("✗ Feature name mismatch!")
        print(f"  Expected: {len(expected_features)}, Got: {len(feature_names)}")
        missing = set(expected_features) - set(feature_names)
        extra = set(feature_names) - set(expected_features)
        if missing:
            print(f"  Missing: {list(missing)[:10]}")
        if extra:
            print(f"  Extra: {list(extra)[:10]}")

    print("\nAll artifacts saved successfully!")


if __name__ == "__main__":
    main()