"""Health and readiness endpoints."""

from typing import Any, Literal

import httpx
from fastapi import APIRouter

from api.config import AI_ASSISTANT_BASE_URL, LLM_MODEL, OLLAMA_BASE_URL
from api.database import check_database
from api.models import HealthResponse, ReadinessResponse, ServiceStatus, SystemStatusResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Check whether the API process is responding."""
    return {
        "status": "ok",
        "service": "fraud-detection-api",
    }


@router.get("/ready", response_model=ReadinessResponse)
def readiness():
    """Check whether the API can access its required database."""
    database_ready = check_database()

    return {
        "status": "ready" if database_ready else "not_ready",
        "database": "ok" if database_ready else "unavailable",
    }


@router.get("/system/status", response_model=SystemStatusResponse)
def system_status() -> Any:  # type: ignore[valid-type]
    """
    System status for the web dashboard.

    Separates service liveness from functional readiness: AI/OLLAMA timeout
    does not disable prediction when XGBoost is ready.
    """
    from api.inference import get_inference_pipeline

    db_ok = check_database()

    # Model readiness: try to ensure the pipeline can load (artifacts present).
    model_status: Literal["ok", "degraded", "unavailable"] = "ok"
    model_detail = "Artifacts loaded"
    try:
        pipeline = get_inference_pipeline()
        if not pipeline._loaded:
            pipeline.load()
        if not pipeline._loaded or pipeline.model is None:
            model_status = "unavailable"
            model_detail = "Model object not available"
        elif pipeline.feature_cols is None:
            model_status = "unavailable"
            model_detail = "Feature schema not loaded"
    except Exception as exc:  # noqa: BLE001
        model_status = "unavailable"
        model_detail = str(exc)

    ai_status: Literal["ok", "degraded", "unavailable"] = "unavailable"
    ai_detail = "AI Assistant not checked"
    ollama_status: Literal["ok", "degraded", "unavailable"] = "unavailable"
    ollama_detail = "Ollama not checked"

    try:
        with httpx.Client(timeout=5.0) as client:
            try:
                r = client.get(f"{AI_ASSISTANT_BASE_URL}/health")
                if r.status_code == 200:
                    ai_status = "ok"
                    ai_detail = "AI Assistant reachable"
                else:
                    ai_status = "degraded"
                    ai_detail = f"AI Assistant HTTP {r.status_code}"
            except Exception:
                ai_status = "unavailable"
                ai_detail = "AI Assistant unreachable"

            try:
                r = client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if r.status_code == 200:
                    tags = r.json().get("models", [])
                    if any(m.get("name", "").startswith(LLM_MODEL) for m in tags):
                        ollama_status = "ok"
                        ollama_detail = f"Ollama reachable, model {LLM_MODEL} present"
                    else:
                        ollama_status = "degraded"
                        ollama_detail = f"Ollama reachable, model {LLM_MODEL} not found"
                else:
                    ollama_status = "degraded"
                    ollama_detail = f"Ollama HTTP {r.status_code}"
            except Exception:
                ollama_status = "unavailable"
                ollama_detail = "Ollama unreachable"
    except Exception:
        pass

    return {
        "api": "ok",
        "model": ServiceStatus(name="xgboost", status=model_status, detail=model_detail),
        "database": ServiceStatus(
            name="postgresql",
            status="ok" if db_ok else "unavailable",
            detail="marts schema reachable" if db_ok else "database unreachable",
        ),
        "ai": ServiceStatus(name="ai-assistant", status=ai_status, detail=ai_detail),
        "ollama": ServiceStatus(name="ollama", status=ollama_status, detail=ollama_detail),
    }