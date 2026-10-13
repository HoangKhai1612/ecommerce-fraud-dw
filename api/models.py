"""Pydantic schemas for the fraud detection API."""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class TransactionRaw(BaseModel):
    """
    Raw transaction input for prediction.

    These are the columns from marts.fact_transactions that are needed
    for feature engineering. The full table has 339 v* columns, 38 id_*
    columns, and other features. We accept a flexible dict for the rest.
    """

    model_config = ConfigDict(extra="allow")

    transaction_id: int = Field(gt=0)
    transaction_dt: int = Field(ge=0)
    transaction_amt: float = Field(gt=0, allow_inf_nan=False)
    product_cd: str = Field(min_length=1, max_length=10)
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