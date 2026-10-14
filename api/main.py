"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from api.config import API_HOST, API_PORT, limiter
from api.inference import load_inference_pipeline
from api.routes import health, predict, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load model on startup."""
    # Startup
    try:
        load_inference_pipeline()
    except Exception as e:
        # Log but don't crash - health endpoint will show not ready
        print(f"Warning: Failed to load model on startup: {e}")
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(
    title="E-commerce Fraud Detection API",
    description=(
        "REST API for the fraud detection Data Warehouse project. "
        "Provides health checks, transaction lookups, saved predictions, "
        "and real-time fraud scoring using the Phase 16 XGBoost model."
    ),
    version="1.0.0",
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