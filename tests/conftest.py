"""Shared pytest fixtures."""
import pytest
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw")


def pytest_addoption(parser):
    parser.addoption(
        "--run-pipeline",
        action="store_true",
        default=False,
        help="Run full pipeline test (requires all services)",
    )


@pytest.fixture(scope="session")
def engine():
    """Database engine fixture."""
    eng = create_engine(DB_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def sample_transaction():
    """Sample transaction data."""
    return {
        "TransactionID": 3561737,
        "TransactionDT": 86400,
        "TransactionAmt": 49.5,
        "ProductCD": "W",
        "card1": 567,
        "card2": 100.0,
        "card3": 200.0,
        "card4": "Visa",
        "card5": 134.0,
        "card6": "credit",
    }