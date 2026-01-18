"""
Database connection and schema management for predictions storage.
"""

import sqlite3
import aiosqlite
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "db" / "predictions.db"

def get_db_path() -> Path:
    """Get the database file path."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH

async def get_db():
    """Get async database connection."""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    return db

def init_db():
    """
    Initialize database schema.
    Creates predictions table if it doesn't exist.
    """
    db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            ticker TEXT NOT NULL,
            horizon INTEGER NOT NULL,
            direction TEXT NOT NULL,
            prob_up REAL,
            prob_down REAL,
            prob_flat REAL,
            expected_return REAL,
            model_version TEXT,
            UNIQUE(ts, ticker, horizon)
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ticker_horizon 
        ON predictions(ticker, horizon)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ts 
        ON predictions(ts DESC)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f"✓ Database initialized at {db_path}")
    return db_path

def check_db_health() -> bool:
    """
    Check if database is accessible and healthy.
    
    Returns:
        bool: True if database is healthy
    """
    try:
        db_path = get_db_path()
        if not db_path.exists():
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def get_model_version() -> Optional[str]:
    """
    Get the latest model version from database.
    
    Returns:
        str: Model version or None if no predictions exist
    """
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT model_version 
            FROM predictions 
            WHERE model_version IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting model version: {e}")
        return None

if __name__ == "__main__":
    # Test database initialization
    logging.basicConfig(level=logging.INFO)
    init_db()
    print(f"Database health: {check_db_health()}")
    print(f"Model version: {get_model_version()}")
