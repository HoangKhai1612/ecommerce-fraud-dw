# Phase 31 — Architecture

## Overview

The Integrated Fraud Detection Testing Platform is a full-stack web UI that lets
users run real XGBoost fraud inference through a FastAPI backend, persist results
to PostgreSQL, and get AI explanations via Ollama. All components use real
services — no mocks, no static-only UI.

## Component Diagram

```
Browser (web/, port 5173)
    |
    | HTTP (Vite proxy /api -> :8000)
    v
FastAPI (api/, port 8000)
    |
    +-- Real XGBoost inference (ml/models/xgboost.pkl, 1014 features)
    +-- PostgreSQL: marts.web_test_history (prediction history)
    +-- AI Assistant (port 8001)  -->  Ollama (port 11434, llama3)  [fallback]
```

## Data Flow

### Prediction (Transaction Testing)
1. User submits a transaction via mode A (IEEE-CIS form/CSV) or mode B
   (ecommerce-sim simplified form).
2. Frontend POSTs to `/predictions` with `{ mode, transaction }`.
3. Backend runs real `InferencePipeline.predict_proba()` (XGBoost).
4. Result is persisted to `marts.web_test_history` and returned (201).
5. Frontend shows probability, label, risk level, and offers "AI explain".

### Prediction History
1. Frontend GETs `/predictions` with optional filters (`input_mode`,
   `is_fraud_predicted`, `min/max_probability`, date range) and pagination
   (`limit`, `offset`).
2. Backend queries `marts.web_test_history` and returns paginated items.

### AI Explanation
1. Frontend POSTs to `/ai/chat` with `{ question }` and optional
   `?prediction_id=` query param.
2. If `prediction_id` is given, backend fetches the real record from
   `marts.web_test_history` and builds context from the actual XGBoost result.
3. `AIService.explain()` tries AI Assistant (port 8001, 20s timeout), then
   falls back to direct Ollama (port 11434, 90s timeout).
4. Answer is saved back to `marts.web_test_history` (ai_explanation,
   ai_available, ai_explanation_at).
5. If both AI services are unavailable, `ai_available=false` and the prediction
   remains valid — XGBoost results are never affected.

### System Status
1. Frontend GETs `/system/status` (polls every 15s).
2. Backend reports status for: API (always ok), XGBoost model, PostgreSQL,
   AI Assistant, Ollama. AI/OLLAMA being down does not disable prediction.

## Database Table

`marts.web_test_history` — idempotent DDL in `sql/31_web_test_history.sql` and
auto-created by `api.database.ensure_history_table()` on API startup.

Key columns: `prediction_id` (UUID PK), `transaction_id`, `model_version`,
`input_mode`, `input_payload` (JSONB), `is_fraud_predicted`, `fraud_probability`,
`threshold`, `predicted_at`, `ai_explanation`, `ai_explanation_at`,
`ai_available`, `status`.

Indexes on `predicted_at`, `input_mode`, `is_fraud_predicted`, `transaction_id`.

## Security Notes

- Rate limiting: 10/min on `/predictions`, `/ai/chat`; 5/min on explain.
- AI explanations are advisory only — they never override XGBoost scores.
- AI is explicitly instructed not to invent feature importance or SHAP values
  unless actual computation backs them.
- No secrets or credentials in the frontend; all calls go through FastAPI.
