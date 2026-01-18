"""
Prediction runner script.

Loads model artifacts, fetches latest data, generates predictions,
and stores them in the database.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import sqlite3
from datetime import datetime, timedelta
import logging
import os

import pandas as pd

from app.services.data_sources import fetch_ohlcv_with_fallback, fetch_fred_series
from app.services.features import create_feature_matrix
from app.services.inference import load_artifacts, predict_for_ticker, get_model_info
from app.db import get_db_path, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FRED series for macro data
FRED_SERIES = [
    'FEDFUNDS',   # Federal Funds Rate
    'CPIAUCSL',   # CPI
    'UNRATE',     # Unemployment Rate
    'DGS10',      # 10-Year Treasury
    'DGS2',       # 2-Year Treasury
    'T10Y2Y',     # 10Y-2Y Spread
    'VIXCLS',     # VIX
    'USREC'       # Recession Indicator
]

def load_tickers_from_meta() -> list:
    """
    Load ticker list from model_meta.json.
    
    Returns:
        List of tickers or default list if not found
    """
    try:
        meta_path = Path(__file__).parent.parent.parent / "artifacts" / "model_meta.json"
        
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                tickers = meta.get('tickers', [])
                logger.info(f"✓ Loaded {len(tickers)} tickers from model_meta.json")
                return tickers
        else:
            logger.warning("model_meta.json not found, using default tickers")
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
            
    except Exception as e:
        logger.error(f"Error loading tickers from meta: {e}")
        return ['AAPL', 'MSFT', 'GOOGL']

def insert_prediction(conn, ticker: str, horizon: int, prediction: dict, model_version: str):
    """
    Insert prediction into database.
    
    Args:
        conn: Database connection
        ticker: Stock symbol
        horizon: Prediction horizon
        prediction: Prediction dict from inference
        model_version: Model version string
    """
    cursor = conn.cursor()
    
    ts = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO predictions 
        (ts, ticker, horizon, direction, prob_up, prob_down, prob_flat, expected_return, model_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts,
        ticker,
        horizon,
        prediction['direction'],
        prediction['prob_up'],
        prediction['prob_down'],
        prediction['prob_flat'],
        prediction['expected_return'],
        model_version
    ))

def run_predictions(use_dummy: bool = False):
    """
    Run predictions for all tickers and horizons.
    
    Args:
        use_dummy: Use dummy predictions if model not available
    """
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("Starting prediction run...")
    logger.info(f"Time: {start_time}")
    logger.info("="*60)
    
    # Initialize database
    init_db()
    
    # Load model artifacts
    model, schema, meta = load_artifacts()
    
    if model is None and not use_dummy:
        logger.error("❌ Model not found and dummy mode not enabled")
        logger.error("   Run the training notebook first or use --dummy flag")
        return
    
    # Get model info
    model_info = get_model_info()
    model_version = meta.get('model_version', 'unknown') if meta else 'dummy'
    horizons = meta.get('horizons', [1, 5, 20]) if meta else [1, 5, 20]
    
    logger.info(f"Model version: {model_version}")
    logger.info(f"Horizons: {horizons}")
    
    # Load tickers
    tickers = load_tickers_from_meta()
    logger.info(f"Processing {len(tickers)} tickers")
    
    # Fetch macro data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of data
    
    logger.info(f"\nFetching macro data ({start_date.date()} to {end_date.date()})...")
    macro_df = fetch_fred_series(
        FRED_SERIES,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    if macro_df is None:
        logger.warning("⚠ Failed to fetch macro data, continuing without it")
    
    # Connect to database
    conn = sqlite3.connect(get_db_path())
    
    # Process each ticker
    successful = 0
    failed = 0
    total_predictions = 0
    
    for i, ticker in enumerate(tickers, 1):
        logger.info(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Fetch OHLCV data
            ohlcv_df = fetch_ohlcv_with_fallback(
                ticker,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if ohlcv_df is None or len(ohlcv_df) < 100:
                logger.warning(f"  ⚠ Insufficient data for {ticker}, skipping")
                failed += 1
                continue
            
            # Create feature matrix
            features_df = create_feature_matrix(ohlcv_df, macro_df)
            
            if features_df.empty:
                logger.warning(f"  ⚠ Empty feature matrix for {ticker}, skipping")
                failed += 1
                continue
            
            # Generate predictions for each horizon
            for horizon in horizons:
                prediction = predict_for_ticker(
                    ticker,
                    horizon,
                    features_df,
                    use_dummy_if_missing=use_dummy
                )
                
                if prediction:
                    insert_prediction(conn, ticker, horizon, prediction, model_version)
                    total_predictions += 1
                    logger.info(f"  ✓ H{horizon}: {prediction['direction']} (prob={max(prediction['prob_up'], prediction['prob_down'], prediction['prob_flat']):.2f})")
            
            successful += 1
            
        except Exception as e:
            logger.error(f"  ✗ Error processing {ticker}: {e}")
            failed += 1
            continue
    
    # Commit and close
    conn.commit()
    conn.close()
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "="*60)
    logger.info("Prediction run complete!")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Tickers processed: {successful}/{len(tickers)}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total predictions inserted: {total_predictions}")
    logger.info(f"Latest timestamp: {datetime.now().isoformat()}")
    logger.info("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run stock predictions")
    parser.add_argument(
        '--dummy',
        action='store_true',
        help='Use dummy predictions if model not available (dev mode)'
    )
    
    args = parser.parse_args()
    
    run_predictions(use_dummy=args.dummy)
