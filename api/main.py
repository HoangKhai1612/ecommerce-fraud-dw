from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Fraud Detection API", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fraud-dw-api"}

@app.get("/")
async def root():
    return {
        "message": "Fraud Detection Data Warehouse API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
