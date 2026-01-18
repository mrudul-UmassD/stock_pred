"""
Server-Sent Events (SSE) streaming endpoint for real-time predictions.
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
import sqlite3
import logging
from datetime import datetime

from .db import get_db_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["streaming"])

async def prediction_stream_generator(horizon: int, interval: int = 2):
    """
    Generate SSE events with latest predictions.
    
    Args:
        horizon: Prediction horizon to stream
        interval: Seconds between updates
        
    Yields:
        SSE formatted strings with prediction data
    """
    logger.info(f"SSE stream started for horizon={horizon}")
    
    try:
        while True:
            try:
                # Fetch latest predictions
                conn = sqlite3.connect(get_db_path())
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
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
                    LIMIT 200
                """
                
                cursor.execute(query, (horizon, horizon))
                rows = cursor.fetchall()
                conn.close()
                
                predictions = [dict(row) for row in rows]
                
                # Format as SSE event
                event_data = {
                    "horizon": horizon,
                    "count": len(predictions),
                    "predictions": predictions,
                    "timestamp": datetime.now().isoformat()
                }
                
                # SSE format: "data: {json}\n\n"
                yield f"event: overview\ndata: {json.dumps(event_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generator: {e}")
                # Send error event
                error_data = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
            
            # Wait before next update
            await asyncio.sleep(interval)
            
    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for horizon={horizon}")
        raise

@router.get("/stream")
async def stream_predictions(
    horizon: int = Query(5, description="Prediction horizon (1, 5, or 20 days)")
):
    """
    Server-Sent Events (SSE) stream for real-time prediction updates.
    
    Args:
        horizon: Prediction horizon to stream
        
    Returns:
        StreamingResponse with SSE events
        
    Events:
        - overview: Latest predictions for all tickers
        - error: Error messages
    """
    if horizon not in [1, 5, 20]:
        return StreamingResponse(
            iter([f"event: error\ndata: {{\"error\": \"Invalid horizon\"}}\n\n"]),
            media_type="text/event-stream"
        )
    
    return StreamingResponse(
        prediction_stream_generator(horizon, interval=2),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
            "Connection": "keep-alive"
        }
    )

# Add keepalive/heartbeat stream (optional)
async def heartbeat_generator():
    """
    Generate heartbeat events to keep connection alive.
    
    Yields:
        SSE heartbeat comments
    """
    while True:
        yield f": heartbeat {datetime.now().isoformat()}\n\n"
        await asyncio.sleep(15)  # Heartbeat every 15 seconds

@router.get("/stream/heartbeat")
async def stream_heartbeat():
    """
    SSE endpoint with just heartbeats for testing connections.
    
    Returns:
        StreamingResponse with heartbeat events
    """
    return StreamingResponse(
        heartbeat_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
