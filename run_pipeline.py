"""
Phase 24 — End-to-End Pipeline Runner.

Executes the full fraud-DW pipeline with per-step subprocess
control, exit-code checks, timeouts and evidence logging.

Run from the project root with the project virtualenv:

    .venv\\Scripts\\python.exe run_pipeline.py

Options:
    --steps step_a,step_b   Run only the named steps (comma separated).
    --evidence-dir PATH     Evidence output directory (default: evidence/phase_24).

Steps:
    check_postgres   - PostgreSQL readiness (SELECT 1)
    ingestion        - CSV -> RAW (GATED: requires data/raw/*.csv;
                       refused automatically when CSVs are missing so
                       the existing RAW tables are never dropped)
    verify_raw       - RAW row counts vs source expectations
    dbt_staging      - dbt staging models (runs inside the Airflow
                       container: the host venv dbt CLI is broken by
                       protobuf 4.25.9 + Python 3.14)
    dbt_marts        - dbt marts models (same container path)
    dbt_tests        - dbt data-quality tests (same container path)
    verify_quality   - DW integrity checks (fraud counts, FK sanity)
    ml_train         - train Logistic Regression / Random Forest / XGBoost
    ml_evaluate      - evaluate the three models on the held-out test set
    ml_predict       - batch prediction -> marts.predictions
    ml_shap          - SHAP explanations -> ml/models/shap_*.png
    api_check        - FastAPI /health, /ready, /predict, /transactions
    metabase_check   - Metabase /api/health + DW connection registry
    airflow_check    - Airflow webserver health + DAG presence

Every step writes its captured output to
<evidence-dir>/logs/step_<name>.log and the run summary to
<evidence-dir>/pipeline_summary.json.

The runner never prints secrets: it only records exit codes,
timings, row counts and file paths.
"""

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parent

VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

EVIDENCE_DIR = PROJECT_ROOT / "evidence" / "phase_24"

LOGS_DIR = EVIDENCE_DIR / "logs"

AIRFLOW_CONTAINER = "fraud_dw_airflow"

# Source CSVs required by ingestion/load_raw.py (DATA_DIR default ./data/raw).
INGESTION_CSVS = [
    PROJECT_ROOT / "data" / "raw" / "train_transaction.csv",
    PROJECT_ROOT / "data" / "raw" / "train_identity.csv",
]

# Row expectations from ingestion/load_raw.py (EXPECTED_TRANSACTIONS /
# EXPECTED_IDENTITY). Used to VERIFY raw tables, never to hardcode test
# passes: a mismatch is reported as a failure with the real numbers.
EXPECTED_RAW = {
    "raw.transactions": 590540,
    "raw.identity": 144233,
}

# Step registry: name -> (description, handler, timeout seconds).
STEPS = {}


