export default function DataWarehouse() {
  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Data Warehouse</div>
            <div className="card-subtitle">Khám phá dữ liệu phân tích</div>
          </div>
        </div>
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">Kiến trúc</div>
            <p>Raw → Staging → Data Warehouse → Marts (Analytics)</p>
            <p>PostgreSQL Data Warehouse</p>
          </div>
          <div className="card">
            <div className="card-title">Thành phần</div>
            <ul>
              <li>Apache Airflow (Orchestration)</li>
              <li>dbt (Data Transformation)</li>
              <li>Metabase (BI Dashboard)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
