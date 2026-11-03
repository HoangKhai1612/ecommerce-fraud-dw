import { useState } from "react";
import { apiRequest } from "../api";

export default function BatchPrediction() {
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState("xgboost");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [batchDetails, setBatchDetails] = useState<any>(null);
  const [batchOffset, setBatchOffset] = useState(0);
  const batchPageSize = 100;

  async function loadBatchPage(batchId: string, offset: number) {
    const detailRes = await apiRequest(
      `/predictions/batch/${batchId}?offset=${offset}&limit=${batchPageSize}`,
    );
    const detailText = await detailRes.text();
    const detailBody = JSON.parse(detailText);
    if (!detailRes.ok) {
      throw new Error(detailBody?.detail || `HTTP ${detailRes.status}`);
    }
    setBatchDetails(detailBody);
    setBatchOffset(offset);
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Vui lòng chọn file CSV");
      return;
    }
    setUploading(true);
    setError(null);
    setResult(null);
    setBatchDetails(null);
    setBatchOffset(0);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_name", model);
      const res = await apiRequest("/predictions/batch", {
        method: "POST",
        body: formData,
        headers: {} as any,
      });
      const text = await res.text();
      let body: any = null;
      try { body = JSON.parse(text); } catch { body = text; }
      if (!res.ok) {
        throw new Error(body?.detail || `HTTP ${res.status}`);
      }
      setResult(body);
      
      // If completed, fetch details
      if (body.status === "completed" && body.batch_id) {
        try {
          await loadBatchPage(body.batch_id, 0);
        } catch (detailError: any) {
          setError(`Batch đã chạy xong nhưng không tải được danh sách chi tiết: ${detailError.message}`);
        }
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function downloadResults() {
    if (!result?.batch_id) return;
    try {
      const res = await apiRequest(`/predictions/batch/${result.batch_id}/download`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_${result.batch_id}_results.csv`;
      a.click();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Dự đoán hàng loạt (Batch Prediction)</div>
            <div className="card-subtitle">Tải lên file CSV để dự đoán gian lận hàng loạt - EXT-06</div>
          </div>
        </div>
        <form onSubmit={handleUpload}>
          <div style={{ marginBottom: "12px" }}>
            <label>Chọn file CSV</label><br />
            <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </div>
          <div style={{ marginBottom: "12px" }}>
            <label>Mô hình</label><br />
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="xgboost">XGBoost</option>
              <option value="lightgbm">LightGBM</option>
              <option value="random_forest">Random Forest</option>
              <option value="logistic_regression">Logistic Regression</option>
            </select>
          </div>
          <button type="submit" disabled={uploading}>
            {uploading ? "Đang tải lên..." : "Tải lên và dự đoán"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        {result && (
          <div style={{ marginTop: "16px" }}>
            <h3>Kết quả</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", background: "#0f172a", padding: "12px", borderRadius: "6px" }}>
              <div><strong>Batch ID:</strong> {result.batch_id}</div>
              <div><strong>Trạng thái:</strong> <span style={{ color: result.status === 'completed' ? '#4ade80' : '#fbbf24' }}>{result.status}</span></div>
              <div><strong>Tổng số bản ghi:</strong> {result.total_rows}</div>
              <div><strong>Thành công:</strong> {result.successful ?? result.total_rows}</div>
              <div><strong>Phát hiện gian lận:</strong> <span style={{ color: '#f87171' }}>{result.fraud_detected || 0}</span></div>
              <div><strong>Hợp lệ:</strong> <span style={{ color: '#4ade80' }}>{result.legit || 0}</span></div>
              <div><strong>File:</strong> {result.filename}</div>
              <div><strong>Mô hình:</strong> {result.model_name}</div>
              <div><strong>Phiên bản:</strong> {result.model_version || "-"}</div>
              <div><strong>Ngưỡng phân loại:</strong> {result.threshold ?? "-"}</div>
              <div><strong>Xác suất gian lận trung bình:</strong> {result.statistics?.avg_fraud_probability == null ? "-" : `${(result.statistics.avg_fraud_probability * 100).toFixed(2)}%`}</div>
              <div><strong>Rủi ro cao / trung bình / thấp:</strong> {result.statistics ? `${result.statistics.high_risk_count} / ${result.statistics.medium_risk_count} / ${result.statistics.low_risk_count}` : "-"}</div>
            </div>
            <p style={{ marginTop: "12px" }}>{result.message}</p>
            {result.status === "completed" && (
              <button onClick={downloadResults} style={{ marginTop: "8px" }}>Tải xuống kết quả CSV</button>
            )}
          </div>
        )}
        {batchDetails?.results && batchDetails.results.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <h4>Kết quả từng giao dịch ({batchOffset + 1}–{batchOffset + batchDetails.results.length} / {batchDetails.results_total})</h4>
            <div style={{ overflowX: "auto", maxHeight: "400px" }}>
              <table style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#1e293b" }}>
                    <th style={{ padding: "6px", textAlign: "left" }}>STT</th>
                    <th style={{ padding: "6px", textAlign: "left" }}>Transaction ID</th>
                    <th style={{ padding: "6px", textAlign: "left" }}>Xác suất</th>
                    <th style={{ padding: "6px", textAlign: "left" }}>Dự đoán</th>
                    <th style={{ padding: "6px", textAlign: "left" }}>Mức độ</th>
                  </tr>
                </thead>
                <tbody>
                  {batchDetails.results.map((r: any, i: number) => (
                    <tr key={`${r.row_index}-${i}`} style={{ borderBottom: "1px solid #334155" }}>
                      <td style={{ padding: "4px 6px" }}>{r.row_index}</td>
                      <td style={{ padding: "4px 6px" }}>{r.transaction_id}</td>
                      <td style={{ padding: "4px 6px" }}>{r.fraud_probability == null ? '-' : (r.fraud_probability * 100).toFixed(2) + '%'}</td>
                      <td style={{ padding: "4px 6px", color: r.predicted_label === 1 ? '#f87171' : '#4ade80' }}>{r.prediction || '-'}</td>
                      <td style={{ padding: "4px 6px" }}>{r.risk_level || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "8px" }}>
              <button
                type="button"
                disabled={batchOffset === 0}
                onClick={() => result?.batch_id && loadBatchPage(result.batch_id, Math.max(0, batchOffset - batchPageSize)).catch((e: any) => setError(e.message))}
              >Trang trước</button>
              <span>{batchDetails.results_total} kết quả; mỗi trang {batchPageSize} dòng</span>
              <button
                type="button"
                disabled={batchOffset + batchDetails.results.length >= batchDetails.results_total}
                onClick={() => result?.batch_id && loadBatchPage(result.batch_id, batchOffset + batchPageSize).catch((e: any) => setError(e.message))}
              >Trang tiếp</button>
            </div>
          </div>
        )}
      </div>
      <div className="card" style={{ marginTop: "16px" }}>
        <div className="card-header">
          <div className="card-title">Hướng dẫn</div>
        </div>
        <p>File CSV cần có đúng cấu trúc dữ liệu giao dịch như đầu vào của mô hình.</p>
        <p>Hệ thống sẽ tự động xử lý feature engineering và preprocessing theo pipeline huấn luyện.</p>
      </div>
    </div>
  );
}
