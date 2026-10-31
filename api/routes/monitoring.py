"""Phase 30 - EXT-05: Monitoring API endpoints"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
def get_monitoring_health() -> Dict[str, Any]:
    from ml.monitoring import FraudMonitor
    monitor = FraudMonitor()
    return monitor.get_system_health()


@router.get("/fraud-rate")
def get_fraud_rate() -> Dict[str, Any]:
    from ml.monitoring import FraudMonitor
    monitor = FraudMonitor()
    # Without DB access in this context, return basic info
    return {
        "status": "ok",
        "message": "Fraud rate monitoring available (requires DB connection)",
        "threshold": monitor.fraud_rate_threshold,
        "note": "predicted_fraud_rate != actual_fraud_rate (no ground truth labels)"
    }
