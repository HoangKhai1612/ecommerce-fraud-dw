"""
Feature engineering for fraud detection.

Phase 15:
- Time features
- Missing indicators
- Amount bins
- Frequency features
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.config import AMOUNT_BIN_LABELS, AMOUNT_BINS


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create time-related features from TransactionDT.

    TransactionDT is treated as relative elapsed seconds,
    not as a real Unix timestamp.
    """

    df = df.copy()

    if "transaction_dt" not in df.columns:
        raise ValueError(
            "Column 'transaction_dt' is required for time features."
        )

    transaction_dt = pd.to_numeric(
        df["transaction_dt"],
        errors="coerce",
    )

    seconds_in_day = transaction_dt % 86400

    df["transaction_hour"] = (
        seconds_in_day // 3600
    ).astype("Int64")

    df["transaction_day_index"] = (
        transaction_dt // 86400
    ).astype("Int64")

    df["transaction_dayofweek"] = (
        df["transaction_day_index"] % 7
    ).astype("Int64")

    df["is_weekend"] = (
        df["transaction_dayofweek"]
        .isin([5, 6])
        .astype("int8")
    )

    return df


def add_missing_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add selected missing-value indicators.

    The indicator is 1 when the original value is missing,
    otherwise 0. Always creates the indicator column to ensure
    consistent feature set for inference.
    """

    df = df.copy()

    # Identity fields.
    identity_columns = [
        column
        for column in df.columns
        if column.startswith("id_")
    ]

    for column in identity_columns:
        # Safety check: ensure column is a string and exists
        if not isinstance(column, str):
            continue
        if column not in df.columns:
            continue

        try:
            # ALWAYS create the missing indicator, not just when there are NaNs
            # This ensures consistent feature set for inference
            df[f"{column}_missing"] = (
                df[column].isna().astype("int8")
            )
        except Exception as e:
            print(f"Warning: Could not process column {column}: {e}")
            continue

    # Device information.
    if "device_info" in df.columns:
        df["device_info_missing"] = (
            df["device_info"].isna()
            | df["device_info"].astype("string").eq("")
        ).astype("int8")

    # Email domains.
    for column in [
        "p_emaildomain",
        "r_emaildomain",
    ]:
        if column in df.columns:
            df[f"{column}_missing"] = (
                df[column].isna()
                | df[column].astype("string").eq("")
            ).astype("int8")

    return df


def add_amount_bin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create categorical transaction amount bins.
    """

    df = df.copy()

    if "transaction_amt" not in df.columns:
        raise ValueError(
            "Column 'transaction_amt' is required."
        )

    df["transaction_amt_bin"] = pd.cut(
        pd.to_numeric(
            df["transaction_amt"],
            errors="coerce",
        ),
        bins=AMOUNT_BINS,
        labels=AMOUNT_BIN_LABELS,
        include_lowest=True,
        right=True,
    )

    return df


def add_basic_frequency_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create simple global frequency features.

    IMPORTANT:
    This function is intended for exploratory/basic feature creation.
    Frequency features that learn statistics from data should be fitted
    on TRAIN only in preprocessing.py.
    """

    df = df.copy()

    for column in [
        "device_type",
        "product_cd",
        "p_emaildomain",
    ]:
        if column not in df.columns:
            continue

        frequency = (
            df[column]
            .value_counts(normalize=True, dropna=False)
        )

        df[f"{column}_freq"] = (
            df[column]
            .map(frequency)
            .fillna(0.0)
        )

    return df


def add_all_engineered_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply deterministic feature engineering.
    """

    df = add_time_features(df)

    df = add_missing_indicators(df)

    df = add_amount_bin(df)

    return df