def step(name, description, timeout):
    """Register a pipeline step."""

    def decorator(func):
        STEPS[name] = {
            "description": description,
            "handler": func,
            "timeout": timeout,
        }
        return func

    return decorator


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def run_subprocess(args, log_path, timeout, cwd=None, env=None):
    """Run a command, capture output, return (exit_code, output)."""

    started = time.monotonic()

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(
            f"$ {' '.join(str(a) for a in args)}\n"
            f"cwd: {cwd or PROJECT_ROOT}\n"
            f"started: {dt.datetime.now(dt.timezone.utc).isoformat()}\n\n"
        )
        log_file.flush()

        try:
            completed = subprocess.run(
                args,
                cwd=cwd,
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                text=True,
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            log_file.write(f"\nTIMEOUT after {timeout}s\n")
            exit_code = 124
        except OSError as exc:
            log_file.write(f"\nOS ERROR: {exc}\n")
            exit_code = 127

        elapsed = time.monotonic() - started
        log_file.write(f"\nexit_code: {exit_code}\nelapsed: {elapsed:.1f}s\n")

    return exit_code, elapsed


def run_python(script_rel, log_path, timeout, extra_args=None):
    """Run a project script with the project virtualenv interpreter."""

    args = [str(VENV_PYTHON), str(PROJECT_ROOT / script_rel)]
    if extra_args:
        args.extend(extra_args)
    return run_subprocess(args, log_path, timeout)


def run_dbt(selector, log_path, timeout):
    """Run a dbt command inside the Airflow container.

    The host venv dbt CLI fails on Python 3.14
    (protobuf 4.25.9: "Metaclasses with custom tp_new are not
    supported"). dbt 1.8.2 is installed and working inside the
    Airflow container (apache/airflow:2.10.5, Python 3.12), which
    is also where the production DAG runs dbt.
    """

    args = [
        "docker",
        "exec",
        AIRFLOW_CONTAINER,
        "bash",
        "-c",
        f"cd /opt/airflow/dbt && dbt {selector} --profiles-dir .",
    ]
    return run_subprocess(args, log_path, timeout)


def query_sql(sql, database=None):
    """Run one SQL statement against a database and return
    all rows. Defaults to the project DW database.

    The SQL is passed via argv (not string-embedded) so
    quotes and special characters in the statement cannot
    break the generated code.
    """

    database_clause = (
        "database=os.getenv('POSTGRES_DB','ecommerce_fraud_dw')"
        if database is None
        else f"database='{database}'"
    )
    code = (
        "import os\n"
        "import sys\n"
        "import json\n"
        "from dotenv import load_dotenv\n"
        "from sqlalchemy import URL, create_engine, text\n"
        "load_dotenv()\n"
        "url = URL.create('postgresql+psycopg2',"
        " username=os.getenv('POSTGRES_USER','postgres'),"
        " password=os.getenv('POSTGRES_PASSWORD','postgres'),"
        " host=os.getenv('POSTGRES_HOST','localhost'),"
        " port=int(os.getenv('POSTGRES_PORT','5432')),"
        f" {database_clause})\n"
        "engine = create_engine(url)\n"
        "with engine.connect() as conn:\n"
        "    rows = conn.execute(text(sys.argv[1])).fetchall()\n"
        "print(json.dumps([list(r) for r in rows]))\n"
    )
    completed = subprocess.run(
        [str(VENV_PYTHON), "-c", code, sql],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"SQL failed: {completed.stderr[-2000:]}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def http_get(url, timeout=30):
    """GET a URL, return (status_code, body_text)."""

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - connection errors are evidence
        return None, str(exc)


def http_post(url, payload, timeout=60):
    """POST JSON, return (status_code, body_text)."""

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


# ---------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------


@step(
    "check_postgres",
    "PostgreSQL readiness (SELECT 1 on the DW)",
    120,
)
def check_postgres(log_path):
    rows = query_sql("SELECT 1 AS ready")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"SELECT 1 -> {rows}\n")
    if rows != [[1]]:
        return "FAIL", f"unexpected result: {rows}"
    return "PASS", "PostgreSQL answers SELECT 1"


@step(
    "ingestion",
    "CSV -> RAW ingestion (ingestion/load_raw.py)",
    1800,
)
def ingestion(log_path):
    """GATED: ingestion/load_raw.py DROP+CREATEs the RAW tables, so it
    must never run without the source CSVs. If the CSVs are missing the
    step is recorded as SKIPPED with the reason instead of destroying
    the existing RAW data.
    """

    missing = [str(p) for p in INGESTION_CSVS if not p.exists()]

    with open(log_path, "w", encoding="utf-8") as log_file:
        if missing:
            log_file.write(
                "INGESTION SKIPPED — source CSV(s) not found:\n"
                + "\n".join(missing)
                + "\n\n"
                "ingestion/load_raw.py DROP+CREATEs raw.transactions and "
                "raw.identity, so running it without the CSVs would "
                "destroy the existing RAW data. The RAW tables are "
                "verified separately in step verify_raw.\n"
            )
            return "SKIPPED", (
                "source CSVs missing: " + ", ".join(missing)
            )

        log_file.write("Source CSVs present, running ingestion...\n")

    exit_code, elapsed = run_python(
        "ingestion/load_raw.py",
        log_path,
        1800,
    )
    if exit_code != 0:
        return "FAIL", f"load_raw.py exit code {exit_code}"
    return "PASS", f"ingestion completed in {elapsed:.0f}s"


@step(
    "verify_raw",
    "Verify RAW tables exist with the expected row counts",
    300,
)
def verify_raw(log_path):
    rows = query_sql(
        "SELECT 'raw.transactions', COUNT(*) FROM raw.transactions "
        "UNION ALL SELECT 'raw.identity', COUNT(*) FROM raw.identity"
    )
    lines = [f"{table}: {count:,} rows" for table, count in rows]

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines) + "\n")
        for table, expected in EXPECTED_RAW.items():
            actual = dict(rows)[table]
            log_file.write(
                f"{table}: expected={expected:,} actual={actual:,} "
                f"match={actual == expected}\n"
            )

    actual = dict(rows)
    mismatches = {
        table: (actual[table], expected)
        for table, expected in EXPECTED_RAW.items()
        if actual[table] != expected
    }
    if mismatches:
        return "FAIL", f"row count mismatch: {mismatches}"
    return "PASS", "; ".join(lines)


