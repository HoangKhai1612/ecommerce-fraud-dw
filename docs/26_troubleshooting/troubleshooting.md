# PHASE 26 — Troubleshooting & Failure Engineering

## 1. Mục tiêu
Ghi chép các lỗi thường gặp và cách khắc phục:
- Environment issues
- Pipeline failures
- Performance issues
- Security issues

## 2. ISSUE DATABASE

### ISS-001 — PostgreSQL port 5432 conflict
- ID: ISS-001
- Severity: HIGH
- Component: PostgreSQL/Docker
- Symptoms: connection to server at "localhost", port 5432 failed: FATAL
- Cause hypothesis: PostgreSQL local chạy trùng port với Docker hoặc service khác
- Evidence collection: 
etstat -ano | findstr 5432 (Windows), ss -tlnp | grep 5432
- Diagnosis steps: Check port listeners, identify PID
- Safe fix: Identify process and stop safely (	askkill /PID <pid> /F only if safe); or change PGPORT in .env if appropriate. Never drop data.
- Verification after fix: SELECT 1 succeeds
- Rollback: Restart service if unintended
- Notes: Prevention; may be BLOCKED if cannot stop system service

### ISS-002 — dbt schema concatenation
- ID: ISS-002
- Severity: MEDIUM
- Component: dbt
- Symptoms: dbt tạo schema aw_staging thay vì staging
- Cause hypothesis: dbt default macro nối {target_schema}_{custom_schema}
- Evidence collection: dbt/logs/dbt.log, dbt_project.yml, macros
- Diagnosis steps: Review generate_schema_name macro behavior
- Safe fix: Override default__generate_schema_name in macros/schema_override.sql preserving existing logic
- Verification: dbt debug, dbt run --select <model> produces expected schema names
- Rollback: Restore macro backup
- Notes: Avoid broad macro changes

### ISS-003 — protobuf incompatible with Python 3.14
- ID: ISS-003
- Severity: MEDIUM
- Component: Python dependencies
- Symptoms: TypeError: Metaclasses with custom tp_new are not supported
- Cause hypothesis: protobuf 4.x không tương thích Python 3.14
- Evidence collection: pip list, traceback, requirements.txt
- Diagnosis steps: Check protobuf version, reproduce import error
- Safe fix: Upgrade protobuf to compatible version (avoid mass version bumps). Test affected imports
- Verification: Imports succeed, no new warnings
- Rollback: Pin to previous version if regression
- Notes: Document compatibility constraint

### ISS-004 — File encoding error
- ID: ISS-004
- Severity: LOW
- Component: Ingestion
- Symptoms: UnicodeDecodeError: 'utf-8' codec can't decode byte
- Cause hypothesis: CSV encoding not UTF-8
- Evidence collection: File BOM/header bytes, traceback
- Diagnosis steps: Detect encoding or try latin-1/utf-8-sig
- Safe fix: Specify encoding (e.g. encoding='latin-1' or errors='replace' with care)
- Verification: File reads without decode error, row counts reasonable
- Rollback: Revert change
- Notes: Prefer explicit encoding; log detected encoding if used

### ISS-005 — Memory error loading large CSV
- ID: ISS-005
- Severity: MEDIUM
- Component: Ingestion
- Symptoms: MemoryError: Unable to allocate khi load CSV lớn
- Cause hypothesis: File quá lớn để nạp toàn bộ vào memory
- Evidence collection: File size, RAM usage, traceback, logs/ingestion.log
- Diagnosis steps: Check available memory, file size, chunking feasibility
- Safe fix: Use chunksize, iterator, dtypes optimization; avoid global memory changes
- Verification: Processing completes without OOM, row counts match
- Rollback: Revert approach if fails
- Notes: Trade-off memory/time; document chunk size

