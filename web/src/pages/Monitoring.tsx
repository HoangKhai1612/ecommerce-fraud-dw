import { useEffect, useState } from "react";
import { apiJson } from "../api";

export default function Monitoring() {
  const [health, setHealth] = useState<any>(null);
  const [fraudRate, setFraudRate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const h = await apiJson<any>("/monitoring/health").catch(() => null);
      const f = await apiJson<any>("/monitoring/fraud-rate").catch(() => null);
      setHealth(h);
      setFraudRate(f);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Giám sát hệ thống</div>
            <div className="card-subtitle">Fraud Monitoring & Alerting - EXT-05</div>
          </div>
        </div>
        {loading && <p>Đang tải...</p>}
        {!loading && (
          <div className="grid grid-2">
            <div className="card">
              <div className="card-title">Trạng thái giám sát</div>
              {health ? (
                <div>
                  <p><strong>Status:</strong> {health.status}</p>
                  <p><strong>Monitoring enabled:</strong> {health.monitoring_enabled ? "Yes" : "No"}</p>
                  <p><strong>Threshold:</strong> {(health.thresholds?.fraud_rate_threshold * 100).toFixed(1)}%</p>
                </div>
              ) : <p>Không khả dụng</p>}
            </div>
            <div className="card">
              <div className="card-title">Tỷ lệ gian lận dự đoán</div>
              {fraudRate ? (
                <div>
                  <p><strong>Trạng thái:</strong> {fraudRate.status}</p>
                  <p><strong>Ghi chú:</strong> {fraudRate.note || fraudRate.message}</p>
                  {fraudRate.threshold && <p><strong>Ngưỡng cảnh báo:</strong> {(fraudRate.threshold * 100).toFixed(1)}%</p>}
                </div>
              ) : <p>Không khả dụng</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
