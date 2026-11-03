import { useEffect, useState, FormEvent } from "react";
import { apiJson } from "../api";

type Sample = {
  transaction_id: number;
  is_fraud: number;
  transaction_amt: number;
  product_cd: string;
  transaction_dt: number;
};

const MINIMAL_FIELDS: { key: string; label: string; placeholder: string }[] = [
  { key: "transaction_id", label: "Ma giao dich", placeholder: "vd. 12345" },
  { key: "transaction_dt", label: "TransactionDT (giay)", placeholder: "vd. 86400" },
  { key: "transaction_amt", label: "So tien (USD)", placeholder: "vd. 150.75" },
  { key: "product_cd", label: "Ma san pham (C/H/R/S/W)", placeholder: "vd. W" },
  { key: "card1", label: "card1", placeholder: "vd. 1001" },
  { key: "card4", label: "card4 (loai the)", placeholder: "vd. visa" },
  { key: "card6", label: "card6", placeholder: "vd. credit" },
  { key: "device_type", label: "Loai thiet bi", placeholder: "vd. mobile" },
  { key: "device_info", label: "Thong tin thiet bi", placeholder: "vd. SM-G950F" },
  { key: "p_emaildomain", label: "Mien email nguoi gui", placeholder: "vd. gmail.com" },
];

