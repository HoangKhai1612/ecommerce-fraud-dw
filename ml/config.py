"""
Configuration for Phase 15 - Fraud Detection Data Preparation.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ML_DIR = PROJECT_ROOT / "ml"

DATA_DIR = ML_DIR / "data"

ARTIFACTS_DIR = ML_DIR / "artifacts"

PREPROCESSING_DIR = ARTIFACTS_DIR / "preprocessing"


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecommerce_fraud_dw")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# URL-encode password to handle special characters like @
encoded_password = quote_plus(POSTGRES_PASSWORD)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)


# ---------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------

TARGET_COLUMN = "is_fraud"

ID_COLUMN = "transaction_id"


# ---------------------------------------------------------------------
# Split configuration
# ---------------------------------------------------------------------

RANDOM_STATE = 42

TRAIN_SIZE = 0.70

VALIDATION_SIZE = 0.15

TEST_SIZE = 0.15


# ---------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------

TRAIN_OUTPUT = DATA_DIR / "train.parquet"

VALIDATION_OUTPUT = DATA_DIR / "val.parquet"

TEST_OUTPUT = DATA_DIR / "test.parquet"

FEATURE_METADATA_OUTPUT = DATA_DIR / "feature_metadata.json"


# ---------------------------------------------------------------------
# Feature configuration
# ---------------------------------------------------------------------

AMOUNT_BINS = [
    0,
    50,
    100,
    200,
    500,
    1000,
    5000,
    10000,
    float("inf"),
]

AMOUNT_BIN_LABELS = [
    "0-50",
    "50-100",
    "100-200",
    "200-500",
    "500-1K",
    "1K-5K",
    "5K-10K",
    "10K+",
]


# Columns used as categorical features.

CATEGORICAL_COLUMNS = [
    "product_cd",
    "card4",
    "card6",
    "transaction_amt_bin",
]


# Columns used as frequency features.

FREQUENCY_COLUMNS = [
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


# Identity columns.

IDENTITY_COLUMNS = [
    f"id_{i:02d}"
    for i in range(1, 39)
]