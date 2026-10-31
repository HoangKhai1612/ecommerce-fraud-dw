import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import TransactionTesting from "./pages/TransactionTesting";
import PredictionDetail from "./pages/PredictionDetail";
import AIDataAnalyst from "./pages/AIDataAnalyst";
import PredictionHistory from "./pages/PredictionHistory";
import SystemStatus from "./pages/SystemStatus";
import DataWarehouse from "./pages/DataWarehouse";
import MachineLearning from "./pages/MachineLearning";
import ModelComparison from "./pages/ModelComparison";
import BatchPrediction from "./pages/BatchPrediction";
import Monitoring from "./pages/Monitoring";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="/signin" element={<Navigate to="/" replace />} />
          <Route path="/auth" element={<Navigate to="/" replace />} />
          <Route path="/register" element={<Navigate to="/" replace />} />
          <Route path="/dw" element={<DataWarehouse />} />
          <Route path="/transactions" element={<TransactionTesting />} />
          <Route path="/testing" element={<TransactionTesting />} />
          <Route path="/prediction/:id" element={<PredictionDetail />} />
          <Route path="/history" element={<PredictionHistory />} />
          <Route path="/ml" element={<MachineLearning />} />
          <Route path="/models" element={<ModelComparison />} />
          <Route path="/batch" element={<BatchPrediction />} />
          <Route path="/ai" element={<AIDataAnalyst />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/status" element={<SystemStatus />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
