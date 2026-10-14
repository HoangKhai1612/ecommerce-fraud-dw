
from __future__ import annotations

import importlib
import json
import os
import socket
import sys
from pathlib import Path

from src.logging_config import get_logger

ROOT = Path(__file__).resolve().parents[1]
logger = get_logger("phase26.diagnostics", "diagnostics.log")

results: list[dict[str, str]] = []


def record(name: str, status: str, detail: str = "") -> None:
    results.append({
        "check": name,
        "status": status,
        "detail": detail,
    })
    log_method = logger.error if status == "FAIL" else logger.info
    log_method("%s: %s %s", name, status, detail)


def check_path(label: str, relative_path: str) -> None:
    path = ROOT / relative_path
    record(label, "PASS" if path.exists() else "WARN", str(path))


def check_port(host: str, port: int) -> None:
    try:
        with socket.create_connection((host, port), timeout=3):
            record(f"TCP {host}:{port}", "PASS", "Connection accepted")
    except OSError as exc:
        record(f"TCP {host}:{port}", "WARN", str(exc))


def check_python_packages() -> None:
    packages = [
        "pandas",
        "sqlalchemy",
        "psycopg",
        "xgboost",
        "fastapi",
        "sklearn",
    ]

    for package in packages:
        try:
            importlib.import_module(package)
            record(f"Python package: {package}", "PASS")
        except ImportError as exc:
            record(f"Python package: {package}", "WARN", str(exc))


def check_postgres() -> None:
    # Read only environment variables; never print the password.
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    database = os.getenv("PGDATABASE", "ecommerce_fraud_dw")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD")

    try:
        import psycopg

        kwargs = {
            "host": host,
            "port": port,
            "dbname": database,
            "user": user,
            "connect_timeout": 3,
        }
        if password is not None:
            kwargs["password"] = password

        with psycopg.connect(**kwargs) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                value = cursor.fetchone()[0]

        record("PostgreSQL query", "PASS", f"SELECT 1 returned {value}")
    except Exception as exc:
        # Exception text may include host/database details; do not log secrets.
        record("PostgreSQL query", "FAIL", type(exc).__name__)


def main() -> int:
    record("Python version", "PASS", sys.version.split()[0])

    check_port("localhost", 5432)
    check_port("localhost", 8000)
    check_port("localhost", 11434)

    check_path("Environment file", ".env")
    check_path("dbt project", "dbt/dbt_project.yml")
    check_path("XGBoost model", "ml/models/xgboost.pkl")
    check_path("Feature columns", "ml/models/feature_columns.json")

    check_python_packages()
    check_postgres()

    output_dir = ROOT / "evidence" / "phase_26"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "diagnostics.json"
    output_file.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    failures = sum(item["status"] == "FAIL" for item in results)
    warnings = sum(item["status"] == "WARN" for item in results)

    print(f"\nChecks: {len(results)}")
    print(f"FAIL: {failures} | WARN: {warnings}")
    print(f"Report: {output_file}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