### ISS-006 — Ollama model not responding
- ID: ISS-006
- Severity: MEDIUM
- Component: Ollama/AI Assistant
- Symptoms: Connection refused khi gọi Ollama API
- Cause hypothesis: Ollama container chưa khởi động hoặc model chưa được pull
- Evidence collection: docker compose ps, curl http://localhost:11434/api/tags, ollama logs
- Diagnosis steps: Check service health, port 11434, model availability
- Safe fix: Start ollama (docker compose up -d ollama), pull required model if missing. Do not disable SQL validator.
- Verification: API responds, required model available
- Rollback: N/A (reversible)
- Notes: AI Assistant must remain within configured scope and security constraints

### ISS-007 — XGBoost tree_method warning/deprecation
- ID: ISS-007
- Severity: LOW
- Component: ML
- Symptoms: UserWarning: tree_method is deprecated or related warnings
- Cause hypothesis: Version-specific API changes
- Evidence collection: Warnings in logs/ml_train.log, xgboost version
- Diagnosis steps: Review xgboost API, check compatibility
- Safe fix: Use supported 	ree_method without changing model architecture/artifacts evaluation criteria
- Verification: Warnings reduced, training runs, metrics in expected range
- Rollback: Revert param change
- Notes: Do not change hyperparameters of approved models just for speed

### ISS-008 — SQLAlchemy connection pool exhausted
- ID: ISS-008
- Severity: MEDIUM
- Component: API/DB
- Symptoms: TimeoutError: QueuePool limit overflow
- Cause hypothesis: Connections not closed properly, pool size too small
- Evidence collection: API logs, DB connection counts, traceback
- Diagnosis steps: Check session/connection lifecycle, concurrency
- Safe fix: Ensure proper close/dispose, context managers, appropriate pool config, timeouts
- Verification: No pool exhaustion under expected load, connections released
- Rollback: Revert config changes
- Notes: Tune conservatively

### ISS-009 — Docker disk space full
- ID: ISS-009
- Severity: HIGH
- Component: Docker
- Symptoms: Docker stuck at "Starting", build fails with no space
- Cause hypothesis: Images/containers/volumes consuming disk
- Evidence collection: docker system df, disk usage
- Diagnosis steps: Identify reclaimable space; distinguish volumes with data
- Safe fix: Prune unused resources carefully. **WARNING:** Never run docker system prune -a --volumes. Only prune safe targets. Prefer targeted cleanup. Never drop project DB volumes.
- Verification: Sufficient disk space, services start normally
- Rollback: N/A if removing unused artifacts
- Notes: Strictly follow project rule

### ISS-010 — Airflow DAG/task failure
- ID: ISS-010
- Severity: HIGH
- Component: Airflow
- Symptoms: DAG parse errors, task failures, sensor timeouts
- Cause hypothesis: Dependency/env issues, DB connection, import errors, misconfiguration
- Evidence collection: Airflow UI logs, airflow/logs/, scheduler logs, DAG parsing errors
- Diagnosis steps: Check DAG syntax, connections, variables, requirements, DB access
- Safe fix: Fix syntax/config without changing business logic; retry with limits; ensure idempotency
- Verification: DAG loads successfully, tasks complete with expected state
- Rollback: Revert changes
- Notes: Fail-safe, retry bounded

### ISS-011 — FastAPI model loading/readiness failure
- ID: ISS-011
- Severity: HIGH
- Component: FastAPI/ML
- Symptoms: Startup fails loading models, /health/readiness unhealthy, model files missing/corrupt
- Cause hypothesis: Missing model artifacts, feature schema mismatch, path issues
- Evidence collection: API logs, ml/models/ contents, feature_columns.json, training_results.json, traceback
- Diagnosis steps: Verify required model files exist (logistic_regression.pkl, random_forest.pkl, xgboost.pkl, scalers, feature_columns.json)
- Safe fix: Ensure correct project paths; validate readable. Do not auto-download or replace approved models. Load lazily with proper error handling
- Verification: API starts, health/readiness reflects true state, predictions work
- Rollback: Restore artifacts if replaced
- Notes: Readiness must reflect actual capability

