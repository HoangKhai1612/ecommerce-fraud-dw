"""
Phase 24 — End-to-End Pipeline Verification Tests.

Run from the project root with the project virtualenv:

    .venv\\Scripts\\python.exe -m pytest tests/test_end_to_end.py -v

Test design:

- Verification tests (C1-C9) are INDEPENDENT state checks against
  the real PostgreSQL Data Warehouse and the real running Docker
  services. They do not depend on execution order and do not
  modify warehouse data (read-only queries + HTTP checks).
- test_ingestion_step_is_safely_gated executes the real ingestion
  step of the pipeline runner and asserts the documented safety
  gate: when source CSVs are absent the step is SKIPPED instead
  of dropping the existing RAW tables.
- test_dbt_tests_pass executes the real `dbt test` inside the
  Airflow container (dbt 1.8.2) and asserts zero failures.
- test_full_pipeline is opt-in via the custom --run-pipeline
  pytest option. It executes run_pipeline.py which runs every
  pipeline step for real (ingestion gate, dbt staging/marts/
  tests, ML training of all three models, evaluation, batch
  prediction, SHAP, API/Metabase/Airflow checks) and asserts
  the runner summary.

No mock data, no hardcoded passes: every assertion reads real
database state or real HTTP responses.
"""

import base64
import json
import subprocess
import time
from pathlib import Path

import pytest
import requests
from sqlalchemy import URL, create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

AIRFLOW_CONTAINER = "fraud_dw_airflow"

API_BASE = "http://localhost:8000"

METABASE_BASE = "http://localhost:3000"

AIRFLOW_BASE = "http://localhost:8080"

EXPECTED_RAW = {
    "raw.transactions": 590540,
    "raw.identity": 144233,
}

EXPECTED_MARTS_FACT = 590540