@step(
    "dbt_staging",
    "dbt staging models (view materialization, in Airflow container)",
    900,
)
def dbt_staging(log_path):
    exit_code, elapsed = run_dbt("run --select staging", log_path, 900)
    if exit_code != 0:
        return "FAIL", f"dbt staging exit code {exit_code}"
    return "PASS", f"dbt staging completed in {elapsed:.0f}s"


@step(
    "dbt_marts",
    "dbt marts models (table materialization, in Airflow container)",
    900,
)
def dbt_marts(log_path):
    exit_code, elapsed = run_dbt("run --select marts", log_path, 900)
    if exit_code != 0:
        return "FAIL", f"dbt marts exit code {exit_code}"
    return "PASS", f"dbt marts completed in {elapsed:.0f}s"


@step(
    "dbt_tests",
    "dbt data-quality tests (in Airflow container)",
    900,
)
def dbt_tests(log_path):
    exit_code, elapsed = run_dbt("test", log_path, 900)
    if exit_code != 0:
        return "FAIL", f"dbt test exit code {exit_code}"
    return "PASS", f"dbt tests completed in {elapsed:.0f}s"


@step(
    "verify_quality",
    "DW integrity: staging/fact row counts, fraud totals, dimension keys",
    300,
)
def verify_quality(log_path):
    rows = query_sql(
        "SELECT 'staging.stg_transactions', COUNT(*) FROM staging.stg_transactions "
        "UNION ALL SELECT 'marts.fact_transactions', COUNT(*) FROM marts.fact_transactions "
        "UNION ALL SELECT 'marts.fact_transactions is_fraud=1', COUNT(*) FROM marts.fact_transactions WHERE is_fraud = 1 "
        "UNION ALL SELECT 'marts.dim_product', COUNT(*) FROM marts.dim_product "
        "UNION ALL SELECT 'marts.dim_device', COUNT(*) FROM marts.dim_device "
        "UNION ALL SELECT 'marts.dim_date', COUNT(*) FROM marts.dim_date "
        "UNION ALL SELECT 'null product_key', COUNT(*) FROM marts.fact_transactions WHERE product_key IS NULL "
        "UNION ALL SELECT 'null device_key', COUNT(*) FROM marts.fact_transactions WHERE device_key IS NULL "
        "UNION ALL SELECT 'orphan product_key', COUNT(*) FROM marts.fact_transactions f LEFT JOIN marts.dim_product d ON f.product_key = d.product_key WHERE f.product_key IS NOT NULL AND d.product_key IS NULL "
        "UNION ALL SELECT 'orphan device_key', COUNT(*) FROM marts.fact_transactions f LEFT JOIN marts.dim_device d ON f.device_key = d.device_key WHERE f.device_key IS NOT NULL AND d.device_key IS NULL"
    )
    summary = {table: count for table, count in rows}

    with open(log_path, "w", encoding="utf-8") as log_file:
        for table, count in rows:
            log_file.write(f"{table}: {count:,}\n")

    fraud_count = summary.get("marts.fact_transactions is_fraud=1", 0)
    fraud_rate = (
        fraud_count / summary.get("marts.fact_transactions", 1)
        if summary.get("marts.fact_transactions")
        else 0
    )

    # Orphan semantics follow the dbt "relationships" test:
    # only NON-NULL foreign keys without a matching dimension
    # row are orphans. NULL keys are legitimate LEFT JOIN
    # results (transactions without an identity record, or
    # without a matching product/device combination) and are
    # reported separately as informational counts.
    problems = []
    if summary.get("staging.stg_transactions") != summary.get(
        "marts.fact_transactions"
    ):
        problems.append("staging/fact row count mismatch")
    if summary.get("orphan product_key", 0) != 0:
        problems.append("orphan product_key found")
    if summary.get("orphan device_key", 0) != 0:
        problems.append("orphan device_key found")

    if problems:
        return "FAIL", "; ".join(problems)
    return "PASS", (
        f"staging=fact={summary.get('marts.fact_transactions'):,}; "
        f"fraud={fraud_count:,} ({fraud_rate:.3%}); "
        f"orphan keys=0; "
        f"null product_key={summary.get('null product_key', 0):,} "
        f"(LEFT JOIN unmatched, informational)"
    )


