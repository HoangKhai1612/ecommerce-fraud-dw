export default function Settings() {
  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Cấu hình hệ thống</div>
            <div className="card-subtitle">Trạng thái cấu hình</div>
          </div>
        </div>
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">API & Backend</div>
            <ul>
              <li>FastAPI - Port 8000</li>
              <li>AI Assistant - Port 8001</li>
              <li>MLflow - Port 5000</li>
            </ul>
          </div>
          <div className="card">
            <div className="card-title">AI Provider</div>
            <p>Hỗ trợ: Ollama (local) / DeepSeek (cloud)</p>
            <p>Được cấu hình qua biến môi trường AI_PROVIDER</p>
          </div>
        </div>
      </div>
    </div>
  );
}
