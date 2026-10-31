"""
Phase 31: AI Assistant chat endpoint for the web platform.

Proxies chat questions to the AI Assistant service (port 8001) with direct
Ollama fallback. If a prediction_id is supplied, the question is answered
in the context of that REAL prediction record (model result + input +
metadata). The LLM never overrides the XGBoost result.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from api.config import limiter
from api.database import get_prediction_record, save_ai_explanation
from api.models import ExplainResponse
from api.services.ai_service import AIService

router = APIRouter(tags=["AI Assistant (Phase 31)"])
logger = logging.getLogger(__name__)


def _get_ai_service() -> AIService:
    return AIService()


def _require_question(body: dict[str, Any] | None) -> str:
    if not body or not isinstance(body.get("question"), str) or not body["question"].strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required."
        )
    return body["question"].strip()


@router.post(
    "/ai/chat",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def ai_chat(
    request: Request,
    prediction_id: str | None = Query(
        default=None,
        description="Optional prediction ID for context-bound explanation",
    ),
    body: dict[str, Any] | None = None,
    ai: AIService = Depends(_get_ai_service),
) -> Any:
    """
    Chat with the AI Assistant.

    Body: { "question": "..." }

    If prediction_id is provided, the answer is grounded in the stored
    prediction record (real XGBoost result). Otherwise the question is
    answered as a general question (via the AI Assistant service with
    Ollama fallback).
    """
    question = _require_question(body)

    if prediction_id:
        try:
            record = get_prediction_record(prediction_id)
        except Exception as exc:  # database unavailable
            logger.exception("Failed to read prediction %s", prediction_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable.",
            ) from exc

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found.",
            )

        try:
            result = ai.explain(
                prediction_id=prediction_id,
                record=record,
                question=question,
            )
        except Exception as exc:  # never break the prediction page
            logger.exception("AI context explanation failed for %s", prediction_id)
            result = {
                "answer": (
                    "AI Assistant khong the xu ly yeu cau nay. Du doan XGBoost "
                    "con luu tru va co the xem lai, nhung chua co giai thich tu AI."
                ),
                "ai_available": False,
                "source": "unavailable",
            }

        try:
            save_ai_explanation(
                prediction_id=prediction_id,
                explanation=result["answer"],
                ai_available=bool(result.get("ai_available")),
            )
        except Exception as exc:
            logger.exception(
                "Failed to persist AI explanation for %s", prediction_id
            )

        return {
            "prediction_id": prediction_id,
            "answer": result["answer"],
            "ai_available": bool(result.get("ai_available")),
            "source": result.get("source", "unavailable"),
        }

    # General question: route through AI Data Analyst (knowledge + data)
    try:
        result = ai.answer_general(question=question)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("General AI chat failed")
        result = {
            "answer": (
                "AI Assistant va Ollama khong hoat dong luc nay. "
                "Vui long thu lai sau."
            ),
            "ai_available": False,
            "source": "unavailable",
        }

    return {
        "prediction_id": None,
        "answer": result["answer"],
        "ai_available": bool(result.get("ai_available")),
        "source": result.get("source", "unavailable"),
        "sql_query": result.get("sql_query"),
        "results": result.get("results"),
    }