@step(
    "ml_train",
    "Train Logistic Regression, Random Forest, XGBoost (ml/train.py)",
    7200,
)
def ml_train(log_path):
    exit_code, elapsed = run_python("ml/train.py", log_path, 7200)
    if exit_code != 0:
        return "FAIL", f"ml/train.py exit code {exit_code}"

    results_path = PROJECT_ROOT / "ml" / "models" / "training_results.json"
    if not results_path.exists():
        return "FAIL", "training_results.json not created"

    with open(results_path, encoding="utf-8") as f:
        results = json.load(f)

    models = [r["model"] for r in results.get("models", [])]
    if len(models) != 3:
        return "FAIL", f"expected 3 models in results, got {models}"

    return "PASS", (
        f"trained {', '.join(models)} in {elapsed:.0f}s; "
        f"n_features={results.get('n_features')}; "
        f"best={results.get('best_model')}"
    )


@step(
    "ml_evaluate",
    "Evaluate three models on held-out test set (ml/evaluate.py)",
    900,
)
def ml_evaluate(log_path):
    exit_code, elapsed = run_python("ml/evaluate.py", log_path, 900)
    if exit_code != 0:
        return "FAIL", f"ml/evaluate.py exit code {exit_code}"

    for artifact in (
        "evaluation_results.pkl",
        "evaluation_summary.csv",
        "xgboost_eval.png",
        "random_forest_eval.png",
        "logistic_regression_eval.png",
    ):
        if not (PROJECT_ROOT / "ml" / "models" / artifact).exists():
            return "FAIL", f"evaluation artifact missing: {artifact}"

    return "PASS", f"evaluation completed in {elapsed:.0f}s; artifacts present"


@step(
    "ml_predict",
    "Batch prediction -> marts.predictions (ml/predict.py)",
    1800,
)
def ml_predict(log_path):
    exit_code, elapsed = run_python("ml/predict.py", log_path, 1800)
    if exit_code != 0:
        return "FAIL", f"ml/predict.py exit code {exit_code}"

    for artifact in ("prediction_metrics.pkl", "prediction_metrics.json"):
        if not (PROJECT_ROOT / "ml" / "models" / artifact).exists():
            return "FAIL", f"prediction artifact missing: {artifact}"

    rows = query_sql(
        "SELECT COUNT(*), COUNT(DISTINCT transaction_id), "
        "MIN(fraud_probability), MAX(fraud_probability) "
        "FROM marts.predictions"
    )
    count, distinct_txn, min_prob, max_prob = rows[0]

    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"\nmarts.predictions: rows={count:,} distinct_txn={distinct_txn:,} "
            f"prob_range=[{min_prob:.6f}, {max_prob:.6f}]\n"
        )

    if count == 0 or distinct_txn != count:
        return "FAIL", f"predictions integrity problem: rows={count} distinct={distinct_txn}"
    if not (0.0 <= float(min_prob) <= float(max_prob) <= 1.0):
        return "FAIL", f"probability out of range: [{min_prob}, {max_prob}]"

    return "PASS", (
        f"prediction completed in {elapsed:.0f}s; "
        f"marts.predictions rows={count:,}"
    )


