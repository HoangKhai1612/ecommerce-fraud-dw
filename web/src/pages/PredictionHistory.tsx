import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiJson, PredictionListItem } from "../api";

export default function PredictionHistory() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<PredictionListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(Number(searchParams.get("limit") || 50));
  const [offset, setOffset] = useState(Number(searchParams.get("offset") || 0));
  const [inputMode, setInputMode] = useState(searchParams.get("input_mode") || "");
  const [label, setLabel] = useState(searchParams.get("is_fraud_predicted") || "");
  const [minProb, setMinProb] = useState(searchParams.get("min_probability") || "");
  const [maxProb, setMaxProb] = useState(searchParams.get("max_probability") || "");
  const [from, setFrom] = useState(searchParams.get("from_predicted_at") || "");
  const [to, setTo] = useState(searchParams.get("to_predicted_at") || "");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const mounted = useRef(true);

  const load = useCallback(async () => {
    mounted.current = true;
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (inputMode) params.input_mode = inputMode;
      if (label !== "") params.is_fraud_predicted = label;
      if (minProb !== "") params.min_probability = minProb;
      if (maxProb !== "") params.max_probability = maxProb;
      if (from) params.from_predicted_at = from;
      if (to) params.to_predicted_at = to;
      params.limit = String(limit);
      params.offset = String(offset);

      const qs = Object.entries(params)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join("&");

      const data = await apiJson<any>(
        `/predictions?${qs}`
      ).catch(() => ({ items: [], total: 0, limit, offset }));
      if (mounted.current) {
        setItems(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (e: any) {
      if (mounted.current) setError(e.message || "Khong tai duoc lich su");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [inputMode, label, minProb, maxProb, from, to, limit, offset]);

  useEffect(() => {
    load();
    return () => {
      mounted.current = false;
    };
  }, [load]);

  const updateParam = (key: string, value: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value === "") next.delete(key);
      else next.set(key, value);
      return next;
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="page">
      <div className="page-header">
        <h2>Lich su kiem thu</h2>
      </div>

      <div className="card">
        <h3>Bo loc</h3>
        <div className="form">
          <div className="field">
            <label>Che do</label>
            <select
              value={inputMode}
              onChange={(ev) => {
                setInputMode(ev.target.value);
                updateParam("input_mode", ev.target.value);
              }}
            >
              <option value="">-- tat ca --</option>
              <option value="ieee-cis">IEEE-CIS</option>
              <option value="ecommerce-sim">Mo phong</option>
            </select>
          </div>
          <div className="field">
            <label>Nhan du doan</label>
            <select
              value={label}
              onChange={(ev) => {
                setLabel(ev.target.value);
                updateParam("is_fraud_predicted", ev.target.value);
              }}
            >
              <option value="">-- tat ca --</option>
              <option value="1">GIAN LUAN</option>
              <option value="0">HOP LE</option>
            </select>
          </div>
          <div className="field">
            <label>Xac suat it nhat</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={minProb}
              onChange={(ev) => {
                setMinProb(ev.target.value);
                updateParam("min_probability", ev.target.value);
              }}
            />
          </div>
          <div className="field">
            <label>Xac suat toi da</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={maxProb}
              onChange={(ev) => {
                setMaxProb(ev.target.value);
                updateParam("max_probability", ev.target.value);
              }}
            />
          </div>
          <div className="field">
            <label>Tu thoi gian</label>
            <input
              type="datetime-local"
              value={from}
              onChange={(ev) => {
                setFrom(ev.target.value);
                updateParam("from_predicted_at", ev.target.value);
              }}
            />
          </div>
          <div className="field">
            <label>Den thoi gian</label>
            <input
              type="datetime-local"
              value={to}
              onChange={(ev) => {
                setTo(ev.target.value);
                updateParam("to_predicted_at", ev.target.value);
              }}
            />
          </div>
          <div className="field" style={{ alignSelf: "end", marginTop: 26 }}>
            <button
              className="btn btn-primary"
              onClick={() => setOffset(0)}
            >
            Ap dung
            </button>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ fontSize: 13, color: "#94a3b8", marginBottom: 8 }}>
        Tong co {total} ban ghi. Hien thi {items.length} ban ghi (offset {offset}).
      </div>

      <div className="card">
        {items.length === 0 ? (
          <div className="empty">Chua co ban ghi kiem thu nao phu hop bo loc.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Prediction ID</th>
                <th>Che do</th>
                <th>Giao dich goc</th>
                <th>Nhan</th>
                <th>Xac suat</th>
                <th>Model</th>
                <th>AI</th>
                <th>Thoi gian</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.prediction_id}>
                  <td style={{ fontFamily: "monospace", fontSize: 12 }}>
                    {r.prediction_id}
                  </td>
                  <td>{r.input_mode}</td>
                  <td>{r.transaction_id ?? "-"}</td>
                  <td>
                    <span className={
                      r.is_fraud_predicted === 1 ? "label-fraud" : "label-legit"
                    }>
                      {r.is_fraud_predicted === 1 ? "GIAN LUAN" : "HOP LE"}
                    </span>
                  </td>
                  <td>{(r.fraud_probability * 100).toFixed(2)}%</td>
                  <td>{r.model_version}</td>
                  <td>{r.ai_available ? "Da giai thich" : "Chua"}</td>
                  <td>{new Date(r.predicted_at).toLocaleString("vi-VN")}</td>
                  <td>
                    <Link
                      to={`/prediction/${r.prediction_id}`}
                      className="btn btn-secondary"
                    >
                      Xem chi tiet
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="pagination">
        <div>
          Trang {Math.floor(offset / limit) + 1} / {totalPages}
        </div>
        <div className="btn-group">
          <button
            className="btn btn-secondary"
            disabled={offset === 0 || loading}
            onClick={() => setOffset(Math.max(0, offset - limit))}
          >
            Truoc
          </button>
          <button
            className="btn btn-secondary"
            disabled={offset + limit >= total || loading}
            onClick={() => setOffset(offset + limit)}
          >
            Ke tiep
          </button>
        </div>
      </div>
    </div>
  );
}
