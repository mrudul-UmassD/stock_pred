"""
Feature engineering module for technical and macro indicators.

All functions prevent data leakage by using only past information.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

def compute_returns(df: pd.DataFrame, price_col: str = 'close') -> pd.DataFrame:
    """
    Compute simple and log returns.
    
    Args:
        df: DataFrame with OHLCV data
        price_col: Column to use for returns calculation
        
    Returns:
        DataFrame with added return columns
    """
    df = df.copy()
    df['return_1d'] = df[price_col].pct_change()
    df['log_return_1d'] = np.log(df[price_col] / df[price_col].shift(1))
    return df

def compute_rolling_statistics(
    df: pd.DataFrame,
    windows: List[int] = [5, 20, 60],
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Compute rolling mean and volatility.
    
    Args:
        df: DataFrame with price data
        windows: List of window sizes
        price_col: Column to use
        
    Returns:
        DataFrame with rolling statistics
    """
    df = df.copy()
    
    for window in windows:
        # Rolling mean
        df[f'sma_{window}'] = df[price_col].rolling(window=window).mean()
        
        # Rolling volatility (std of returns)
        df[f'vol_{window}'] = df['return_1d'].rolling(window=window).std()
        
        # Price relative to rolling mean
        df[f'price_to_sma_{window}'] = df[price_col] / df[f'sma_{window}']
    
    return df