@step(
    "ml_shap",
    "SHAP explanations (ml/shap_explain.py)",
    1800,
)
def ml_shap(log_path):
    exit_code, elapsed = run_python("ml/shap_explain.py", log_path, 1800)
    if exit_code != 0:
        return "FAIL", f"ml/shap_explain.py exit code {exit_code}"

    artifacts = sorted(
        p.name
        for p in (PROJECT_ROOT / "ml" / "models").glob("shap_*.png")
    )
    top_features = PROJECT_ROOT / "ml" / "models" / "top_features.csv"

    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\nSHAP artifacts: {', '.join(artifacts)}\n")

    if not artifacts or not top_features.exists():
        return "FAIL", "SHAP artifacts missing"

    return "PASS", (
        f"SHAP completed in {elapsed:.0f}s; "
        f"{len(artifacts)} PNGs + top_features.csv"
    )


@step(
    "api_check",
    "FastAPI health/readiness/predict/transactions (running container)",
    300,
)
def api_check(log_path):
    lines = []

    status, body = http_get("http://localhost:8000/health")
    lines.append(f"GET /health -> {status} {body.strip()}")
    ok = status == 200 and json.loads(body)["status"] == "ok"

    status, body = http_get("http://localhost:8000/ready")
    ready = json.loads(body)
    lines.append(f"GET /ready -> {status} {body.strip()}")
    ok = ok and status == 200 and ready["status"] == "ready"

    payload = {
        "transaction_id": 999999,
        "transaction_dt": 86400,
        "transaction_amt": 150.75,
        "product_cd": "W",
        "card1": 1001,
        "card4": "visa",
        "device_type": "mobile",
    }
    status, body = http_post("http://localhost:8000/predict", payload)
    pred = json.loads(body)
    lines.append(
        f"POST /predict -> {status} "
        f"is_fraud={pred.get('is_fraud')} "
        f"fraud_probability={pred.get('fraud_probability')}"
    )
    ok = (
        ok
        and status == 200
        and 0.0 <= float(pred["fraud_probability"]) <= 1.0
        and pred["is_fraud"] in (0, 1)
    )

    status, body = http_get("http://localhost:8000/transactions/3411796")
    txn = json.loads(body)
    lines.append(
        f"GET /transactions/3411796 -> {status} "
        f"transaction_id={txn.get('transaction_id')}"
    )
    ok = ok and status == 200 and txn.get("transaction_id") == 3411796

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines) + "\n")

    if not ok:
        return "FAIL", "one or more API checks failed (see log)"
    return "PASS", "API /health /ready /predict /transactions all 200"


@step(
    "metabase_check",
    "Metabase health + application DB + DW connection registry",
    300,
)
def metabase_check(log_path):
    status, body = http_get("http://localhost:3000/api/health")
    health_ok = status == 200

    # Verify the Metabase application database (metabase_db on
    # the Windows PostgreSQL server) holds the DW connection
    # entry. PostgreSQL does not support cross-database
    # queries, so connect to metabase_db directly.
    rows = query_sql(
        "SELECT count(*) FROM metabase_database "
        "WHERE name = 'ecommerce_fraud_dw'",
        database="metabase_db",
    )
    dw_registered = rows[0][0] == 1

    lines = [
        f"GET /api/health -> {status} {body.strip()}",
        f"metabase_db.metabase_database contains ecommerce_fraud_dw: {dw_registered}",
    ]

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines) + "\n")

    if not health_ok or not dw_registered:
        return "FAIL", "Metabase health or DW connection registry check failed"
    return "PASS", "Metabase healthy; DW connection registered in metabase_db"


