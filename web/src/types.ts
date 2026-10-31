export type PredictionRecord = {
  prediction_id: string;
  transaction_id: number | null;
  model_version: string;
  input_mode: "ieee-cis" | "ecommerce-sim";
  is_fraud_predicted: number;
  fraud_probability: number;
  threshold: number;
  predicted_at: string;
  ai_available: boolean;
  ai_explanation: string | null;
  ai_explanation_at: string | null;
  status: string;
  risk_level?: string;
  message?: string;
  input_payload?: any;
};

export type PredictionListItem = {
  prediction_id: string;
  transaction_id: number | null;
  model_version: string;
  input_mode: "ieee-cis" | "ecommerce-sim";
  is_fraud_predicted: number;
  fraud_probability: number;
  threshold: number;
  predicted_at: string;
  ai_available: boolean;
  status: string;
};

export type PredictionsListResponse = {
  items: PredictionListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type TransactionSample = {
  transaction_id: number;
  is_fraud: number;
  transaction_amt: number;
  product_cd: string;
  transaction_dt: number;
};

export type ServiceStatus = {
  name: string;
  status: "ok" | "degraded" | "unavailable";
  detail: string | null;
};

export type SystemStatusResponse = {
  api: string;
  model: ServiceStatus;
  database: ServiceStatus;
  ai: ServiceStatus;
  ollama: ServiceStatus;
};

export type ExplainResponse = {
  prediction_id: string;
  answer: string;
  ai_available: boolean;
  source: string;
};
