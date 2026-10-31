"""Pydantic schemas for the fraud detection API."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TransactionRaw(BaseModel):
    """
    Raw transaction input for prediction.

    These are the columns from marts.fact_transactions that are needed
    for feature engineering. The full table has 339 v* columns, 38 id_*
    columns, and other features. We accept a flexible dict for the rest.
    """

    model_config = ConfigDict(extra="allow")

    transaction_id: Optional[int] = Field(default=None, gt=0)
    transaction_dt: Optional[int] = Field(default=None, ge=0)
    transaction_amt: float = Field(gt=0, allow_inf_nan=False)
    product_cd: Optional[str] = Field(default=None, min_length=1, max_length=10)
    card1: Optional[float] = None
    card2: Optional[float] = None
    card3: Optional[float] = None
    card4: Optional[str] = None
    card5: Optional[float] = None
    card6: Optional[str] = None
    addr1: Optional[float] = None
    addr2: Optional[float] = None
    dist1: Optional[float] = None
    dist2: Optional[float] = None
    p_emaildomain: Optional[str] = None
    r_emaildomain: Optional[str] = None
    device_type: Optional[str] = None
    device_info: Optional[str] = None
    # c1-c14, d1-d15, v1-v339, id_01-id_38, m1-m9 are optional
    # They can be passed as extra fields


class PredictionResponse(BaseModel):
    transaction_id: int
    is_fraud: int = Field(ge=0, le=1)
    fraud_probability: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high"]
    message: str
    model_version: str


class TransactionResponse(BaseModel):
    transaction_id: int
    is_fraud: int = Field(ge=0, le=1)
    transaction_amt: float
    product_cd: str
    transaction_dt: int


class TopPredictionResponse(BaseModel):
    transaction_id: int
    is_fraud_actual: int
    is_fraud_predicted: int
    fraud_probability: float
    transaction_amt: float
    model_version: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    database: Literal["ok", "unavailable"]


class ErrorResponse(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# Phase 31: integrated testing platform schemas
# ---------------------------------------------------------------------------

class PredictionCreate(BaseModel):
    """Request to run and persist a fraud prediction."""

    mode: Literal["ieee-cis", "ecommerce-sim"] = "ieee-cis"
    transaction: TransactionRaw


class PredictionRecord(BaseModel):
    """Persisted prediction record returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    prediction_id: UUID
    transaction_id: Optional[int] = None
    model_version: str
    input_mode: Literal["ieee-cis", "ecommerce-sim"]
    is_fraud_predicted: int
    fraud_probability: float
    threshold: float
    predicted_at: datetime
    ai_available: bool
    status: str

    @property
    def risk_level(self) -> str:
        if self.fraud_probability >= 0.7:
            return "high"
        if self.fraud_probability >= 0.3:
            return "medium"
        return "low"

    @property
    def message(self) -> str:
        return "Fraud detected" if self.is_fraud_predicted == 1 else "Transaction appears legitimate"


class PredictionListItem(BaseModel):
    prediction_id: UUID
    transaction_id: Optional[int] = None
    model_version: str
    input_mode: Literal["ieee-cis", "ecommerce-sim"]
    is_fraud_predicted: int
    fraud_probability: float
    threshold: float
    predicted_at: datetime
    ai_available: bool
    status: str


class PredictionsListResponse(BaseModel):
    items: list[PredictionListItem]
    total: int
    limit: int
    offset: int


class PredictionsFilter(BaseModel):
    input_mode: Optional[Literal["ieee-cis", "ecommerce-sim"]] = None
    is_fraud_predicted: Optional[int] = Field(default=None, ge=0, le=1)
    min_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    from_predicted_at: Optional[datetime] = None
    to_predicted_at: Optional[datetime] = None


class PredictionDetail(BaseModel):
    """Full detail of one prediction, including AI explanation if available."""

    prediction_id: UUID
    transaction_id: Optional[int] = None
    model_version: str
    input_mode: Literal["ieee-cis", "ecommerce-sim"]
    input_payload: dict
    is_fraud_predicted: int
    fraud_probability: float
    threshold: float
    risk_level: str
    message: str
    predicted_at: datetime
    ai_available: bool
    ai_explanation: Optional[str] = None
    ai_explanation_at: Optional[datetime] = None
    status: str


class ExplainRequest(BaseModel):
    """Request AI explanation for an existing prediction."""

    question: Optional[str] = None


class ExplainResponse(BaseModel):
    prediction_id: Optional[UUID] = None
    answer: str
    ai_available: bool
    source: Literal["ai-assistant", "ollama-direct", "unavailable"]
    sql_query: Optional[str] = None
    results: Optional[list[dict[str, Any]]] = None


class ServiceStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "unavailable"]
    detail: Optional[str] = None


class SystemStatusResponse(BaseModel):
    api: Literal["ok"]
    model: ServiceStatus
    database: ServiceStatus
    ai: ServiceStatus
    ollama: ServiceStatus