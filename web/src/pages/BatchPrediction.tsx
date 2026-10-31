import { useState } from "react";
import { apiRequest } from "../api";

export default function BatchPrediction() {
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState("xgboost");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Vui lòng chọn file CSV");
      return;
    }
    setUploading(true);
    setError(null);
    setResult(null);
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
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
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
            <p><strong>Batch ID:</strong> {result.batch_id}</p>
            <p><strong>Trạng thái:</strong> {result.status}</p>
            <p><strong>Số bản ghi:</strong> {result.total_rows}</p>
            <p><strong>File:</strong> {result.filename}</p>
            <p><strong>Mô hình:</strong> {result.model_name}</p>
            <p>{result.message}</p>
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
