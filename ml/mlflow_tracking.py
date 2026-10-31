"""Phase 30 - EXT-03: MLflow Experiment Tracking"""
import json
import os
import time

import mlflow
import mlflow.sklearn


def setup_mlflow(experiment_name: str = "fraud_detection", tracking_uri: str = None):
    if tracking_uri is None:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    return mlflow.get_experiment_by_name(experiment_name)


def log_training_run(model_name: str, model, params: dict, metrics: dict, artifacts: dict = None):
    with mlflow.start_run(run_name=f"{model_name}_{int(time.time())}"):
        for k, v in params.items():
            try:
                mlflow.log_param(k, v)
            except Exception:
                pass
        for k, v in metrics.items():
            try:
                if isinstance(v, (int, float)):
                    mlflow.log_metric(k, v)
            except Exception:
                pass
        mlflow.set_tag("model_name", model_name)
        mlflow.set_tag("training_timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        try:
            mlflow.sklearn.log_model(model, "model")
        except Exception:
            pass
        if artifacts:
            for name, path in artifacts.items():
                try:
                    if path and os.path.exists(path):
                        mlflow.log_artifact(path, name)
                except Exception:
                    pass
        run = mlflow.active_run()
        return run.info.run_id if run else None
