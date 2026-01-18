"""
API routes for predictions endpoints.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import sqlite3
import logging

from .db import get_db_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["predictions"])

@router.get("/predictions/overview")
async def get_predictions_overview(
    horizon: int = Query(5, description="Prediction horizon (1, 5, or 20 days)"),
    limit: int = Query(200, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get overview of latest predictions for all tickers.
    
    Args:
        horizon: Prediction horizon (1, 5, or 20)
        limit: Maximum number of results
        
    Returns:
        List of latest predictions for each ticker at the specified horizon
    """
    try:
        # Validate horizon
        if horizon not in [1, 5, 20]:
            raise HTTPException(status_code=400, detail="Horizon must be 1, 5, or 20")
        
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get latest prediction for each ticker at specified horizon
        query = """
            WITH LatestPredictions AS (
                SELECT 
                    ticker,
                    MAX(ts) as latest_ts
                FROM predictions
                WHERE horizon = ?
                GROUP BY ticker
            )
            SELECT 
                p.ts,
                p.ticker,
                p.horizon,
                p.direction,
                p.prob_up,
                p.prob_down,
                p.prob_flat,
                p.expected_return,
                p.model_version
            FROM predictions p
            INNER JOIN LatestPredictions lp 
                ON p.ticker = lp.ticker AND p.ts = lp.latest_ts
            WHERE p.horizon = ?
            ORDER BY p.prob_up DESC
            LIMIT ?
        """
        
        cursor.execute(query, (horizon, horizon, limit))
        rows = cursor.fetchall()
        conn.close()
        
        predictions = [dict(row) for row in rows]
        
        return {
            "horizon": horizon,
            "count": len(predictions),
            "predictions": predictions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/latest")
async def get_latest_prediction(
    ticker: str = Query(..., description="Stock ticker symbol"),
    horizon: int = Query(5, description="Prediction horizon (1, 5, or 20 days)")
):
    """
    Get latest prediction for a specific ticker and horizon.
    
    Args:
        ticker: Stock ticker symbol
        horizon: Prediction horizon
        
    Returns:
        Latest prediction for the ticker
    """
    try:
        # Validate inputs
        if horizon not in [1, 5, 20]:
            raise HTTPException(status_code=400, detail="Horizon must be 1, 5, or 20")
        
        if not ticker or len(ticker) > 10:
            raise HTTPException(status_code=400, detail="Invalid ticker symbol")
        
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ts,
                ticker,
                horizon,
                direction,
                prob_up,
                prob_down,
                prob_flat,
                expected_return,
                model_version
            FROM predictions
            WHERE ticker = ? AND horizon = ?
            ORDER BY ts DESC
            LIMIT 1
        """
        
        cursor.execute(query, (ticker.upper(), horizon))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction found for {ticker} at horizon {horizon}"
            )
        
        return dict(row)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/history")
async def get_prediction_history(
    ticker: str = Query(..., description="Stock ticker symbol"),
    horizon: int = Query(5, description="Prediction horizon (1, 5, or 20 days)"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum number of results")
):
    """
    Get historical predictions for a specific ticker and horizon.
    
    Args:
        ticker: Stock ticker symbol
        horizon: Prediction horizon
        limit: Maximum number of results
        
    Returns:
        Historical predictions ordered by timestamp (newest first)
    """
    try:
        # Validate inputs
        if horizon not in [1, 5, 20]:
            raise HTTPException(status_code=400, detail="Horizon must be 1, 5, or 20")
        
        if not ticker or len(ticker) > 10:
            raise HTTPException(status_code=400, detail="Invalid ticker symbol")
        
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ts,
                ticker,
                horizon,
                direction,
                prob_up,
                prob_down,
                prob_flat,
                expected_return,
                model_version
            FROM predictions
            WHERE ticker = ? AND horizon = ?
            ORDER BY ts DESC
            LIMIT ?
        """
        
        cursor.execute(query, (ticker.upper(), horizon, limit))
        rows = cursor.fetchall()
        conn.close()
        
        predictions = [dict(row) for row in rows]
        
        return {
            "ticker": ticker.upper(),
            "horizon": horizon,
            "count": len(predictions),
            "predictions": predictions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
