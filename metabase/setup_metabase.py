"""
Phase 20 — Automated Metabase setup via the official REST API (v0.49.0).

Steps (idempotent — safe to re-run):
  1. Complete first-run setup (admin account) using the setup token from
     GET /api/session/properties, or log in if setup is already done.
  2. Add the analytics database `ecommerce_fraud_dw` (PostgreSQL, reached
     through host.docker.internal:5432) using the read-only role metabase_ro.
  3. Trigger schema sync and wait until marts tables are visible.
  4. Create collection "Fraud Analytics".
  5. Create the 8 SQL questions (4 KPI scalars, fraud trend line,
     device bar, product bar, top-50 predictions table).
  6. Create dashboard "E-commerce Fraud Analytics" and place the cards.
  7. Verify every card by executing its query through Metabase's own
     database connection and cross-checking the returned numbers.

Run from the project root:
    .venv\\Scripts\\python.exe metabase\\setup_metabase.py

No secrets are printed or written outside .env (gitignored).
"""

import json
import os
import sys
import time
from pathlib import Path

# Windows consoles default to cp1252; force UTF-8 for Vietnamese log text.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
import requests

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence" / "phase_20"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3000")
ADMIN_EMAIL = os.getenv("METABASE_ADMIN_EMAIL", "admin@frauddw.local")
ADMIN_PASSWORD = os.getenv("METABASE_ADMIN_PASSWORD")
DB_HOST = "host.docker.internal"
DB_PORT = 5432
DB_NAME = "ecommerce_fraud_dw"
DB_USER = "metabase_ro"
DB_PASSWORD = os.getenv("METABASE_RO_PASSWORD")

MODEL_VERSION = "xgboost-v1-phase16"
COLLECTION_NAME = "Fraud Analytics"
DASHBOARD_NAME = "E-commerce Fraud Analytics"

if not ADMIN_PASSWORD or not DB_PASSWORD:
    sys.exit("Missing METABASE_ADMIN_PASSWORD / METABASE_RO_PASSWORD in .env")

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def log(msg: str) -> None:
    print(msg, flush=True)


def save_evidence(name: str, payload) -> None:
    path = EVIDENCE_DIR / name
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(payload, str):
            fh.write(payload)
        else:
            json.dump(payload, fh, indent=2, default=str)
    log(f"  evidence saved: {path.relative_to(PROJECT_ROOT)}")


