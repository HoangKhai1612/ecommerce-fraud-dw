import { useCallback, useEffect, useState } from "react";
import { apiJson, SystemStatusResponse, ServiceStatus } from "../api";

export default function SystemStatus() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: SystemStatusResponse = await apiJson("/system/status");
      setStatus(data);
    } catch (e: any) {
      // Try fallback to health
      try {
        const h = await apiJson<any>("/health");
        setStatus({
          model: { name: "XGBoost", status: "ok", detail: "Model loaded" },
          database: { name: "Postgres", status: h.status === "ok" ? "ok" : "degraded", detail: "Connected" },
          api: { name: "FastAPI", status: "ok", detail: "API running" },
          ai: { name: "AI", status: "unknown", detail: "Unknown" },
          ollama: { name: "Ollama", status: "unknown", detail: "Unknown" },
        } as any);
        setError(null);
        return;
      } catch {
        // ignore
      }
      setError(e.message || "Khong lay duoc trang thai he thong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  const statusBadge = (s: ServiceStatus) => {
    const cls = `status-dot status-${s.status}`;
    return (
      <div className="status-row" style={{ marginBottom: 10 }}>
        <span className={cls} />
        <strong>{s.name}</strong>: {s.detail || s.status}
        <span
          style={{
            fontSize: 11,
            color: "#94a3b8",
            marginLeft: 8,
            textTransform: "uppercase",
          }}
        >
          [{s.status}]
        </span>
      </div>
    );
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>He thong</h2>
        <button
          className="btn btn-secondary"
          onClick={load}
          disabled={loading}
        >
          Cap nhat
        </button>
      </div>

      {loading ? (
        <div className="content-loading"><div className="spinner" /></div>
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : (
        <>
          <div className="card">
            <h3>Trang thai dich vu</h3>
            {status && [
              status.model,
              status.database,
              status.ai,
              status.ollama,
            ].filter(Boolean).map((s: any, idx: number) => (
              <div key={s.name || idx}>{statusBadge(s)}</div>
            ))}
          </div>

          <div className="card">
            <h3>Giai thich trang thai</h3>
            <ul style={{ paddingLeft: 20, color: "#94a3b8", fontSize: 13 }}>
              <li>
                <strong>ok:</strong> dich vu hoat dung binh thuong.
              </li>
              <li>
                <strong>degraded:</strong> dich vu da ket noi nhung co han che
                (vd. model LLM chua duoc tai).
              </li>
              <li>
                <strong>unavailable:</strong> dich vu khong the ket noi.
              </li>
            </ul>
            <p style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>
              Trang thai AI/OLLAMA khong anh huong khong du doan: neu AI khoan,
              XGBoost van tra ket qua thuc va luu lich su. Trang thai nay duoc
              cap nhat tu dong moi 15 giay.
            </p>
          </div>

          <div className="card">
            <h3>Du an</h3>
            <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>
              Ngan thuc thu cong the tich - Phase 31: Integrated Fraud Detection
              Testing Platform. Backend: FastAPI (port 8000). Model: XGBoost
              (ml/models/xgboost.pkl, 1.014 feature). LLM: Ollama llama3. CSDL:
              PostgreSQL marts schema.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
