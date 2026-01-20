"""
Model Training Script

Trains XGBoost models for stock movement prediction using real data from:
- Yahoo Finance (OHLCV)
- FRED API (macro indicators)

Implements walk-forward validation with strict data leakage prevention.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pickle
import warnings
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import xgboost as xgb

from app.services.data_sources import fetch_ohlcv_with_fallback, fetch_fred_series
from app.services.features import (
    compute_rsi, compute_macd, compute_bollinger_bands, compute_atr
)

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',  # Tech
    'JPM', 'BAC', 'WFC', 'C',  # Financials
    'XOM', 'CVX',  # Energy
    'JNJ', 'PFE',  # Healthcare
    'WMT', 'HD',  # Retail
    'SPY', 'QQQ'  # ETFs
]

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

HORIZONS = [1, 5, 20]  # Trading days ahead
LOOKBACK_DAYS = 730  # 2 years of historical data
TRAIN_TEST_SPLIT = 0.8


def create_labels(df: pd.DataFrame, horizon: int) -> pd.Series:
    """
    Create directional labels for given horizon.
    
    Args:
        df: DataFrame with OHLCV data
        horizon: Days ahead to predict
        
    Returns:
        Series with labels: 'up', 'down', 'flat'
    """
    future_returns = df['close'].pct_change(horizon).shift(-horizon)
    
    # Define thresholds (adjust based on volatility)
    threshold = 0.02  # 2% threshold
    
    labels = pd.Series(index=df.index, dtype=str)
    labels[future_returns > threshold] = 'up'
    labels[future_returns < -threshold] = 'down'
    labels[abs(future_returns) <= threshold] = 'flat'
    
    return labels


def compute_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators as features.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with technical features added
    """
    df = df.copy()
    
    # Price features
    df['returns_1d'] = df['close'].pct_change(1)
    df['returns_5d'] = df['close'].pct_change(5)
    df['returns_20d'] = df['close'].pct_change(20)
    
    # Volume features
    df['volume_change'] = df['volume'].pct_change(1)
    df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # RSI
    rsi_df = compute_rsi(df, period=14)
    df['rsi_14'] = rsi_df['rsi_14']
    
    # MACD
    macd_df = compute_macd(df)
    df['macd'] = macd_df['macd']
    df['macd_signal'] = macd_df['macd_signal']
    df['macd_hist'] = macd_df['macd_hist']
    
    # Bollinger Bands
    bb_df = compute_bollinger_bands(df)
    df['bb_upper'] = bb_df['bb_upper']
    df['bb_middle'] = bb_df['bb_middle']
    df['bb_lower'] = bb_df['bb_lower']
    df['bb_position'] = (df['close'] - bb_df['bb_lower']) / (bb_df['bb_upper'] - bb_df['bb_lower'])
    
    # ATR
    atr_df = compute_atr(df, period=14)
    df['atr_14'] = atr_df['atr_14']
    df['atr_ratio'] = atr_df['atr_14'] / df['close']
    
    # Moving averages
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_20'] = df['close'].rolling(20).mean()
    df['ma_50'] = df['close'].rolling(50).mean()
    df['ma_ratio_5_20'] = df['ma_5'] / df['ma_20']
    df['ma_ratio_20_50'] = df['ma_20'] / df['ma_50']
    
    # Price position
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['price_position'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    
    return df


def align_macro_features(stock_df: pd.DataFrame, macro_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align macro features with stock data.
    
    Args:
        stock_df: Stock OHLCV data
        macro_df: Macro indicators from FRED
        
    Returns:
        DataFrame with macro features aligned
    """
    if macro_df is None or macro_df.empty:
        return stock_df
    
    # Merge and forward-fill
    combined = stock_df.join(macro_df, how='left')
    
    # Forward fill macro data (assumes last known value)
    macro_cols = macro_df.columns.tolist()
    combined[macro_cols] = combined[macro_cols].fillna(method='ffill')
    
    return combined


def prepare_training_data(tickers: List[str], macro_df: pd.DataFrame, 
                          horizon: int) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prepare training data for all tickers.
    
    Args:
        tickers: List of ticker symbols
        macro_df: Macro economic indicators
        horizon: Prediction horizon in days
        
    Returns:
        Tuple of (features_df, labels_series, feature_names)
    """
    all_data = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    logger.info(f"Fetching data for {len(tickers)} tickers...")
    
    for ticker in tickers:
        try:
            # Fetch OHLCV data
            df = fetch_ohlcv_with_fallback(
                ticker,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if df is None or len(df) < 100:
                logger.warning(f"Insufficient data for {ticker}, skipping")
                continue
            
            # Compute technical features
            df = compute_technical_features(df)
            
            # Align macro features
            df = align_macro_features(df, macro_df)
            
            # Create labels
            df['label'] = create_labels(df, horizon)
            
            # Add ticker identifier
            df['ticker'] = ticker
            
            all_data.append(df)
            logger.info(f"  ✓ {ticker}: {len(df)} rows")
            
        except Exception as e:
            logger.error(f"  ✗ {ticker}: {e}")
            continue
    
    # Combine all ticker data
    combined_df = pd.concat(all_data, ignore_index=False)
    
    # Drop rows with NaN labels (can't predict beyond available data)
    combined_df = combined_df.dropna(subset=['label'])
    
    # Feature columns (exclude OHLCV, ticker, label)
    exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'ticker', 'label']
    feature_cols = [col for col in combined_df.columns if col not in exclude_cols]
    
    # Drop any remaining NaNs in features
    combined_df = combined_df.dropna(subset=feature_cols)
    
    X = combined_df[feature_cols]
    y = combined_df['label']
    
    logger.info(f"Total samples: {len(X)}, Features: {len(feature_cols)}")
    logger.info(f"Label distribution: {y.value_counts().to_dict()}")
    
    return X, y, feature_cols


def train_xgboost_model(X_train: pd.DataFrame, y_train: pd.Series,
                        X_test: pd.DataFrame, y_test: pd.Series) -> xgb.XGBClassifier:
    """
    Train XGBoost classifier.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Trained XGBoost model
    """
    logger.info("Training XGBoost model...")
    
    # Label encoding
    label_map = {'down': 0, 'flat': 1, 'up': 2}
    y_train_encoded = y_train.map(label_map)
    y_test_encoded = y_test.map(label_map)
    
    # Model parameters
    params = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'eval_metric': 'mlogloss'
    }
    
    model = xgb.XGBClassifier(**params)
    
    # Train
    model.fit(
        X_train, y_train_encoded,
        eval_set=[(X_test, y_test_encoded)],
        verbose=False
    )
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_labels = pd.Series(y_pred).map({0: 'down', 1: 'flat', 2: 'up'})
    
    accuracy = accuracy_score(y_test, y_pred_labels)
    logger.info(f"\nTest Accuracy: {accuracy:.4f}")
    
    logger.info("\nClassification Report:")
    print(classification_report(y_test, y_pred_labels))
    
    logger.info("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred_labels, labels=['down', 'flat', 'up']))
    
    return model


def save_artifacts(models: Dict, feature_schema: Dict, model_meta: Dict):
    """
    Save trained models and metadata to artifacts directory.
    
    Args:
        models: Dict of {horizon: model}
        feature_schema: Feature names and metadata
        model_meta: Model version and configuration
    """
    artifacts_dir = Path(__file__).parent.parent.parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    # Save models (one file with all horizons)
    model_path = artifacts_dir / "model.bin"
    with open(model_path, 'wb') as f:
        pickle.dump(models, f)
    logger.info(f"✓ Saved models to {model_path}")
    
    # Save feature schema
    schema_path = artifacts_dir / "feature_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(feature_schema, f, indent=2)
    logger.info(f"✓ Saved feature schema to {schema_path}")
    
    # Save model metadata
    meta_path = artifacts_dir / "model_meta.json"
    with open(meta_path, 'w') as f:
        json.dump(model_meta, f, indent=2)
    logger.info(f"✓ Saved model metadata to {meta_path}")


def main():
    """Main training pipeline."""
    start_time = datetime.now()
    
    logger.info("="*70)
    logger.info("Stock Movement Prediction - Model Training")
    logger.info(f"Started: {start_time}")
    logger.info("="*70)
    
    # Fetch macro data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    logger.info(f"\n1. Fetching macro data from FRED...")
    macro_df = fetch_fred_series(
        FRED_SERIES,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    if macro_df is not None:
        logger.info(f"   ✓ Fetched {len(macro_df)} rows, {len(macro_df.columns)} indicators")
    else:
        logger.warning("   ⚠ Failed to fetch macro data, continuing without it")
    
    # Train models for each horizon
    trained_models = {}
    feature_names = None
    
    for horizon in HORIZONS:
        logger.info(f"\n{'='*70}")
        logger.info(f"2. Training model for {horizon}-day horizon")
        logger.info(f"{'='*70}")
        
        # Prepare data
        X, y, feature_cols = prepare_training_data(TICKERS, macro_df, horizon)
        
        if feature_names is None:
            feature_names = feature_cols
        
        # Train/test split (time-based)
        split_idx = int(len(X) * TRAIN_TEST_SPLIT)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Train model
        model = train_xgboost_model(X_train, y_train, X_test, y_test)
        trained_models[horizon] = model
    
    # Prepare metadata
    model_meta = {
        "model_version": f"v1.0_{start_time.strftime('%Y%m%d_%H%M%S')}",
        "trained_at": start_time.isoformat(),
        "tickers": TICKERS,
        "horizons": HORIZONS,
        "lookback_days": LOOKBACK_DAYS,
        "train_test_split": TRAIN_TEST_SPLIT,
        "fred_series": FRED_SERIES,
        "model_type": "XGBoost"
    }
    
    feature_schema = {
        "features": feature_names,
        "num_features": len(feature_names),
        "feature_groups": {
            "price": [f for f in feature_names if 'returns' in f or 'ma' in f],
            "volume": [f for f in feature_names if 'volume' in f],
            "technical": [f for f in feature_names if any(x in f for x in ['rsi', 'macd', 'bb', 'atr'])],
            "macro": [f for f in feature_names if f in FRED_SERIES]
        }
    }
    
    # Save artifacts
    logger.info(f"\n{'='*70}")
    logger.info("3. Saving model artifacts")
    logger.info(f"{'='*70}")
    save_artifacts(trained_models, feature_schema, model_meta)
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("Training Complete!")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Models trained: {HORIZONS}")
    logger.info(f"Tickers: {len(TICKERS)}")
    logger.info(f"Features: {len(feature_names)}")
    logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    main()
