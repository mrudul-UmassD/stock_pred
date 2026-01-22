"""
Batch prediction runner for all US stocks.

Handles large-scale predictions with:
- Parallel processing
- Progress tracking
- Error handling
- Database batching
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

import pandas as pd

from app.services.data_sources import fetch_ohlcv_with_fallback
from app.services.features import create_feature_matrix
from app.services.inference import load_artifacts, predict_for_ticker
from app.services.market_data import get_market_universe
from app.db import get_db_path, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # Process N stocks at a time
MAX_WORKERS = 5  # Parallel threads


def predict_single_ticker(ticker: str, horizons: List[int], model_version: str) -> Dict:
    """
    Generate predictions for a single ticker.
    
    Args:
        ticker: Stock symbol
        horizons: List of prediction horizons
        model_version: Model version string
        
    Returns:
        Dictionary with predictions or error
    """
    try:
        # Fetch data (1 year lookback for features)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        ohlcv_df = fetch_ohlcv_with_fallback(
            ticker,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        if ohlcv_df is None or ohlcv_df.empty:
            return {
                'ticker': ticker,
                'status': 'error',
                'error': 'No data available'
            }
        
        # Compute features
        features_df = create_feature_matrix(ohlcv_df, macro_df=None)
        
        if features_df.empty:
            return {
                'ticker': ticker,
                'status': 'error',
                'error': 'Feature computation failed'
            }
        
        predictions = []
        
        for horizon in horizons:
            pred = predict_for_ticker(ticker, horizon, features_df)
            
            if pred:
                pred['model_version'] = model_version
                pred['ticker'] = ticker
                pred['ts'] = datetime.now().isoformat()
                pred['horizon'] = horizon
                predictions.append(pred)
        
        if not predictions:
            return {
                'ticker': ticker,
                'status': 'error',
                'error': 'All predictions failed'
            }
        
        return {
            'ticker': ticker,
            'status': 'success',
            'predictions': predictions
        }
    
    except Exception as e:
        logger.error(f"Failed to predict {ticker}: {e}")
        return {
            'ticker': ticker,
            'status': 'error',
            'error': str(e)
        }


def save_predictions_batch(predictions: List[Dict], conn: sqlite3.Connection):
    """
    Save a batch of predictions to database.
    
    Args:
        predictions: List of prediction dictionaries
        conn: Database connection
    """
    cursor = conn.cursor()
    
    for pred in predictions:
        cursor.execute("""
            INSERT INTO predictions (
                ts, ticker, horizon, direction,
                prob_up, prob_down, prob_flat,
                expected_return, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pred['ts'],
            pred['ticker'],
            pred['horizon'],
            pred['direction'],
            pred['prob_up'],
            pred['prob_down'],
            pred['prob_flat'],
            pred.get('expected_return', 0.0),
            pred['model_version']
        ))
    
    conn.commit()


def run_batch_predictions(
    tickers: List[str],
    horizons: List[int] = [1, 5, 20],
    universe_type: str = "sp500",
    max_tickers: int = None
):
    """
    Run predictions for a batch of tickers.
    
    Args:
        tickers: List of ticker symbols
        horizons: Prediction horizons
        universe_type: Type of universe being predicted
        max_tickers: Maximum number of tickers to process (for testing)
    """
    logger.info("="*60)
    logger.info(f"Starting batch prediction run ({universe_type})")
    logger.info(f"Time: {datetime.now()}")
    logger.info("="*60)
    
    # Initialize database
    init_db()
    conn = sqlite3.connect(get_db_path())
    
    # Load model artifacts
    model, feature_schema, model_meta = load_artifacts()
    model_version = model_meta.get('version', 'unknown')
    
    logger.info(f"Model version: {model_version}")
    logger.info(f"Horizons: {horizons}")
    
    # Limit tickers if specified
    if max_tickers:
        tickers = tickers[:max_tickers]
    
    logger.info(f"Processing {len(tickers)} tickers")
    
    # Track statistics
    start_time = datetime.now()
    success_count = 0
    error_count = 0
    total_predictions = 0
    
    # Process in batches
    for batch_start in range(0, len(tickers), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(tickers))
        batch = tickers[batch_start:batch_end]
        
        logger.info(f"\nBatch {batch_start//BATCH_SIZE + 1}: Processing tickers {batch_start+1}-{batch_end}")
        
        batch_predictions = []
        
        # Process batch with thread pool
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_ticker = {
                executor.submit(predict_single_ticker, ticker, horizons, model_version): ticker
                for ticker in batch
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        success_count += 1
                        batch_predictions.extend(result['predictions'])
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Exception processing {ticker}: {e}")
                    error_count += 1
        
        # Save batch to database
        if batch_predictions:
            save_predictions_batch(batch_predictions, conn)
            total_predictions += len(batch_predictions)
            logger.info(f"  ✓ Saved {len(batch_predictions)} predictions")
        
        # Progress update
        progress_pct = (batch_end / len(tickers)) * 100
        logger.info(f"  Progress: {progress_pct:.1f}% ({success_count} success, {error_count} errors)")
    
    # Close connection
    conn.close()
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "="*60)
    logger.info("Batch prediction run complete!")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Tickers processed: {success_count}/{len(tickers)}")
    logger.info(f"Failed: {error_count}")
    logger.info(f"Total predictions inserted: {total_predictions}")
    logger.info(f"Throughput: {success_count/(duration/60):.1f} tickers/min")
    logger.info("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run batch predictions for US stocks')
    parser.add_argument(
        '--universe',
        type=str,
        default='sp500',
        choices=['sp500', 'nasdaq100', 'all'],
        help='Stock universe to predict'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of tickers (for testing)'
    )
    parser.add_argument(
        '--horizons',
        type=int,
        nargs='+',
        default=[1, 5, 20],
        help='Prediction horizons'
    )
    
    args = parser.parse_args()
    
    # Get ticker universe
    logger.info(f"Fetching {args.universe} universe...")
    tickers = get_market_universe(args.universe)
    
    if not tickers:
        logger.error("No tickers found!")
        return
    
    # Run predictions
    run_batch_predictions(
        tickers=tickers,
        horizons=args.horizons,
        universe_type=args.universe,
        max_tickers=args.limit
    )


if __name__ == "__main__":
    main()
