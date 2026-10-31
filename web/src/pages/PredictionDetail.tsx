import { useCallback, useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { apiJson } from "../api";

export default function PredictionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [record, setRecord] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await apiJson<any>(`/predictions/${id}`);
      setRecord(data);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Khong tai duoc chi tiet du doan");
      if ((e as any).status === 404) {
        navigate("/history");
      }
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="page"><div className="content-loading"><div className="spinner" /></div></div>
    );
  }

  if (error || !record) {
    return (
      <div className="page">
        <div className="page-header"><h2>Chi tiet du doan</h2></div>
        <div className="alert alert-error">
          {error || "Khong tim thay du doan."}
          <br />
          <Link to="/history">Quay ve lich su</Link>
        </div>
      </div>
    );
  }

  const inputPayload = record.input_payload || {};
  const payloadEntries = typeof inputPayload === "object" && inputPayload !== null ? Object.entries(inputPayload) : [];

  return (
    <div className="page">
      <div className="page-header">
        <h2>Chi tiet du doan</h2>
        <Link to="/history" className="btn btn-secondary">Quay ve lich su</Link>
      </div>

      <div className="card">
        <h3>Ket qua model XGBoost (thuc te)</h3>
        <div className="detail-row">
          <span className="k">Prediction ID</span>
          <span style={{ fontFamily: "monospace", fontSize: 12 }}>{record.prediction_id}</span>
        </div>
        <div className="detail-row">
          <span className="k">Che do kiem thu</span>
          <span>{record.input_mode}</span>
        </div>
        <div className="detail-row">
          <span className="k">Nhan du doan</span>
          <span className={
            record.is_fraud_predicted === 1 ? "label-fraud" : "label-legit"
          }>
            {record.is_fraud_predicted === 1 ? "GIAN LUAN (1)" : "HOP LE (0)"}
          </span>
        </div>
        <div className="detail-row">
          <span className="k">Xac suat gian luan</span>
          <span>{(record.fraud_probability * 100).toFixed(4)}%</span>
        </div>
        <div className="detail-row">
          <span className="k">Nguong du ap dung</span>
          <span>{record.threshold}</span>
        </div>
        <div className="detail-row">
          <span className="k">Muc do rui ro</span>
          <span className={
            record.fraud_probability >= 0.7 ? "risk-high" :
            record.fraud_probability >= 0.3 ? "risk-medium" : "risk-low"
          }>
            {record.risk_level}
          </span>
        </div>
        <div className="detail-row">
          <span className="k">Model version</span>
          <span>{record.model_version}</span>
        </div>
        <div className="detail-row">
          <span className="k">Thuc hien vao</span>
          <span>{new Date(record.predicted_at).toLocaleString("vi-VN")}</span>
        </div>
        <div className="detail-row">
          <span className="k">Trang thai luu tru</span>
          <span>{record.status}</span>
        </div>
        {record.transaction_id != null && (
          <div className="detail-row">
            <span className="k">Ma giao dich goc</span>
            <span>{record.transaction_id}</span>
          </div>
        )}
      </div>

      <div className="card">
        <h3>Du lieu nhap vao (da luu trong lich su kiem thu)</h3>
        {payloadEntries.length === 0 ? (
          <div className="empty">Khong co du lieu nhap.</div>
        ) : (
          <table>
            <tbody>
              {payloadEntries.map(([k, v]) => (
                <tr key={k}>
                  <td style={{ color: "#94a3b8", width: "40%" }}>{k}</td>
                  <td>{v === null || v === undefined ? "-" : String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>Giai thich cua AI Assistant</h3>
        {record.ai_explanation ? (
          <div className="ai-card">
            <div className="ai-source">
              AI - {record.ai_available ? "Co AI/OLLAMA" : "AI khong khoan"}{" "}
              - {record.ai_explanation_at ? new Date(record.ai_explanation_at).toLocaleString("vi-VN") : ""}
            </div>
            {record.ai_explanation}
          </div>
        ) : (
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button
              className="btn btn-secondary"
              onClick={() => navigate(`/ai?prediction=${record.prediction_id}`)}
            >
              Yeu cau AI giai thich du doan nay
            </button>
            <span style={{ fontSize: 12, color: "#94a3b8" }}>
              Giai thich duoc sinh boi LLM duoc luu vao ban ghi du doan.
            </span>
          </div>
        )}
        <p style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>
          Liet ke: ket qua model XGBoost vs giai thich cua AI la hai vat ly
          khac nhau. AI khong duoc phep thay doi nhan hoac xac suat cua model.
          Du doan khong la ket luan phap ly ve gian luan.
        </p>
      </div>
    </div>
  );
}
