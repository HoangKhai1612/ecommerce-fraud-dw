import { useEffect, useState } from "react";
import { apiJson } from "../api";

export default function MachineLearning() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    try {
      const data = await apiJson<any>("/health").catch(() => null);
      setStatus(data);
    } catch (e) {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Machine Learning</div>
            <div className="card-subtitle">Quản lý mô hình phát hiện gian lận</div>
          </div>
        </div>
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">Mô hình khả dụng</div>
            <ul>
              <li>Logistic Regression</li>
              <li>Random Forest</li>
              <li>XGBoost (mặc định)</li>
              <li>LightGBM (Phase 30 - EXT-01)</li>
            </ul>
          </div>
          <div className="card">
            <div className="card-title">Trạng thái API</div>
            {loading && <p>Đang kiểm tra...</p>}
            {!loading && status && (
              <div>
                <p><strong>Service:</strong> {status.service || "-"}</p>
                <p><strong>Status:</strong> {status.status || "-"}</p>
              </div>
            )}
            {!loading && !status && <p>Không thể kết nối API</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
