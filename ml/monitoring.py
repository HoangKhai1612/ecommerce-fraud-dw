"""
Phase 30 - EXT-05: Fraud Monitoring & Alerting
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FraudMonitor:
    def __init__(self):
        self.fraud_rate_threshold = float(os.getenv("FRAUD_ALERT_THRESHOLD", "0.10"))
        self.alert_cooldown_minutes = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))
        self._last_alert_time = None

    def check_fraud_rate(self, db_connector) -> Dict[str, Any]:
        try:
            query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN predicted_label = 1 THEN 1 END) as predicted_fraud_count,
                    COUNT(CASE WHEN predicted_label = 1 THEN 1 END) * 1.0 / NULLIF(COUNT(*), 0) as predicted_fraud_rate
                FROM marts.web_test_history
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """
            result = db_connector.execute_query(query)
            if not result:
                return {"status": "no_data", "message": "No predictions in last hour"}
            row = result[0]
            fraud_rate = float(row.get("predicted_fraud_rate") or 0)
            total = int(row.get("total_predictions") or 0)
            fraud_count = int(row.get("predicted_fraud_count") or 0)
            
            alert = False
            if fraud_rate > self.fraud_rate_threshold and total >= 10:
                if self._should_alert():
                    alert = True
                    self._last_alert_time = datetime.now()
                    logger.warning(f"FRAUD RATE SPIKE: {fraud_rate:.2%} ({fraud_count}/{total}) in last hour")
            
            return {
                "status": "ok",
                "total_predictions_1h": total,
                "predicted_fraud_count_1h": fraud_count,
                "predicted_fraud_rate_1h": fraud_rate,
                "threshold": self.fraud_rate_threshold,
                "alert_triggered": alert,
                "note": "predicted_fraud_rate != actual_fraud_rate (no ground truth labels)"
            }
        except Exception as e:
            logger.error(f"Error checking fraud rate: {e}")
            return {"status": "error", "message": str(e)}

    def _should_alert(self) -> bool:
        if self._last_alert_time is None:
            return True
        return (datetime.now() - self._last_alert_time).total_seconds() > self.alert_cooldown_minutes * 60

    def get_system_health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "monitoring_enabled": True,
            "thresholds": {
                "fraud_rate_threshold": self.fraud_rate_threshold,
                "alert_cooldown_minutes": self.alert_cooldown_minutes
            },
            "timestamp": datetime.now().isoformat()
        }
