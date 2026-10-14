# PHASE 27 — BENCHMARK METHODOLOGY

## 1. Purpose
Provide reproducible, non-destructive performance benchmarking for ingestion, dbt, ML, API, memory.

## 2. Principles
- Measure only when prerequisites exist; otherwise SKIP with reason.
- No fabricated numbers; historical values labeled as estimates if included.
- Expensive ops opt-in (--force-expensive).
- Do not modify existing DW tables.

## 3. Metrics
- Ingestion: rows, elapsed_s, rows_per_s
- dbt: total + per-model timing from run_results.json when available
- ML: fit time, optional tuning, metrics (ROC-AUC/AP/PR/RC/F1 as available)
- API: mean/p50/p95/p99, throughput, error rate, HTTP statuses
- Memory: RSS before/after, delta, peak if available.
