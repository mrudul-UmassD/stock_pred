"""
Data sources module for fetching stock and macro data.

Implements:
- yfinance for stock OHLCV data
- Stooq CSV fallback
- FRED API for macro indicators
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import yfinance as yf
import requests
from io import StringIO
from fredapi import Fred
import os

logger = logging.getLogger(__name__)

def fetch_yfinance_ohlcv(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Yahoo Finance.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        interval: Data interval ('1d' for daily)
        
    Returns:
        DataFrame with Date index and OHLCV columns, or None if fetch fails
    """
    try:
        logger.info(f"Fetching yfinance data for {ticker}")
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end, interval=interval)
        
        if df.empty:
            logger.warning(f"No data returned from yfinance for {ticker}")
            return None
        
        # Standardize column names
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Keep only OHLCV columns
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        df = df[[col for col in columns_to_keep if col in df.columns]]
        
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        logger.info(f"✓ Fetched {len(df)} rows for {ticker} from yfinance")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching yfinance data for {ticker}: {e}")
        return None

def fetch_stooq_ohlcv(
    ticker: str,
    start: str,
    end: str
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Stooq as fallback.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        
    Returns:
        DataFrame with Date index and OHLCV columns, or None if fetch fails
    """
    try:
        logger.info(f"Fetching Stooq data for {ticker}")
        
        # Convert dates to Stooq format (YYYYMMDD)
        start_str = pd.to_datetime(start).strftime('%Y%m%d')
        end_str = pd.to_datetime(end).strftime('%Y%m%d')
        
        # Stooq URL format
        url = f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&d1={start_str}&d2={end_str}&i=d"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty or 'Date' not in df.columns:
            logger.warning(f"No valid data returned from Stooq for {ticker}")
            return None
        
        # Standardize columns
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Keep only OHLCV columns and sort by date
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        df = df[[col for col in columns_to_keep if col in df.columns]]
        df = df.sort_index()
        
        logger.info(f"✓ Fetched {len(df)} rows for {ticker} from Stooq")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching Stooq data for {ticker}: {e}")
        return None

def fetch_ohlcv_with_fallback(
    ticker: str,
    start: str,
    end: str
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data with automatic fallback to Stooq if yfinance fails.
    
    Args:
        ticker: Stock symbol
        start: Start date
        end: End date
        
    Returns:
        DataFrame with OHLCV data or None if both sources fail
    """
    # Try yfinance first
    df = fetch_yfinance_ohlcv(ticker, start, end)
    
    if df is not None and len(df) > 0:
        return df
    
    # Fallback to Stooq
    logger.info(f"Falling back to Stooq for {ticker}")
    df = fetch_stooq_ohlcv(ticker, start, end)
    
    if df is not None and len(df) > 0:
        return df
    
    logger.error(f"Failed to fetch data for {ticker} from all sources")
    return None

def fetch_fred_series(
    series_ids: List[str],
    start: str,
    end: str,
    api_key: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Fetch multiple macro series from FRED API.
    
    Args:
        series_ids: List of FRED series IDs (e.g., ['FEDFUNDS', 'CPIAUCSL'])
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        api_key: FRED API key (if not provided, reads from environment)
        
    Returns:
        DataFrame with date index and series as columns, or None if fetch fails
    """
    try:
        # Get API key
        if api_key is None:
            api_key = os.environ.get('FRED_API_KEY')
            
        if not api_key:
            logger.error("FRED_API_KEY not found in environment")
            return None
        
        fred = Fred(api_key=api_key)
        logger.info(f"Fetching {len(series_ids)} FRED series")
        
        # Fetch each series
        series_data = {}
        for series_id in series_ids:
            try:
                series = fred.get_series(
                    series_id,
                    observation_start=start,
                    observation_end=end
                )
                series_data[series_id] = series
                logger.info(f"  ✓ Fetched {series_id}: {len(series)} observations")
            except Exception as e:
                logger.warning(f"  ✗ Failed to fetch {series_id}: {e}")
                continue
        
        if not series_data:
            logger.error("No FRED series data fetched")
            return None
        
        # Combine into DataFrame
        df = pd.DataFrame(series_data)
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        logger.info(f"✓ Combined FRED data: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching FRED data: {e}")
        return None

if __name__ == "__main__":
    # Test data sources
    logging.basicConfig(level=logging.INFO)
    
    start = "2023-01-01"
    end = "2024-01-01"
    
    # Test yfinance
    print("\n" + "="*60)
    print("Testing yfinance...")
    df = fetch_yfinance_ohlcv("AAPL", start, end)
    if df is not None:
        print(df.head())
        print(f"Shape: {df.shape}")
    
    # Test Stooq fallback
    print("\n" + "="*60)
    print("Testing Stooq...")
    df = fetch_stooq_ohlcv("AAPL", start, end)
    if df is not None:
        print(df.head())
        print(f"Shape: {df.shape}")
    
    # Test FRED
    print("\n" + "="*60)
    print("Testing FRED...")
    fred_series = ['FEDFUNDS', 'CPIAUCSL', 'UNRATE']
    df = fetch_fred_series(fred_series, start, end)
    if df is not None:
        print(df.head())
        print(f"Shape: {df.shape}")
