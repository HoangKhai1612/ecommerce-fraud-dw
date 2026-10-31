# Phase 31 — API Reference

Base URL: `http://localhost:8000` (or `http://host.docker.internal:8000` from
containers). OpenAPI schema: `GET /openapi.json`, UI: `/docs`.

## Endpoints

### POST /predictions
Run real XGBoost inference and persist the result.

Request:
```json
{
  "mode": "ieee-cis",
  "transaction": {
    "transaction_id": 12345,
    "transaction_dt": 86400,
    "transaction_amt": 150.75,
    "product_cd": "W",
    "card1": 1001,
    "card4": "visa",
    "device_type": "mobile"
  }
}
```

Response (201): `PredictionRecord` — includes `prediction_id` (UUID),
`fraud_probability`, `is_fraud_predicted`, `risk_level`, `message`,
`model_version`, `predicted_at`, `ai_available`, `status`.

Errors: 400 (missing required fields), 422 (validation), 503 (model/DB
unavailable). Rate limit: 10/min.

### GET /predictions/{prediction_id}
Get one persisted prediction record by UUID.

Response (200): `PredictionDetail` — full record including `input_payload`,
`ai_explanation`, `ai_explanation_at`.

Errors: 404 (not found), 503 (DB unavailable).

### GET /predictions
List prediction history with filters and pagination.

Query params: `input_mode`, `is_fraud_predicted` (0/1), `min_probability`,
`max_probability`, `from_predicted_at`, `to_predicted_at`, `limit` (1-200),
`offset` (>=0).

Response (200): `PredictionsListResponse` — `{ items, total, limit, offset }`.

Errors: 422 (invalid limit), 503 (DB unavailable).

### POST /predictions/{prediction_id}/explain
Generate an AI explanation for a real prediction.

Request body (optional): `{ "question": "..." }`

Response (200): `ExplainResponse` — `{ prediction_id, answer, ai_available,
source }` where `source` is `ai-assistant`, `ollama-direct`, or `unavailable`.

Errors: 404 (not found), 503 (DB unavailable). Rate limit: 5/min.

### POST /ai/chat
Chat with the AI Assistant.

Request body: `{ "question": "..." }`

Query param (optional): `?prediction_id=<uuid>` for context-bound explanation.

Response (200): `ExplainResponse`. For general chat (no prediction_id),
`prediction_id` is null.

Errors: 400 (missing/empty question), 404 (prediction not found when context
given), 503 (DB unavailable). Rate limit: 10/min.

### GET /system/status
System status for the web dashboard.

Response (200): `SystemStatusResponse` — `{ api, model, database, ai, ollama }`
where each service has `{ name, status ("ok"|"degraded"|"unavailable"),
detail }`.

### GET /transactions/sample
Read-only sample transactions from `marts.fact_transactions`.

Query param: `limit` (1-20, default 5).

Response (200): array of `TransactionResponse` — `{ transaction_id, is_fraud,
transaction_amt, product_cd, transaction_dt }`.

### GET /health / GET /ready / GET /
Standard health, readiness, and root endpoints.

## Schemas

All request/response schemas are defined in `api/models.py` (Phase 31 section)
and exposed via `/openapi.json`.

## Notes

- The model is never mocked. If XGBoost artifacts cannot be loaded, the
  endpoint returns 503.
- AI failure never invalidates a prediction. `ai_available=false` means the
  XGBoost result is still valid; only the explanation is missing.
- `marts.web_test_history` is separate from `marts.predictions` (batch layer).
  Web test history is not mixed with batch predictions.
