import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, SystemStatusResponse, PredictionListItem } from "../api";
import "../index.css";

export default function Overview() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [recent, setRecent] = useState<PredictionListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, historyRes] = await Promise.allSettled([
        apiJson<SystemStatusResponse>("/system/status"),
        apiJson<{ items: PredictionListItem[]; total: number }>(
          "/predictions?limit=50"
        ),
      ]);
      if (statusRes.status === 'fulfilled') {
        setStatus(statusRes.value);
      }
      if (historyRes.status === 'fulfilled') {
        setRecent(historyRes.value.items || []);
        setTotal(historyRes.value.total || 0);
      }
      setError(null);
    } catch (e: any) {
      setError(e.message || "Khong the lay du lieu trang chu");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const fraudCount = recent.filter((r) => r.is_fraud_predicted === 1).length;
  const legitCount = recent.length - fraudCount;

  if (loading) {
    return <div className="content-loading"><div className="spinner" /></div>;
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-header"><h2>Tong quan</h2></div>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Tong quan</h2>
        <span className="badge">
          {status?.model.status === "ok" ? "Model san sang" : "Model chua san sang"}
        </span>
      </div>

      {status && (
        <div className="grid">
          <div className="stat-card">
            <div className="label">Tong so kiem thu</div>
            <div className="value">{total}</div>
            <div className="label" style={{ marginTop: 6 }}>
              Cac lan kiem thu gan nhat: {recent.length}
            </div>
          </div>
          <div className="stat-card">
            <div className="label">Du doan gian luan (1)</div>
            <div className="value label-fraud">{fraudCount}</div>
          </div>
          <div className="stat-card">
            <div className="label">Du doan hop le (0)</div>
            <div className="value label-legit">{legitCount}</div>
          </div>
          <div className="stat-card">
            <div className="label">Model</div>
            <div className="value">{status.model.detail}</div>
          </div>
        </div>
      )}

      {status && (
        <div className="card">
          <h3>Trang thai dich vu</h3>
          <div className="status-row">
            <span className={`status-dot status-${status.model.status}`}></span>
            <strong>XGBoost ({status.model.name}):</strong>{" "}
            {status.model.status === "ok" ? "San sang du doan" : "Khong san sang"}
            {status.model.detail ? ` - ${status.model.detail}` : ""}
          </div>
          <div className="status-row" style={{ marginTop: 6 }}>
            <span className={`status-dot status-${status.database.status}`}></span>
            <strong>PostgreSQL:</strong>{" "}
            {status.database.status === "ok" ? "Ket noi OK" : "Khong ket noi duoc"}
            {status.database.detail ? ` - ${status.database.detail}` : ""}
          </div>
          <div className="status-row" style={{ marginTop: 6 }}>
            <span className={`status-dot status-${status.ai.status}`}></span>
            <strong>AI Assistant:</strong>{" "}
            {status.ai.status === "ok" ? "San sang" : "Khong san sang"}
            {status.ai.detail ? ` - ${status.ai.detail}` : ""}
          </div>
          <div className="status-row" style={{ marginTop: 6 }}>
            <span className={`status-dot status-${status.ollama.status}`}></span>
            <strong>Ollama (LLM):</strong>{" "}
            {status.ollama.status === "ok" ? "San sang" : "Khong san sang"}
            {status.ollama.detail ? ` - ${status.ollama.detail}` : ""}
          </div>
          <p style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>
            AI timeout khong lam giu hoat du doan: neu AI khoan, XGBoost van tra
            ket qua thuc va luu lich su binh thuong.
          </p>
        </div>
      )}

      <div className="card">
        <h3>Kiem thu gan nhat</h3>
        {recent.length === 0 ? (
          <div className="empty">Chua co lich su kiem thu nao. Bat dau o <Link to="/testing">Trang kiem thu</Link>.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Prediction ID</th>
                <th>Che do</th>
                <th>Nhan</th>
                <th>Xac suat</th>
                <th>Model</th>
                <th>Thoi gian</th>
                <th>AI</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.prediction_id}>
                  <td>
                    <Link to={`/prediction/${r.prediction_id}`}>
                      {r.prediction_id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td>{r.input_mode}</td>
                  <td>
                    <span className={
                      r.is_fraud_predicted === 1 ? "label-fraud" : "label-legit"
                    }>
                      {r.is_fraud_predicted === 1 ? "GIAN LUAN" : "HOP LE"}
                    </span>
                  </td>
                  <td>{(r.fraud_probability * 100).toFixed(2)}%</td>
                  <td>{r.model_version}</td>
                  <td>{new Date(r.predicted_at).toLocaleString("vi-VN")}</td>
                  <td>
                    {r.ai_available ? "Da giai thich" : "Chua co giai thich"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