def compute_rsi(df: pd.DataFrame, period: int = 14, price_col: str = 'close') -> pd.DataFrame:
    """
    Compute Relative Strength Index (RSI).
    
    Args:
        df: DataFrame with price data
        period: RSI period
        price_col: Column to use
        
    Returns:
        DataFrame with RSI column
    """
    df = df.copy()
    
    # Calculate price changes
    delta = df[price_col].diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period, min_periods=period).mean()
    avg_losses = losses.rolling(window=period, min_periods=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    return df

def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Compute MACD (Moving Average Convergence Divergence).
    
    Args:
        df: DataFrame with price data
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        price_col: Column to use
        
    Returns:
        DataFrame with MACD columns
    """
    df = df.copy()
    
    # Calculate EMAs
    ema_fast = df[price_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[price_col].ewm(span=slow, adjust=False).mean()
    
    # MACD line
    df['macd'] = ema_fast - ema_slow
    
    # Signal line
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    # MACD histogram
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df

def compute_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Compute Bollinger Bands.
    
    Args:
        df: DataFrame with price data
        period: Rolling window period
        num_std: Number of standard deviations
        price_col: Column to use
        
    Returns:
        DataFrame with Bollinger Band columns
    """
    df = df.copy()
    
    # Middle band (SMA)
    sma = df[price_col].rolling(window=period).mean()
    std = df[price_col].rolling(window=period).std()
    
    # Upper and lower bands
    df['bb_upper'] = sma + (std * num_std)
    df['bb_lower'] = sma - (std * num_std)
    df['bb_middle'] = sma
    
    # Band width (volatility indicator)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    # %B (price position within bands)
    df['bb_pct'] = (df[price_col] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    return df

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Compute Average True Range (ATR) - approximate version.
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
        
    Returns:
        DataFrame with ATR column
    """
    df = df.copy()
    
    # True Range components
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    # True Range
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Average True Range
    df[f'atr_{period}'] = tr.rolling(window=period).mean()
    
    return df

def compute_market_regime_features(
    df: pd.DataFrame,
    spy_returns: Optional[pd.Series] = None,
    windows: List[int] = [20, 60]
) -> pd.DataFrame:
    """
    Compute market regime features (beta, correlation, drawdown).
    
    Args:
        df: DataFrame with stock data and returns
        spy_returns: SPY returns for beta calculation (optional)
        windows: Rolling window sizes
        
    Returns:
        DataFrame with market regime features
    """
    df = df.copy()
    
    # Drawdown from rolling maximum
    for window in windows:
        rolling_max = df['close'].rolling(window=window, min_periods=1).max()
        df[f'drawdown_{window}'] = (df['close'] - rolling_max) / rolling_max
    
    # Beta vs SPY (if provided)
    if spy_returns is not None and 'return_1d' in df.columns:
        for window in windows:
            # Align indices
            aligned = pd.DataFrame({
                'stock': df['return_1d'],
                'spy': spy_returns
            }).dropna()
            
            if len(aligned) > window:
                # Rolling covariance and variance
                cov = aligned['stock'].rolling(window=window).cov(aligned['spy'])
                var = aligned['spy'].rolling(window=window).var()
                beta = cov / var
                df[f'beta_{window}'] = beta
    
    return df

def compute_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators matching training feature names.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all technical features
    """
    logger.info("Computing technical features...")
    
    df = df.copy()
    
    # Returns (using consistent names with training)
    df = compute_returns(df)
    df['returns_1d'] = df['return_1d']  # Alias for consistency
    df['returns_5d'] = df['close'].pct_change(5)
    df['returns_20d'] = df['close'].pct_change(20)
    
    # Volume features
    df['volume_change'] = df['volume'].pct_change()
    df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ma_ratio'] = df['volume'] / df['volume_ma_20']
    
    # Rolling statistics
    df = compute_rolling_statistics(df, windows=[5, 20, 60])
    df['ma_5'] = df['sma_5']  # Alias for consistency
    df['ma_20'] = df['sma_20']  # Alias for consistency
    df['ma_ratio'] = df['ma_5'] / df['ma_20']
    
    # Technical indicators
    rsi_df = compute_rsi(df, period=14)
    df['rsi_14'] = rsi_df['rsi_14']
    
    macd_df = compute_macd(df)
    df['macd'] = macd_df['macd']
    df['macd_signal'] = macd_df['macd_signal']
    
    bb_df = compute_bollinger_bands(df, period=20)
    df['bb_upper'] = bb_df['bb_upper']
    df['bb_lower'] = bb_df['bb_lower']
    df['bb_middle'] = bb_df['bb_middle']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    atr_df = compute_atr(df, period=14)
    df['atr_14'] = atr_df['atr_14']
    df['atr_ratio'] = df['atr_14'] / df['close']
    
    # Market regime
    df = compute_market_regime_features(df, windows=[20, 60])
    
    logger.info(f"✓ Technical features computed: {df.shape[1]} columns")
    return df

def align_macro_features(
    features_df: pd.DataFrame,
    macro_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Align and forward-fill macro features to daily frequency.
    
    CRITICAL: Forward-fill only uses past values (no look-ahead).
    
    Args:
        features_df: DataFrame with stock features (daily frequency)
        macro_df: DataFrame with macro series (various frequencies)
        
    Returns:
        DataFrame with aligned macro features
    """
    logger.info("Aligning macro features...")
    
    # Ensure both have datetime index
    features_df = features_df.copy()
    macro_df = macro_df.copy()
    
    # Reindex macro data to match features dates
    # Forward-fill fills today with most recent past value (no leakage)
    macro_aligned = macro_df.reindex(
        features_df.index,
        method='ffill'  # Forward fill = use past values only
    )
    
    # Add macro columns to features
    for col in macro_aligned.columns:
        features_df[f'macro_{col}'] = macro_aligned[col]
    
    # Compute macro deltas (changes in rates, indicators)
    for col in macro_aligned.columns:
        features_df[f'macro_{col}_delta_20'] = features_df[f'macro_{col}'].diff(20)
    
    logger.info(f"✓ Macro features aligned: {len(macro_aligned.columns)} series")
    return features_df

def create_feature_matrix(
    ohlcv_df: pd.DataFrame,
    macro_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Create complete feature matrix with stable column order.
    
    Args:
        ohlcv_df: DataFrame with OHLCV data
        macro_df: Optional DataFrame with macro data
        
    Returns:
        DataFrame with all features, NaNs dropped after warmup period
    """
    logger.info("Creating feature matrix...")
    
    # Compute technical features
    features = compute_technical_features(ohlcv_df)
    
    # Add macro features if provided
    if macro_df is not None:
        features = align_macro_features(features, macro_df)
    
    # Drop warmup period (rows with NaN from rolling calculations)
    initial_rows = len(features)
    features = features.dropna()
    dropped_rows = initial_rows - len(features)
    
    logger.info(f"✓ Feature matrix created: {features.shape}")
    logger.info(f"  Dropped {dropped_rows} warmup rows with NaN")
    
    return features

if __name__ == "__main__":
    # Test feature engineering
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': 100 + np.random.randn(len(dates)).cumsum(),
        'high': 102 + np.random.randn(len(dates)).cumsum(),
        'low': 98 + np.random.randn(len(dates)).cumsum(),
        'close': 100 + np.random.randn(len(dates)).cumsum(),
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    print("Sample OHLCV data:")
    print(df.head())
    
    # Test feature creation
    features = create_feature_matrix(df)
    print(f"\nFeatures shape: {features.shape}")
    print(f"Feature columns: {list(features.columns[:10])}...")
    print("\nSample features:")
    print(features.head())
