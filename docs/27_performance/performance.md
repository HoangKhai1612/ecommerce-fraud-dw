# PHASE 27 — PERFORMANCE BENCHMARKING & OPTIMIZATION

## 1. MỤC TIÊU

Đo lường và tối ưu hiệu năng toàn bộ pipeline:
- Ingestion speed
- dbt model build time
- ML training time
- API response time
- Memory usage

## 2. PERFORMANCE METRICS (HISTORICAL/ESTIMATES)

Các số liệu dưới đây là số liệu lịch sử/ước tính từ các phase trước. Chúng KHÔNG được coi là kết quả benchmark Phase 27 trừ khi được xác minh bằng lần chạy thực tế với bằng chứng trong evidence/phase_27/.

### 2.1 Ingestion Performance (Historical)
| Component | File | Rows | Time | Speed |
|-----------|------|------|------|-------|
| Ingestion | train_transaction.csv | 590,540 | 10.78s | 54,779 rows/s |
| Ingestion | train_identity.csv | 144,233 | 2.34s | 61,640 rows/s |
| **Total** | | **734,773** | **13.12s** | **~56,000 rows/s** |

*Historical note*: improvement noted (to_sql ~15+ min -> COPY ~10.78s). Requires verification under current environment.

### 2.2 dbt Performance (Historical/Estimates)
| Model | Type | Rows | Build Time |
|-------|------|------|-----------|
| stg_transactions | View | 590,540 | 0.13s |
| stg_identity | View | 144,233 | 0.12s |
| fact_transactions | Table | 590,540 | ~60s |
| dim_date | Table | ~183 | ~30s* |
| dim_device | Table | ~1,939 | ~5s* |
| dim_product | Table | ~5 | ~1s* |

*Note*: dim_date/dim_device counts adjusted to actual verified sizes where known; values marked ~ are estimates.

### 2.3 ML Training Performance (Historical/Estimates)
| Model | Training Time | CV Time | Best CV Score |
|-------|--------------|---------|---------------|
| Logistic Regression | ~5 min* | ~4 min* | ~0.92 AUC* |
| Random Forest | ~15 min* | ~10 min* | ~0.97 AUC* |
| XGBoost | ~10 min* | ~8 min* | ~0.99 AUC* |

*Not verified in Phase 27 runs. ML benchmarks are opt-in (--force-expensive) and must not overwrite artifacts.*

### 2.4 API Response Time (Historical/Estimates)
| Endpoint | Avg Response | 95th Percentile | Notes |
|----------|-------------|-----------------|-------|
| GET /health | ~2ms* | ~5ms* | Unverified |
| POST /predict | ~50ms* | ~100ms* | Requires valid payload (1014 features) |
| GET /transactions/{id} | ~30ms* | ~50ms* | Unverified |

## 3. PHASE 27 BENCHMARKING FRAMEWORK

Phase 27 provides safe, non-destructive benchmarking tools. All expensive operations are opt-in.

### 3.1 Scripts
- scripts/benchmark_utils.py — Common utilities (timing, env meta, JSON/CSV)
- scripts/benchmark_ingestion.py — Ingestion benchmark (safe default: SKIPPED)
- scripts/benchmark_dbt.py — dbt benchmark (safe default: SKIPPED)
- scripts/benchmark_ml.py — ML benchmark (opt-in via --force-expensive)
- scripts/benchmark_api.py — API benchmark (safe default: SKIPPED; requires running API)
- scripts/profile_memory.py — Memory profiler (uses psutil if available)
- scripts/run_phase27.py — Orchestrator (--help, --preflight, --stages, --force-expensive)

### 3.2 Execution (PowerShell)
`powershell
Set-Location "C:\Users\Administrator\Documents\ecommerce-fraud-dw"
="C:\Users\Administrator\Documents\ecommerce-fraud-dw"

# Help
python scripts/run_phase27.py --help

# Unit tests
python -m pytest tests/test_phase27.py -v

# Run safe stages (preflight)
python scripts/run_phase27.py --preflight

# Run specific safe stage if applicable
python scripts/profile_memory.py
python scripts/benchmark_api.py --base-url http://localhost:8000  # only if API running
`

## 4. ACTUAL RESULTS (PHASE 27)

| Stage | Status | Details |
|-------|--------|---------|
| Utils/Orchestrator | COMPLETED | Aggregate summary written to evidence/phase_27/aggregate_summary.json |
| Memory | COMPLETED | evidence/phase_27/memory_profile.json (psutil available) |
| API | SKIPPED | evidence/phase_27/api_benchmark.json — No running API service in this environment |
| Ingestion | SKIPPED | Default safe mode (no isolated destructive ops) |
| dbt | SKIPPED | Requires explicit model selection/preflight |
| ML | SKIPPED | Opt-in via --force-expensive to avoid heavy training |

Actual measurements from Phase 27 runs: see evidence/phase_27/*.json. No fabricated performance numbers added.

## 5. METHODOLOGY
See docs/27_performance/benchmark_methodology.md for detailed metric definitions, reproducibility, and safety guarantees.

## 6. SECURITY & SAFETY
- No existing DW tables dropped/truncated/replaced during benchmarking
- Expensive operations opt-in
- No secrets/credentials in evidence
- API benchmark validates schema/HTTP status when run
- Historical values clearly labeled; measured values only from actual runs

## 7. REFERENCES
- Previous: [PHASE 26 — Troubleshooting](../26_troubleshooting/troubleshooting.md)
- Methodology: [benchmark_methodology.md](benchmark_methodology.md)
- Evidence: evidence/phase_27/

*Updated: 2026-10-14 | Version: 2.0 (Phase 27 framework)*