export default function TransactionTesting() {
  const [form, setForm] = useState<Record<string, string>>({
    transaction_id: "",
    transaction_dt: "",
    transaction_amt: "",
    product_cd: "",
    card1: "",
    card4: "",
    card6: "",
    device_type: "",
    device_info: "",
    p_emaildomain: "",
  });
  const [rawJson, setRawJson] = useState("");
  const [dwSamples, setDwSamples] = useState<{ fraud: Sample[]; legit: Sample[] } | null>(null);
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [rawFeatures, setRawFeatures] = useState<Record<string, any> | null>(null);
  const [groundTruth, setGroundTruth] = useState<number | null>(null);
  const [modified, setModified] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [explaining, setExplaining] = useState(false);
  const [aiAnswer, setAiAnswer] = useState<{ answer: string; source: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await apiJson<{ fraud: Sample[]; legit: Sample[] }>("/transactions/samples?n=10");
        setDwSamples(data);
      } catch {
        setDwSamples({ fraud: [], legit: [] });
      }
    })();
  }, []);

  const fillSample = async (s: Sample) => {
    let fullData: Record<string, any> = {};
    try {
      fullData = await apiJson<Record<string, any>>(`/transactions/${s.transaction_id}`);
    } catch {
      fullData = { ...s };
    }

    setForm({
      transaction_id: String(fullData.transaction_id ?? s.transaction_id),
      transaction_dt: String(fullData.transaction_dt ?? s.transaction_dt),
      transaction_amt: String(fullData.transaction_amt ?? s.transaction_amt),
      product_cd: fullData.product_cd ?? s.product_cd,
      card1: fullData.card1 != null ? String(fullData.card1) : "",
      card4: fullData.card4 ?? "",
      card6: fullData.card6 ?? "",
      device_type: fullData.device_type ?? "",
      device_info: fullData.device_info ?? "",
      p_emaildomain: fullData.p_emaildomain ?? "",
    });
    setRawFeatures(fullData);
    setSelectedSample(s);
    setGroundTruth(s.is_fraud);
    setModified(false);
    setRawJson("");
    setResult(null);
    setAiAnswer(null);
    setError(null);
  };

  const markModified = () => {
    if (selectedSample && !modified) setModified(true);
  };

  const buildPayload = (): Record<string, any> => {
    // For DW tab with selected sample: send ALL raw features from DW
    if (rawFeatures && selectedSample && !modified) {
      const payload: Record<string, any> = { ...rawFeatures };
      // Remove technical columns that shouldn't be features
      delete payload._loaded_at;
      delete payload.transaction_key;
      return payload;
    }

    // For modified DW or manual: use form fields
    const payload: Record<string, any> = {};
    for (const [k, v] of Object.entries(form)) {
      if (v === "") continue;
      if (["transaction_id", "transaction_dt", "card1"].includes(k)) {
        const n = Number(v);
        payload[k] = Number.isNaN(n) ? v : n;
      } else if (k === "transaction_amt") {
        payload[k] = Number(v);
      } else {
        payload[k] = v;
      }
    }
    if (rawJson.trim()) {
      try {
        Object.assign(payload, JSON.parse(rawJson));
      } catch {
        // ignore
      }
    }
    return payload;
  };

  const handleSubmit = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setResult(null);
    setAiAnswer(null);
    setSubmitting(true);

    try {
      const payload = buildPayload();
      const required = ["transaction_dt", "transaction_amt", "product_cd"];
      for (const field of required) {
        if (payload[field] === undefined || payload[field] === "" || payload[field] === null) {
          throw new Error(`Thieu truong bat buoc: ${field}`);
        }
      }

      const res = await apiJson<any>("/predictions", {
        method: "POST",
        body: JSON.stringify({ mode: "ieee-cis", transaction: payload }),
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Co loi xay ra khi du doan");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExplain = async () => {
    if (!result?.prediction_id) return;
    setExplaining(true);
    try {
      const data = await apiJson<any>(`/predictions/${result.prediction_id}/explain`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      setAiAnswer({ answer: data.answer, source: data.source });
    } catch (e: any) {
      setError(e.message || "Khong duoc giai thich boi AI");
    } finally {
      setExplaining(false);
    }
  };

  const isModifiedScenario = modified && selectedSample !== null;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Kiem thu giao dich</h2>
      </div>

      <div className="card">
        <div className="btn-group" style={{ marginBottom: 16 }}>
          <button className="btn btn-primary" type="button">
            Kiểm thử giao dịch gian lận
          </button>
        </div>

        <>
            <div style={{ fontSize: 13, color: "#94a3b8", marginBottom: 10 }}>
              Chon 1 trong 10 mau gian luan hoac 10 mau hop le tu Data Warehouse.
              Du lieu thuc te se duoc tu dong dien vao form.
            </div>

            {dwSamples && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                <div>
                  <h4 style={{ color: "#f87171", marginBottom: 6 }}>Gian luan (10 mau)</h4>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {dwSamples.fraud.map((s) => (
                      <button
                        key={s.transaction_id}
                        className={`btn btn-secondary ${selectedSample?.transaction_id === s.transaction_id ? "btn-active" : ""}`}
                        style={{ fontSize: 11 }}
                        onClick={() => fillSample(s)}
                        disabled={submitting}
                      >
                        #{s.transaction_id} ({s.transaction_amt} USD)
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 style={{ color: "#4ade80", marginBottom: 6 }}>Hop le (10 mau)</h4>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {dwSamples.legit.map((s) => (
                      <button
                        key={s.transaction_id}
                        className={`btn btn-secondary ${selectedSample?.transaction_id === s.transaction_id ? "btn-active" : ""}`}
                        style={{ fontSize: 11 }}
                        onClick={() => fillSample(s)}
                        disabled={submitting}
                      >
                        #{s.transaction_id} ({s.transaction_amt} USD)
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {selectedSample && (
              <div className="card" style={{ marginBottom: 12 }}>
                <h4>Mau da chon</h4>
                <div className="detail-row">
                  <span className="k">Transaction ID</span>
                  <span>{selectedSample.transaction_id}</span>
                </div>
                <div className="detail-row">
                  <span className="k">Nhan thuc te</span>
                  <span className={selectedSample.is_fraud === 1 ? "label-fraud" : "label-legit"}>
                    {selectedSample.is_fraud === 1 ? "GIAN LUAN" : "HOP LE"}
                  </span>
                </div>
                {modified && (
                  <div className="alert alert-warn" style={{ marginTop: 8 }}>
                    Du lieu da duoc chinh sua - Modified Scenario.
                  </div>
                )}
                {rawFeatures && (
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ cursor: "pointer", color: "#94a3b8", fontSize: 13 }}>
                      Raw Features tu Data Warehouse ({Object.keys(rawFeatures).length} truong)
                    </summary>
                    <div style={{ maxHeight: 300, overflowY: "auto", marginTop: 8 }}>
                      <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                        <thead>
                          <tr>
                            <th style={{ textAlign: "left", padding: "4px 6px", borderBottom: "1px solid #334155", color: "#94a3b8" }}>Feature</th>
                            <th style={{ textAlign: "left", padding: "4px 6px", borderBottom: "1px solid #334155", color: "#94a3b8" }}>Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(rawFeatures).map(([k, v]) => (
                            <tr key={k}>
                              <td style={{ padding: "2px 6px", borderBottom: "1px solid #1e293b", color: "#cbd5e1" }}>{k}</td>
                              <td style={{ padding: "2px 6px", borderBottom: "1px solid #1e293b" }}>
                                {v === null ? <span style={{ color: "#f87171" }}>NULL</span> : String(v)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </div>
            )}

            <div className="form">
              {MINIMAL_FIELDS.map((f) => (
                <div className="field" key={f.key}>
                  <label>{f.label}</label>
                  <input
                    value={form[f.key]}
                    onChange={(ev) => {
                      setForm({ ...form, [f.key]: ev.target.value });
                      markModified();
                    }}
                    placeholder={f.placeholder}
                    disabled={submitting}
                  />
                </div>
              ))}
              <div className="field">
                <label>Cac cot them (JSON)</label>
                <textarea
                  value={rawJson}
                  onChange={(ev) => {
                    setRawJson(ev.target.value);
                    markModified();
                  }}
                  placeholder='{"c1": 0.5, "v1": 1.2}'
                  rows={3}
                  disabled={submitting}
                />
              </div>
            </div>
          </>

        <div className="btn-group" style={{ marginTop: 10 }}>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Dang xu ly..." : "Chay du doan XGBoost"}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {result && (
          <div className="card" style={{ marginTop: 12 }}>
            <h3>Ket qua du doan</h3>
            <div className="detail-row">
              <span className="k">Prediction ID</span>
              <span>{result.prediction_id}</span>
            </div>
            <div className="detail-row">
              <span className="k">Nhan du doan</span>
              <span className={result.is_fraud_predicted === 1 ? "label-fraud" : "label-legit"}>
                {result.is_fraud_predicted === 1 ? "GIAN LUAN (1)" : "HOP LE (0)"}
              </span>
              {groundTruth !== null && !modified && (
                <span style={{ fontSize: 12, color: "#94a3b8", marginLeft: 8 }}>
                  (thuc te: {groundTruth === 1 ? "GIAN LUAN" : "HOP LE"})
                </span>
              )}
            </div>
            {groundTruth !== null && !modified && (
              <div className="detail-row">
                <span className="k">Danh gia</span>
                <span>
                  {result.is_fraud_predicted === groundTruth
                    ? (groundTruth === 1 ? "TP (True Positive)" : "TN (True Negative)")
                    : (groundTruth === 1 ? "FN (False Negative)" : "FP (False Positive)")}
                  {" - "}
                  {result.is_fraud_predicted === groundTruth ? "DUNG" : "SAI"}
                </span>
              </div>
            )}
            {isModifiedScenario && (
              <div className="detail-row">
                <span className="k">Trang thai</span>
                <span style={{ color: "#fbbf24" }}>Modified Scenario - khong danh gia dung/sai</span>
              </div>
            )}
            <div className="detail-row">
              <span className="k">Xac suat gian luan</span>
              <span>{(result.fraud_probability * 100).toFixed(4)}%</span>
            </div>
            <div className="detail-row">
              <span className="k">Nguong</span>
              <span>{result.threshold}</span>
            </div>
            <div className="detail-row">
              <span className="k">Muc do rui ro</span>
              <span className={
                result.fraud_probability >= 0.7 ? "risk-high" : result.fraud_probability >= 0.3 ? "risk-medium" : "risk-low"
              }>
                {result.risk_level}
              </span>
            </div>
            <div className="detail-row">
              <span className="k">Model</span>
              <span>{result.model_version}</span>
            </div>
            <div className="detail-row">
              <span className="k">Thoi gian</span>
              <span>{result.predicted_at}</span>
            </div>
            <div style={{ marginTop: 12 }}>
              <button
                className="btn btn-secondary"
                onClick={handleExplain}
                disabled={explaining || !result.prediction_id}
              >
                {explaining ? "Đang phân tích các đặc trưng của mô hình..." : "Giải thích kết quả bằng TreeSHAP"}
              </button>
            </div>
            {aiAnswer && (
              <div className="ai-card">
                <div className="ai-source">
                  {aiAnswer.source === "xgboost-tree-shap"
                    ? "Giải thích mô hình XGBoost - TreeSHAP"
                    : `AI Assistant - Source: ${aiAnswer.source}`}
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{aiAnswer.answer}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