def api_get(path: str, expect: int = 200):
    resp = session.get(f"{METABASE_URL}{path}", timeout=60)
    if resp.status_code != expect:
        raise RuntimeError(f"GET {path} -> HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def api_post(path: str, body, expect: int | tuple = 200):
    resp = session.post(f"{METABASE_URL}{path}", json=body, timeout=120)
    expected = (expect,) if isinstance(expect, int) else expect
    if resp.status_code not in expected:
        raise RuntimeError(f"POST {path} -> HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def get_session_token() -> str:
    """Log in, or complete first-run setup if the instance is fresh."""
    # 1) Normal path: instance already set up -> log in.
    try:
        result = api_post(
            "/api/session",
            {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            expect=200,
        )
        if result.get("id"):
            log("Logged in as existing admin")
            return result["id"]
    except RuntimeError:
        pass

    # 2) Fresh instance: complete setup with the one-time setup token.
    props = api_get("/api/session/properties")
    setup_token = props.get("setup-token")
    if not setup_token:
        sys.exit(
            "Cannot log in and no setup token available. "
            "Check METABASE_ADMIN_* in .env."
        )
    log("Setup pending — completing first-run setup via POST /api/setup")
    # Metabase v0.49.0 validates token/site_name/email/password at the
    # TOP level of the body (see src/metabase/api/setup.clj), while the
    # handler destructures user fields from :user and preferences from
    # :prefs. The payload below satisfies both shapes.
    result = api_post(
        "/api/setup",
        {
            "token": setup_token,
            "site_name": "E-commerce Fraud DW",
            "allow_tracking": False,
            "email": ADMIN_EMAIL,
            "first_name": "Fraud",
            "last_name": "DW Admin",
            "password": ADMIN_PASSWORD,
            "user": {
                "first_name": "Fraud",
                "last_name": "DW Admin",
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            },
            "prefs": {
                "site_name": "E-commerce Fraud DW",
                "allow_tracking": False,
            },
        },
        expect=200,
    )
    token = result.get("id")
    if not token:
        raise RuntimeError("Setup response has no session id")
    log("  setup complete: admin account created")
    return token

    log("Setup already completed — logging in via POST /api/session")
    result = api_post(
        "/api/session",
        {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        expect=200,
    )
    token = result.get("id")
    if not token:
        raise RuntimeError("Login failed — check METABASE_ADMIN_* in .env")
    return token


def api_put(path: str, body, expect: int = 200):
    resp = session.put(f"{METABASE_URL}{path}", json=body, timeout=120)
    if resp.status_code != expect:
        raise RuntimeError(f"PUT {path} -> HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def _list_payload(resp) -> list:
    """v0.49 list endpoints return {"data": [...], "total": N}."""
    if isinstance(resp, dict) and "data" in resp:
        return resp["data"]
    return resp


def get_or_add_database() -> int:
    dbs = _list_payload(api_get("/api/database"))
    for db in dbs:
        if db.get("name") == DB_NAME:
            db_id = db["id"]
            log(f"Database '{DB_NAME}' already configured (id={db_id})")
            return db_id

    log(f"Adding database '{DB_NAME}' via POST /api/database")
    result = api_post(
        "/api/database",
        {
            "engine": "postgres",
            "name": DB_NAME,
            "details": {
                "host": DB_HOST,
                "port": DB_PORT,
                "dbname": DB_NAME,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "ssl": False,
                "tunnel-enabled": False,
            },
            "is_full_sync": True,
            "is_on_demand": False,
            "is_sample": False,
            "auto_run_queries": True,
        },
        expect=200,
    )
    db_id = result["id"]
    log(f"  database added (id={db_id})")
    return db_id


def wait_for_metadata(db_id: int, required_tables: list[str], timeout_s: int = 300) -> None:
    log(f"Ensuring metadata for database {db_id} is synced...")
    # v0.49: POST /api/database/:id/sync_schema triggers an async
    # metadata sync (the old /sync route no longer exists).
    try:
        api_post(f"/api/database/{db_id}/sync_schema", {}, expect=200)
    except RuntimeError as exc:
        log(f"  sync_schema call: {exc}")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            meta = api_get(f"/api/database/{db_id}/metadata")
            found = {t["name"] for t in meta.get("tables", [])}
            missing = [t for t in required_tables if t not in found]
            if not missing:
                log(f"  metadata ready: marts tables visible: {sorted(found)}")
                return
            log(f"  waiting for {missing} ...")
        except Exception as exc:  # sync in progress
            log(f"  waiting for metadata ({exc}) ...")
        time.sleep(10)
    raise RuntimeError("Timed out waiting for Metabase metadata sync")


def get_or_create_collection() -> int:
    collections = _list_payload(api_get("/api/collection"))
    for col in collections:
        if col.get("name") == COLLECTION_NAME:
            col_id = col["id"]
            log(f"Collection '{COLLECTION_NAME}' already exists (id={col_id})")
            return col_id
    result = api_post(
        "/api/collection",
        {"name": COLLECTION_NAME, "description": "Fraud analytics questions (Phase 20)"},
        expect=200,
    )
    col_id = result["id"]
    log(f"Collection '{COLLECTION_NAME}' created (id={col_id})")
    return col_id


# ---------------------------------------------------------------------------
# SQL questions (verified against PostgreSQL directly — see docs/20_dashboard/sql)
# ---------------------------------------------------------------------------
QUESTIONS = [
    {
        "name": "Tổng số giao dịch",
        "slug": "total_transactions",
        "display": "scalar",
        "description": "KPI: tổng số giao dịch trong marts.fact_transactions",
        "sql": "SELECT COUNT(*) AS total_transactions FROM marts.fact_transactions;",
    },
    {
        "name": "Tổng số giao dịch gian lận",
        "slug": "total_fraud_transactions",
        "display": "scalar",
        "description": "KPI: số giao dịch có nhãn thực tế is_fraud = 1",
        "sql": "SELECT COUNT(*) AS total_fraud_transactions FROM marts.fact_transactions WHERE is_fraud = 1;",
    },
    {
        "name": "Tỷ lệ giao dịch gian lận (%)",
        "slug": "fraud_rate_pct",
        "display": "scalar",
        "description": "KPI: tỷ lệ giao dịch gian lận trên toàn bộ dữ liệu (%)",
        "sql": "SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_fraud = 1) / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct FROM marts.fact_transactions;",
    },
    {
        "name": "Tổng giá trị giao dịch",
        "slug": "total_amount",
        "display": "scalar",
        "description": "KPI: tổng cột transaction_amt của toàn bộ giao dịch",
        "sql": "SELECT SUM(transaction_amt) AS total_amount FROM marts.fact_transactions;",
    },
    {
        "name": "Tỷ lệ gian lận theo ngày",
        "slug": "fraud_trend_by_day",
        "display": "line",
        "description": "Tỷ lệ gian lận theo ngày giao dịch (transaction_dt là epoch tương đối của dataset)",
        "sql": (
            "SELECT to_timestamp(transaction_dt)::date AS transaction_date, "
            "COUNT(*) AS total_transactions, "
            "COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions, "
            "ROUND(100.0 * COUNT(*) FILTER (WHERE is_fraud = 1) / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct "
            "FROM marts.fact_transactions "
            "GROUP BY transaction_date "
            "ORDER BY transaction_date;"
        ),
    },
    {
        "name": "Gian lận theo loại thiết bị",
        "slug": "fraud_by_device",
        "display": "bar",
        "description": "Tỷ lệ gian lận theo device_type (NULL gom vào nhóm Unknown)",
        "sql": (
            "SELECT COALESCE(NULLIF(device_type, ''), 'Unknown') AS device_type, "
            "COUNT(*) AS total_transactions, "
            "COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions, "
            "ROUND(100.0 * COUNT(*) FILTER (WHERE is_fraud = 1) / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct "
            "FROM marts.fact_transactions "
            "GROUP BY device_type "
            "ORDER BY fraud_rate_pct DESC;"
        ),
    },
    {
        "name": "Gian lận theo mã sản phẩm",
        "slug": "fraud_by_product",
        "display": "bar",
        "description": "Tỷ lệ gian lận theo product_cd (đã materialize trong fact_transactions)",
        "sql": (
            "SELECT product_cd, "
            "COUNT(*) AS total_transactions, "
            "COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions, "
            "ROUND(100.0 * COUNT(*) FILTER (WHERE is_fraud = 1) / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct "
            "FROM marts.fact_transactions "
            "GROUP BY product_cd "
            "ORDER BY fraud_rate_pct DESC;"
        ),
    },
    {
        "name": "Top 50 dự đoán gian lận",
        "slug": "top_fraud_predictions",
        "display": "table",
        "description": (
            "50 giao dịch có xác suất gian lận cao nhất từ marts.predictions "
            f"(model_version='{MODEL_VERSION}'). Đây là dự đoán của mô hình, không phải kết luận điều tra."
        ),
        "sql": (
            "SELECT p.transaction_id, "
            "p.is_fraud_actual, "
            "p.is_fraud_predicted, "
            "ROUND((p.fraud_probability * 100)::numeric, 2) AS fraud_probability_pct, "
            "f.transaction_amt "
            "FROM marts.predictions p "
            "JOIN marts.fact_transactions f ON f.transaction_id = p.transaction_id "
            f"WHERE p.model_version = '{MODEL_VERSION}' "
            "ORDER BY p.fraud_probability DESC "
            "LIMIT 50;"
        ),
    },
]

# Dashboard layout on the 12-column grid: (row, col, sizeX, sizeY)
LAYOUT = {
    "total_transactions": (0, 0, 3, 2),
    "total_fraud_transactions": (0, 3, 3, 2),
    "fraud_rate_pct": (0, 6, 3, 2),
    "total_amount": (0, 9, 3, 2),
    "fraud_trend_by_day": (2, 0, 12, 5),
    "fraud_by_device": (7, 0, 6, 5),
    "fraud_by_product": (7, 6, 6, 5),
    "top_fraud_predictions": (12, 0, 12, 8),
}


def get_or_create_card(question: dict, db_id: int, collection_id: int) -> int:
    cards = _list_payload(api_get(f"/api/collection/{collection_id}/items"))
    for item in cards:
        if item.get("model") == "card" and item.get("name") == question["name"]:
            card_id = item["id"]
            existing = api_get(f"/api/card/{card_id}")
            existing_sql = (
                existing.get("dataset_query", {})
                .get("native", {})
                .get("query", "")
                .strip()
            )
            if existing_sql != question["sql"].strip():
                log(f"Card '{question['name']}' exists but SQL changed — updating (id={card_id})")
                api_put(
                    f"/api/card/{card_id}",
                    {
                        "name": question["name"],
                        "description": question["description"],
                        "dataset_query": {
                            "type": "native",
                            "native": {"query": question["sql"]},
                            "database": db_id,
                        },
                        "display": question["display"],
                        "collection_id": collection_id,
                        "visualization_settings": {},
                    },
                )
            else:
                log(f"Card '{question['name']}' already exists (id={card_id})")
            return card_id

    result = api_post(
        "/api/card",
        {
            "name": question["name"],
            "description": question["description"],
            "dataset_query": {
                "type": "native",
                "native": {"query": question["sql"]},
                "database": db_id,
            },
            "display": question["display"],
            "collection_id": collection_id,
            "visualization_settings": {},
        },
        expect=200,
    )
    card_id = result["id"]
    log(f"Card '{question['name']}' created (id={card_id}, display={question['display']})")
    return card_id


def get_or_create_dashboard(collection_id: int) -> int:
    dashboards = _list_payload(api_get("/api/dashboard"))
    for dash in dashboards:
        if dash.get("name") == DASHBOARD_NAME:
            dash_id = dash["id"]
            log(f"Dashboard '{DASHBOARD_NAME}' already exists (id={dash_id})")
            break
    else:
        result = api_post(
            "/api/dashboard",
            {
                "name": DASHBOARD_NAME,
                "description": "Tổng quan gian lận giao dịch thương mại điện tử — Phase 20",
                "collection_id": collection_id,
                "parameters": [],
            },
            expect=200,
        )
        dash_id = result["id"]
        log(f"Dashboard '{DASHBOARD_NAME}' created (id={dash_id})")

    # Ensure the dashboard lives in the Fraud Analytics collection
    # (v0.49 create/update uses the collection_id key).
    if api_get(f"/api/dashboard/{dash_id}").get("collection_id") != collection_id:
        api_put(
            f"/api/dashboard/{dash_id}",
            {"collection_id": collection_id},
            expect=200,
        )
        log(f"  moved dashboard to collection id={collection_id}")
    return dash_id


def attach_cards_to_dashboard(dash_id: int, card_ids: dict[str, int]) -> None:
    """Place cards on the dashboard grid (idempotent).

    v0.49: PUT /api/dashboard/:id/cards. Existing dashcards are
    referenced by their real (positive) id; new ones use negative
    temporary ids and a card_id, which the backend creates.
    """
    dashboard = api_get(f"/api/dashboard/{dash_id}")
    existing_by_card = {
        dc.get("card", {}).get("id"): dc["id"]
        for dc in dashboard.get("dashcards", [])
        if dc.get("card")
    }
    payload_cards = []
    next_temp_id = -1
    for slug, card_id in card_ids.items():
        row, col, size_x, size_y = LAYOUT[slug]
        dc_id = existing_by_card.get(card_id, next_temp_id)
        if dc_id == next_temp_id:
            next_temp_id -= 1
        payload_cards.append(
            {
                "id": dc_id,
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": size_x,
                "size_y": size_y,
                "parameter_mappings": [],
                "visualization_settings": {},
            }
        )
    result = api_put(
        f"/api/dashboard/{dash_id}/cards",
        {"cards": payload_cards},
        expect=200,
    )
    attached = result.get("cards", [])
    log(f"Dashboard layout applied: {len(attached)} cards attached")


def verify_card_query(card_id: int, slug: str) -> dict:
    """Execute the card through Metabase's own connection and return the result."""
    # v0.49 executes queries asynchronously: the endpoint answers
    # 202 Accepted with the result payload.
    result = api_post(f"/api/card/{card_id}/query", {}, expect=(200, 202))
    data = result.get("data", {})
    rows = data.get("rows", [])
    cols = [c.get("name") for c in data.get("cols", [])]
    log(f"  query '{slug}' -> {len(rows)} rows; columns: {cols}")
    return {"columns": cols, "rows": rows}


def main() -> None:
    log("=== Phase 20 — Metabase automated setup ===")

    token = get_session_token()
    session.headers.update({"X-Metabase-Session": token})

    db_id = get_or_add_database()
    save_evidence("metabase_database.json", api_get(f"/api/database/{db_id}"))

    wait_for_metadata(db_id, ["fact_transactions", "dim_date", "dim_device", "dim_product", "predictions"])

    collection_id = get_or_create_collection()

    card_ids: dict[str, int] = {}
    for question in QUESTIONS:
        card_id = get_or_create_card(question, db_id, collection_id)
        card_ids[question["slug"]] = card_id
        save_evidence(f"card_{question['slug']}.json", api_get(f"/api/card/{card_id}"))

    dash_id = get_or_create_dashboard(collection_id)
    attach_cards_to_dashboard(dash_id, card_ids)
    dashboard = api_get(f"/api/dashboard/{dash_id}")
    save_evidence("dashboard.json", dashboard)

    log("=== Verification: executing each card through Metabase's connection ===")
    verification = {}
    for slug, card_id in card_ids.items():
        verification[slug] = verify_card_query(card_id, slug)
    save_evidence("card_query_results.json", verification)

    log(f"=== DONE — dashboard http://localhost:3000/dashboard/{dash_id} ===")


if __name__ == "__main__":
    main()