### ISS-012 — AI Assistant SQL validation/security failure
- ID: ISS-012
- Severity: CRITICAL
- Component: AI Assistant/Security
- Symptoms: SQL validation blocks legitimate queries incorrectly, or bypass attempted; unexpected data access
- Cause hypothesis: Validator rules misconfigured, scope change
- Evidence collection: ai_assistant logs, validation results, request context (no secrets)
- Diagnosis steps: Review SQL validator, read-only scope, timeouts, row limits. Verify rules unchanged
- Safe fix: Correct validator logic without disabling protections. Maintain read-only permissions, row limits, SQL constraints
- Verification: Security constraints enforced, authorized queries pass, unauthorized blocked
- Rollback: Revert validator changes
- Notes: **MUST NOT** disable SQL validator, DB read-only perms, timeouts, or row limits


## 3. LOGGING

Tất cả components phải có logging chuẩn hóa:
- Timestamp, log level, logger name, message, exception traceback khi có lỗi
- Console handler và RotatingFileHandler (UTF-8, maxBytes=5MB, backupCount=5)
- Tránh duplicate handlers; không lộ secrets
- Ưu tiên stdout/stderr trong container; dùng file logging khi phù hợp

Xem src/logging_config.py để tham khảo.


## 4. FALLBACK STRATEGIES

| Component | Trigger | Allowed Action | Not Allowed | Risk | Verification | Return to Normal |
|---|---|---|---|---|---|---|
| PostgreSQL | Connection failure | Retry with backoff (limited), use cached read-only state if available | Drop/create schema/tables, modify data | Data loss/corruption | Connectivity restored, SELECT 1 works | Auto/manual after stability confirmed |
| Ingestion | CSV read/DB write error | Chunking, skip bad lines with logging (if designed), retry limited times | Bulk destructive ops | Partial ingestion | Row counts match, constraints ok | After fix validated |
| dbt | Compilation/db error | Fix config/macros safely, run targeted models | Drop schemas, full refresh without review | Schema changes | dbt debug passes, tests still relevant | After successful run |
| Airflow | Task failure | Bounded retry, fail to alert state | Force re-run destructive tasks without idempotency check | Duplicate data | Task completes cleanly | After root cause fixed |
| XGBoost | Training/load failure | Use alternative model if artifact valid; check versions | Replace approved artifacts without verification | Wrong predictions | Load succeeds, metrics comparable | After validation |
| FastAPI | Model load failure | Return 503 with proper state, lazy load | False healthy | Misleading clients | Readiness reflects reality | After models loadable |
| Ollama | Unavailable | Degrade gracefully, return clear error | Disable security features | Feature loss only | Service reachable or graceful error | After service up |
| AI Assistant | SQL/security issue | Reject unsafe queries, keep protections | Disable validator/row limits/timeouts/read-only | Data exposure | Constraints enforced | After fix verified |


## 5. PERFORMANCE TROUBLESHOOTING

Các công cụ đo được ưu tiên (không giả định speedup):
- Ingestion: thời gian, số dòng xử lý, peak memory
- dbt: thời gian compile/run, threads
- ML: thời gian huấn luyện, SHAP sample size, metrics
- API: latency, connection pool behavior
- Ollama: response latency
Lưu cấu hình chạy, dữ liệu đầu vào, số lần lặp và kết quả thực đo. Không đưa tỷ lệ tăng tốc mặc định khi chưa đo thực tế.

## 6. CHECKLIST
- [ ] Python version và deps
- [ ] Docker/daemon
- [ ] PostgreSQL connectivity (SELECT 1)
- [ ] dbt project/profile
- [ ] Airflow, FastAPI, Ollama
- [ ] Model artifacts + feature columns
- [ ] Disk/memory
- [ ] Logs locations và rotation
- [ ] Exit codes có ý nghĩa
- [ ] Không in secrets
- [ ] Không phá hủy dữ liệu
