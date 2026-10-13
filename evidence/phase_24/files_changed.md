# Phase 24 — Files Created / Modified

## Tạo mới

| File | Mục đích |
|---|---|
| `run_pipeline.py` | Pipeline runner: 14 bước, subprocess + exit code + timeout, evidence logging, ingestion safety gate, `--steps`/`--evidence-dir` |
| `tests/conftest.py` | pytest config: sys.path + tùy chọn `--run-pipeline` |
| `tests/test_end_to_end.py` | E2E tests C1-C9 (32 tests độc lập) + full-pipeline test (opt-in) |
| `evidence/phase_24/audit_report.md` | Báo cáo audit Giai đoạn A |
| `evidence/phase_24/commands_log.md` | Lệnh thực thi + exit code |
| `evidence/phase_24/pipeline_summary.json` | Tóm tắt pipeline (runner sinh ra) |
| `evidence/phase_24/logs/step_*.log` | Log từng bước (14 files) |
| `evidence/phase_24/pytest_results.txt` | Kết quả pytest |
| `evidence/phase_24/row_counts.json` | Số dòng RAW/staging/marts/predictions |
| `evidence/phase_24/files_changed.md` | File này |
| `evidence/phase_24/models_pre_training_backup/` | Backup artifacts trước retrain (xgboost.pkl, feature_columns.json, frequency_encoder.pkl, preprocessor.pkl) |

## Sửa đổi

| File | Thay đổi | Lý do |
|---|---|---|
| `docs/24_end_to_end/end_to_end.md` | Viết lại hoàn toàn | Bản cũ chứa thông tin sai (artifact `xgb_model.pkl`, DAG `fraud_detection_pipeline`, DB_URL hardcode, payload schema sai `TransactionID`) |

## KHÔNG sửa đổi (bảo toàn Phase 9-23)

- `ingestion/load_raw.py`, `dbt/**`, `ml/train.py`, `ml/evaluate.py`, `ml/predict.py`, `ml/shap_explain.py`, `ml/config.py`, `api/**`, `ai_assistant/**`, `airflow/**`, `docker-compose.yml`, `Dockerfile*`, `.env`

## Ghi chú

- `ml/models/*` được retrain bởi pipeline (deterministic, RANDOM_STATE=42): `logistic_regression.pkl`, `logistic_scaler.pkl`, `random_forest.pkl`, `xgboost.pkl`, `feature_columns.json`, `training_results.json`, `evaluation_*`, `prediction_metrics.*`, `shap_*.png`, `top_features.csv` — đây là kết quả mong đợi của pipeline, không phải sửa code.
- `marts.predictions` được TRUNCATE + insert lại bởi `ml/predict.py` (idempotent theo thiết kế Phase 19, unique trên (transaction_id, model_version)).
- `ml/models/models_pre_training_backup/` giữ bản artifacts trước retrain để đối chiếu.
