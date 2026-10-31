"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from api.config import API_HOST, API_PORT, limiter
from api.database import check_database, ensure_history_table
from api.inference import load_inference_pipeline
from api.inference_manual import load_manual_pipeline
from api.routes import health, predict, transactions
from api.routes import predictions as predictions_route
from api.routes import ai as ai_route
from api.routes import monitoring as monitoring_route
from api.routes import batch as batch_route
from api.routes import models as models_route
from api.routes import monitoring as monitoring_route
from api.routes import batch as batch_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load model and init history table on startup."""
    # Startup
    try:
        load_inference_pipeline()
    except Exception as e:
        # Log but don't crash - health endpoint will show not ready
        print(f"Warning: Failed to load model on startup: {e}")
    try:
        load_manual_pipeline()
        print("Manual model loaded: xgboost-manual-v1")
    except Exception as e:
        print(f"Warning: Failed to load manual model on startup: {e}")
    try:
        ensure_history_table()
        print("History table ensured: marts.web_test_history")
    except Exception as e:
        print(f"Warning: Failed to ensure history table: {e}")
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(
    title="E-commerce Fraud Detection API",
    description=(
        "REST API for the fraud detection Data Warehouse project. "
        "Provides health checks, transaction lookups, saved predictions, "
        "real-time fraud scoring using the Phase 16 XGBoost model, and the "
        "Phase 31 integrated testing platform (prediction history, AI "
        "explanation, system status)."
    ),
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - configure via environment in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(transactions.router)
app.include_router(predict.router)
app.include_router(predictions_route.router)
app.include_router(ai_route.router)
app.include_router(monitoring_route.router)
app.include_router(batch_route.router)
app.include_router(models_route.router)


@app.get("/")
def root():
    return {
        "service": "fraud-detection-api",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)