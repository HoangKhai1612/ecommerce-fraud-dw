"""PostgreSQL connection management."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine import URL

# Load environment variables
load_dotenv()


def get_database_url() -> URL:
    """Build DATABASE_URL from environment variables."""
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
    )


# Create engine lazily
engine: Engine | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global engine
    if engine is None:
        engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=1800,
        )
    return engine


def get_connection() -> Generator:
    """Yield a database connection and always close it."""
    eng = get_engine()
    with eng.connect() as connection:
        yield connection


def check_database() -> bool:
    """Return whether PostgreSQL can execute a simple query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False