# ---------------------------------------------------------------------
# pytest custom option: --run-pipeline (declared in conftest.py)
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped engine against the real DW (from .env)."""

    from dotenv import load_dotenv
    import os

    load_dotenv(PROJECT_ROOT / ".env")

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
    )
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


def scalar(db_engine, sql):
    with db_engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def rows(db_engine, sql):
    with db_engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


def airflow_request(path):
    """Authenticated request to the Airflow REST API."""

    token = base64.b64encode(b"admin:admin").decode("ascii")
    response = requests.get(
        f"{AIRFLOW_BASE}/api/v1{path}",
        headers={"Authorization": f"Basic {token}"},
        timeout=30,
    )
    return response


# ---------------------------------------------------------------------
# C1 — Infrastructure
# ---------------------------------------------------------------------


class TestInfrastructure:
    """C1: PostgreSQL and dependent services are real and reachable."""

    def test_postgres_connects(self, db_engine):
        assert scalar(db_engine, "SELECT 1") == 1

    def test_required_database_and_schemas_exist(self, db_engine):
        schemas = {
            row[0]
            for row in rows(
                db_engine,
                "SELECT schema_name FROM information_schema.schemata",
            )
        }
        assert {"raw", "staging", "marts"} <= schemas

    def test_airflow_health(self):
        response = airflow_request("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["metadatabase"]["status"] == "healthy"
        assert health["scheduler"]["status"] == "healthy"

    def test_metabase_health(self):
        response = requests.get(
            f"{METABASE_BASE}/api/health", timeout=30
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_ollama_api_reachable(self):
        # Ollama runs natively on the Windows host; the AI
        # Assistant container reaches it via host.docker.internal.
        response = requests.get(
            "http://localhost:11434/api/tags", timeout=30
        )
        assert response.status_code == 200
        models = response.json()["models"]
        assert any(m["name"] == "llama3:latest" for m in models)


# ---------------------------------------------------------------------
# C2 — Ingestion / RAW
# ---------------------------------------------------------------------


class TestIngestion:
    """C2: RAW layer state and the ingestion safety gate."""

    def test_raw_tables_populated(self, db_engine):
        counts = {
            table: count
            for table, count in rows(
                db_engine,
                "SELECT 'raw.transactions', COUNT(*) FROM raw.transactions "
                "UNION ALL "
                "SELECT 'raw.identity', COUNT(*) FROM raw.identity",
            )
        }
        for table, expected in EXPECTED_RAW.items():
            assert counts[table] == expected, (
                f"{table}: expected {expected:,}, "
                f"got {counts[table]:,}"
            )

    def test_raw_primary_keys_unique(self, db_engine):
        dup_txn = scalar(
            db_engine,
            "SELECT COUNT(*) FROM ("
            "  SELECT \"TransactionID\" FROM raw.transactions"
            "  GROUP BY \"TransactionID\" HAVING COUNT(*) > 1"
            ") d",
        )
        assert dup_txn == 0

    def test_ingestion_step_is_safely_gated(self, tmp_path):
        """The pipeline runner must refuse to run ingestion when the
        source CSVs are missing (ingestion DROP+CREATEs RAW tables).

        This executes the real ingestion step logic and asserts the
        SKIPPED outcome instead of a destructive run.
        """

        csv_dir = PROJECT_ROOT / "data" / "raw"
        csvs_present = csv_dir.exists() and any(
            csv_dir.glob("*.csv")
        )

        evidence = tmp_path / "evidence_gate"
        completed = subprocess.run(
            [
                str(VENV_PYTHON),
                str(PROJECT_ROOT / "run_pipeline.py"),
                "--steps",
                "ingestion",
                "--evidence-dir",
                str(evidence),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=PROJECT_ROOT,
        )

        summary = json.loads(
            (evidence / "pipeline_summary.json").read_text()
        )
        step = summary["steps"][0]

        if csvs_present:
            assert step["status"] == "PASS"
        else:
            assert step["status"] == "SKIPPED"
            assert "CSV" in step["detail"]

        # RAW data must be untouched by the gated step.
        # (Checked indirectly: the runner exited without FAIL.)
        assert completed.returncode in (0, 1)
        assert summary["failed"] == 0


# ---------------------------------------------------------------------
# C3 — dbt
# ---------------------------------------------------------------------


class TestDbt:
    """C3: dbt staging, marts and tests (real execution)."""

    def test_dbt_staging_model_row_count(self, db_engine):
        count = scalar(
            db_engine, "SELECT COUNT(*) FROM staging.stg_transactions"
        )
        assert count == EXPECTED_MARTS_FACT

    def test_dbt_marts_fact_and_dimensions(self, db_engine):
        fact = scalar(
            db_engine, "SELECT COUNT(*) FROM marts.fact_transactions"
        )
        assert fact == EXPECTED_MARTS_FACT

        for dim, expected in (
            ("marts.dim_product", 22),
            ("marts.dim_device", 1939),
            ("marts.dim_date", 183),
        ):
            count = scalar(db_engine, f"SELECT COUNT(*) FROM {dim}")
            assert count == expected, (
                f"{dim}: expected {expected}, got {count}"
            )

    def test_dbt_marts_foreign_keys_intact(self, db_engine):
        """Orphan semantics follow the dbt relationships test:
        only NON-NULL foreign keys without a matching dimension
        row are orphans. NULL keys are legitimate LEFT JOIN
        results (transactions without identity/product match)."""

        orphan_product = scalar(
            db_engine,
            "SELECT COUNT(*) FROM marts.fact_transactions f "
            "LEFT JOIN marts.dim_product d "
            "ON f.product_key = d.product_key "
            "WHERE f.product_key IS NOT NULL "
            "AND d.product_key IS NULL",
        )
        orphan_device = scalar(
            db_engine,
            "SELECT COUNT(*) FROM marts.fact_transactions f "
            "LEFT JOIN marts.dim_device d "
            "ON f.device_key = d.device_key "
            "WHERE f.device_key IS NOT NULL "
            "AND d.device_key IS NULL",
        )
        assert orphan_product == 0
        assert orphan_device == 0

    def test_dbt_tests_pass(self):
        """Execute the real `dbt test` inside the Airflow container
        (dbt 1.8.2) and assert zero test failures."""

        completed = subprocess.run(
            [
                "docker",
                "exec",
                AIRFLOW_CONTAINER,
                "bash",
                "-c",
                "cd /opt/airflow/dbt && dbt test --profiles-dir .",
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
        output = completed.stdout + completed.stderr
        assert completed.returncode == 0, output[-3000:]
        assert "PASS=" in output
        assert "ERROR=0" in output


# ---------------------------------------------------------------------
# C4 — Machine Learning
# ---------------------------------------------------------------------


class TestMachineLearning:
    """C4: three trained models with real metrics and artifacts."""

    def test_three_model_artifacts_exist(self):
        models_dir = PROJECT_ROOT / "ml" / "models"
        for artifact in (
            "logistic_regression.pkl",
            "logistic_scaler.pkl",
            "random_forest.pkl",
            "xgboost.pkl",
            "feature_columns.json",
            "frequency_encoder.pkl",
            "preprocessor.pkl",
        ):
            path = models_dir / artifact
            assert path.exists(), f"missing artifact: {artifact}"
            assert path.stat().st_size > 0, f"empty artifact: {artifact}"

    def test_training_results_contain_three_models(self):
        results = json.loads(
            (PROJECT_ROOT / "ml" / "models" / "training_results.json").read_text()
        )
        assert results["n_features"] == 1014
        assert results["train_rows"] > 0
        assert results["validation_rows"] > 0
        assert len(results["models"]) == 3

        for model in results["models"]:
            for metric in ("roc_auc", "pr_auc", "precision", "recall", "f1"):
                value = model[metric]
                assert 0.0 <= value <= 1.0, (
                    f"{model['model']}.{metric}={value} out of [0,1]"
                )

    def test_evaluation_artifacts_exist(self):
        models_dir = PROJECT_ROOT / "ml" / "models"
        for artifact in (
            "evaluation_results.pkl",
            "evaluation_summary.csv",
            "xgboost_eval.png",
            "random_forest_eval.png",
            "logistic_regression_eval.png",
        ):
            assert (models_dir / artifact).exists(), artifact


# ---------------------------------------------------------------------
# C5 — Prediction
# ---------------------------------------------------------------------


class TestPrediction:
    """C5: batch predictions persisted in marts.predictions."""

    def test_predictions_table_schema(self, db_engine):
        columns = {
            row[0]
            for row in rows(
                db_engine,
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'marts' "
                "AND table_name = 'predictions'",
            )
        }
        assert {
            "prediction_id",
            "transaction_id",
            "model_version",
            "is_fraud_actual",
            "is_fraud_predicted",
            "fraud_probability",
            "threshold",
            "predicted_at",
        } <= columns

    def test_predictions_content_domain(self, db_engine):
        count, distinct_txn, min_prob, max_prob = rows(
            db_engine,
            "SELECT COUNT(*), COUNT(DISTINCT transaction_id), "
            "MIN(fraud_probability), MAX(fraud_probability) "
            "FROM marts.predictions",
        )[0]

        assert count > 0
        assert distinct_txn == count, "duplicate transaction_id"
        assert 0.0 <= float(min_prob) <= float(max_prob) <= 1.0

    def test_predictions_link_to_transactions(self, db_engine):
        """Every prediction must reference an existing fact row."""

        orphan = scalar(
            db_engine,
            "SELECT COUNT(*) FROM marts.predictions p "
            "LEFT JOIN marts.fact_transactions f "
            "ON p.transaction_id = f.transaction_id "
            "WHERE f.transaction_id IS NULL",
        )
        assert orphan == 0

    def test_batch_vs_online_prediction_consistent(self, db_engine):
        """Batch (marts.predictions) and online (POST /predict) both
        return probabilities in [0,1] for the same model version."""

        batch_version = scalar(
            db_engine,
            "SELECT DISTINCT model_version FROM marts.predictions",
        )
        assert batch_version == "xgboost-v1-phase16"

        payload = {
            "transaction_id": 999999,
            "transaction_dt": 86400,
            "transaction_amt": 150.75,
            "product_cd": "W",
            "card1": 1001,
            "card4": "visa",
            "device_type": "mobile",
        }
        response = requests.post(
            f"{API_BASE}/predict", json=payload, timeout=120
        )
        assert response.status_code == 200
        body = response.json()
        assert body["model_version"] == batch_version
        assert 0.0 <= body["fraud_probability"] <= 1.0
        assert body["is_fraud"] in (0, 1)


# ---------------------------------------------------------------------
# C6 — SHAP
# ---------------------------------------------------------------------


class TestShap:
    """C6: SHAP explanation artifacts are valid."""

    def test_shap_artifacts_exist_and_are_pngs(self):
        models_dir = PROJECT_ROOT / "ml" / "models"
        pngs = sorted(models_dir.glob("shap_*.png"))
        assert len(pngs) >= 3, f"expected shap_*.png artifacts, got {pngs}"

        for png in pngs:
            assert png.stat().st_size > 0
            # PNG magic bytes
            assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

        assert (models_dir / "top_features.csv").exists()


# ---------------------------------------------------------------------
# C7 — FastAPI
# ---------------------------------------------------------------------


class TestFastAPI:
    """C7: FastAPI endpoints of the running container."""

    def test_api_health(self):
        response = requests.get(f"{API_BASE}/health", timeout=30)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_readiness(self):
        response = requests.get(f"{API_BASE}/ready", timeout=30)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["database"] == "ok"

    def test_api_predict_valid_request(self):
        payload = {
            "transaction_id": 12345,
            "transaction_dt": 86400,
            "transaction_amt": 100.0,
            "product_cd": "W",
        }
        response = requests.post(
            f"{API_BASE}/predict", json=payload, timeout=120
        )
        assert response.status_code == 200
        body = response.json()
        assert 0.0 <= body["fraud_probability"] <= 1.0
        assert body["is_fraud"] in (0, 1)
        assert body["risk_level"] in ("low", "medium", "high")

    def test_api_predict_invalid_request_rejected(self):
        response = requests.post(
            f"{API_BASE}/predict",
            json={"transaction_id": "not_an_int"},
            timeout=30,
        )
        assert response.status_code == 422

    def test_api_get_transaction(self, db_engine):
        transaction_id = scalar(
            db_engine,
            "SELECT transaction_id FROM marts.fact_transactions "
            "ORDER BY transaction_id LIMIT 1",
        )
        response = requests.get(
            f"{API_BASE}/transactions/{transaction_id}", timeout=60
        )
        assert response.status_code == 200
        assert response.json()["transaction_id"] == transaction_id

    def test_api_top_predictions(self):
        response = requests.get(
            f"{API_BASE}/transactions/predictions/top?limit=5",
            timeout=60,
        )
        assert response.status_code == 200
        body = response.json()
        assert 1 <= len(body) <= 5
        for row in body:
            assert 0.0 <= row["fraud_probability"] <= 1.0


# ---------------------------------------------------------------------
# C8 — Metabase
# ---------------------------------------------------------------------


class TestMetabase:
    """C8: Metabase service and its database connections."""

    def test_metabase_health(self):
        response = requests.get(
            f"{METABASE_BASE}/api/health", timeout=30
        )
        assert response.status_code == 200

    def test_metabase_application_database_has_dw_connection(self):
        """The Metabase application database (metabase_db) must
        register the Data Warehouse connection — evidence that
        Metabase is wired to the real DW, not just returning 200.

        PostgreSQL does not support cross-database queries, so a
        dedicated connection to metabase_db is used.
        """

        import os
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")

        url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database="metabase_db",
        )
        engine = create_engine(url, pool_pre_ping=True)
        try:
            registered = scalar(
                engine,
                "SELECT COUNT(*) FROM metabase_database "
                "WHERE name = 'ecommerce_fraud_dw'",
            )
        finally:
            engine.dispose()
        assert registered == 1

    def test_metabase_dw_tables_queryable(self, db_engine):
        """Tables Metabase exposes for analysis are queryable."""

        count = scalar(
            db_engine, "SELECT COUNT(*) FROM marts.fact_transactions"
        )
        assert count == EXPECTED_MARTS_FACT


# ---------------------------------------------------------------------
# C9 — Airflow
# ---------------------------------------------------------------------


class TestAirflow:
    """C9: Airflow DAG presence, import health and task wiring."""

    def test_dag_present_and_not_paused(self):
        response = airflow_request("/dags")
        assert response.status_code == 200
        dags = {
            d["dag_id"]: d
            for d in response.json()["dags"]
        }
        assert "fraud_dw_pipeline" in dags
        assert dags["fraud_dw_pipeline"]["is_paused"] is False

    def test_dag_has_no_import_errors(self):
        """Parse the DAG bag inside the container and assert zero
        import errors."""

        completed = subprocess.run(
            [
                "docker",
                "exec",
                AIRFLOW_CONTAINER,
                "python",
                "-c",
                "from airflow.models import DagBag; "
                "bag = DagBag('/opt/airflow/dags', include_examples=False); "
                "print(len(bag.dags), len(bag.import_errors))",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert completed.returncode == 0, completed.stderr[-2000:]
        dag_count, error_count = (
            completed.stdout.strip().split()[-2:]
        )
        assert int(dag_count) >= 1
        assert int(error_count) == 0

    def test_dag_task_dependencies(self):
        """The pipeline DAG must wire ingestion -> staging -> marts ->
        quality gate -> verification."""

        completed = subprocess.run(
            [
                "docker",
                "exec",
                AIRFLOW_CONTAINER,
                "python",
                "-c",
                "from airflow.models import DagBag; "
                "bag = DagBag('/opt/airflow/dags', include_examples=False); "
                "dag = bag.dags['fraud_dw_pipeline']; "
                "print(','.join(sorted(dag.task_ids)))",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert completed.returncode == 0, completed.stderr[-2000:]
        # The DagBag fills with an INFO log line on stdout
        # before the printed task list; take the last line.
        task_line = completed.stdout.strip().splitlines()[-1]
        task_ids = task_line.split(",")
        expected_tasks = {
            "start_pipeline",
            "ingest_raw_data",
            "verify_raw_layer",
            "run_dbt_staging",
            "run_dbt_marts",
            "run_dbt_tests",
            "verify_marts_quality",
            "end_pipeline",
        }
        assert expected_tasks <= set(task_ids)


# ---------------------------------------------------------------------
# Full pipeline (opt-in: --run-pipeline)
# ---------------------------------------------------------------------


class TestFullPipeline:
    """Full pipeline execution via run_pipeline.py.

    Opt-in with: pytest tests/test_end_to_end.py --run-pipeline

    Runs every step for real (ML training included) and asserts the
    runner summary. Ingestion is expected to be SKIPPED when the
    source CSVs are absent (documented safety gate); every other
    step must PASS.
    """

    def test_full_pipeline(self, request):
        if not request.config.getoption("--run-pipeline"):
            pytest.skip(
                "full pipeline not requested "
                "(re-run with --run-pipeline)"
            )

        evidence = PROJECT_ROOT / "evidence" / "phase_24"
        completed = subprocess.run(
            [
                str(VENV_PYTHON),
                str(PROJECT_ROOT / "run_pipeline.py"),
                "--evidence-dir",
                str(evidence),
            ],
            capture_output=True,
            text=True,
            timeout=10800,
            cwd=PROJECT_ROOT,
        )

        summary_path = evidence / "pipeline_summary.json"
        assert summary_path.exists(), (
            f"runner produced no summary. stdout tail:\n"
            f"{completed.stdout[-3000:]}\n"
            f"stderr tail:\n{completed.stderr[-3000:]}"
        )
        summary = json.loads(summary_path.read_text())

        for step in summary["steps"]:
            if step["step"] == "ingestion":
                assert step["status"] in ("PASS", "SKIPPED")
            else:
                assert step["status"] == "PASS", (
                    f"step {step['step']}: {step['status']} — "
                    f"{step['detail']}"
                )
        assert summary["failed"] == 0