@step(
    "airflow_check",
    "Airflow webserver health + DAG presence (no import errors)",
    300,
)
def airflow_check(log_path):
    import base64

    credentials = base64.b64encode(b"admin:admin").decode("ascii")
    request = urllib.request.Request(
        "http://localhost:8080/api/v1/health"
    )
    request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            health = json.loads(response.read().decode("utf-8"))
            health_status = 200
    except Exception as exc:  # noqa: BLE001
        health = {"error": str(exc)}
        health_status = None

    request = urllib.request.Request(
        "http://localhost:8080/api/v1/dags"
    )
    request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            dags = json.loads(response.read().decode("utf-8"))
            dag_ids = [d["dag_id"] for d in dags.get("dags", [])]
            dag_status = 200
    except Exception as exc:  # noqa: BLE001
        dag_ids = []
        dag_status = None

    scheduler_healthy = (
        health.get("scheduler", {}).get("status") == "healthy"
    )
    metadb_healthy = (
        health.get("metadatabase", {}).get("status") == "healthy"
    )
    dag_present = "fraud_dw_pipeline" in dag_ids

    lines = [
        f"GET /api/v1/health -> {health_status} "
        f"scheduler={health.get('scheduler', {}).get('status')} "
        f"metadatabase={health.get('metadatabase', {}).get('status')}",
        f"GET /api/v1/dags -> {dag_status} dag_ids={dag_ids}",
    ]

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines) + "\n")

    if not (
        health_status == 200
        and dag_status == 200
        and scheduler_healthy
        and metadb_healthy
        and dag_present
    ):
        return "FAIL", "Airflow health or DAG presence check failed"
    return "PASS", "Airflow healthy; DAG fraud_dw_pipeline present"


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------


def run_pipeline(selected_steps, evidence_dir):
    """Run the selected steps in registry order, write summary."""

    logs_dir = evidence_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    ordered = [
        name for name in STEPS
        if not selected_steps or name in selected_steps
    ]

    results = []

    for name in ordered:
        spec = STEPS[name]
        log_path = logs_dir / f"step_{name}.log"

        print(f"[{name}] {spec['description']} ...", flush=True)

        started = dt.datetime.now(dt.timezone.utc)
        try:
            state, detail = spec["handler"](log_path)
        except Exception as exc:  # noqa: BLE001 - record and continue
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\nSTEP EXCEPTION: {exc}\n")
            state, detail = "FAIL", f"exception: {exc}"
        elapsed = (
            dt.datetime.now(dt.timezone.utc) - started
        ).total_seconds()

        try:
            log_ref = str(log_path.relative_to(PROJECT_ROOT))
        except ValueError:
            log_ref = str(log_path)

        results.append(
            {
                "step": name,
                "description": spec["description"],
                "status": state,
                "detail": detail,
                "elapsed_seconds": round(elapsed, 1),
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "log": log_ref,
            }
        )

        print(f"  -> {state}: {detail}", flush=True)

        if state == "FAIL":
            print(
                f"Pipeline stopped at step '{name}' (FAIL). "
                "Remaining steps were not executed.",
                flush=True,
            )
            break

    summary = {
        "pipeline": "ecommerce-fraud-dw end-to-end",
        "started_at": results[0]["finished_at"] if results else None,
        "evidence_dir": str(evidence_dir),
        "steps": results,
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "skipped": sum(1 for r in results if r["status"] == "SKIPPED"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
    }

    summary_path = evidence_dir / "pipeline_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary written to {summary_path}", flush=True)
    print(
        f"PASS={summary['passed']} SKIPPED={summary['skipped']} "
        f"FAIL={summary['failed']}",
        flush=True,
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--steps",
        default=None,
        help="Comma-separated step names to run (default: all)",
    )
    parser.add_argument(
        "--evidence-dir",
        default=str(EVIDENCE_DIR),
        help="Evidence output directory",
    )
    args = parser.parse_args()

    if not VENV_PYTHON.exists():
        print(f"ERROR: virtualenv python not found: {VENV_PYTHON}")
        sys.exit(2)

    selected = set(args.steps.split(",")) if args.steps else None
    if selected:
        unknown = selected - set(STEPS)
        if unknown:
            print(f"ERROR: unknown step(s): {sorted(unknown)}")
            print(f"Available: {sorted(STEPS)}")
            sys.exit(2)

    evidence_dir = Path(args.evidence_dir).resolve()
    summary = run_pipeline(selected, evidence_dir)

    sys.exit(1 if summary["failed"] else 0)


if __name__ == "__main__":
    main()
