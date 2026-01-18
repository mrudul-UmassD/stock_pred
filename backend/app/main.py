"""
FastAPI application main entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from .db import init_db, check_db_health, get_model_version
from .routes import router as predictions_router
from .stream import router as stream_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Stock Prediction API",
    description="Real-time stock movement prediction API with SSE streaming",
    version="1.0.0"
)

# Include routers
app.include_router(predictions_router)
app.include_router(stream_router)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting up Stock Prediction API...")
    init_db()
    logger.info("✓ Startup complete")

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Server health status including database and model info
    """
    db_ok = check_db_health()
    model_version = get_model_version()
    
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "time": datetime.now().isoformat(),
        "db_ok": db_ok,
        "model_version": model_version or "not_trained"
    }

@app.get("/api/tickers")
async def get_tickers():
    """
    Get list of distinct tickers in database.
    
    Returns:
        dict: List of available tickers
    """
    try:
        from .db import get_db_path
        import sqlite3
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM predictions ORDER BY ticker")
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return {
            "tickers": tickers,
            "count": len(tickers)
        }
    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Stock Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tickers": "/api/tickers",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
