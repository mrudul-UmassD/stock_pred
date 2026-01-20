"""
Quick model training script - trains on a small set of tickers for rapid deployment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pickle
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report
import xgboost as xgb

from app.services.data_sources import fetch_ohlcv_with_fallback
from app.services.features import compute_rsi, compute_macd, compute_bollinger_bands, compute_atr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Quick training config
TICKERS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL']
HORIZONS = [1, 5, 20]
LOOKBACK_DAYS = 500

def create_labels(df, horizon):
    future_returns = df['close'].pct_change(horizon).shift(-horizon)
    threshold = 0.02
    labels = pd.Series(index=df.index, dtype=str)
    labels[future_returns > threshold] = 'up'
    labels[future_returns < -threshold] = 'down'
    labels[abs(future_returns) <= threshold] = 'flat'
    return labels

def compute_features(df):
    df = df.copy()
    
    # Price features
    df['returns_1d'] = df['close'].pct_change(1)
    df['returns_5d'] = df['close'].pct_change(5)
    df['returns_20d'] = df['close'].pct_change(20)
    
    # Volume
    df['volume_change'] = df['volume'].pct_change(1)
    df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # Technical indicators
    rsi_df = compute_rsi(df)
    df['rsi_14'] = rsi_df['rsi_14']
    
    macd_df = compute_macd(df)
    df['macd'] = macd_df['macd']
    df['macd_signal'] = macd_df['macd_signal']
    
    bb_df = compute_bollinger_bands(df)
    df['bb_position'] = (df['close'] - bb_df['bb_lower']) / (bb_df['bb_upper'] - bb_df['bb_lower'])
    
    atr_df = compute_atr(df)
    df['atr_ratio'] = atr_df['atr_14'] / df['close']
    
    # Moving averages
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_20'] = df['close'].rolling(20).mean()
    df['ma_ratio'] = df['ma_5'] / df['ma_20']
    
    return df

def prepare_data(tickers, horizon):
    all_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    for ticker in tickers:
        try:
            df = fetch_ohlcv_with_fallback(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            if df is None or len(df) < 100:
                continue
            
            df = compute_features(df)
            df['label'] = create_labels(df, horizon)
            df['ticker'] = ticker
            all_data.append(df)
            logger.info(f"  ✓ {ticker}: {len(df)} rows")
        except Exception as e:
            logger.error(f"  ✗ {ticker}: {e}")
            continue
    
    combined = pd.concat(all_data, ignore_index=False)
    combined = combined.dropna(subset=['label'])
    
    exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'ticker', 'label']
    feature_cols = [col for col in combined.columns if col not in exclude_cols]
    
    combined = combined.dropna(subset=feature_cols)
    X = combined[feature_cols]
    y = combined['label']
    
    logger.info(f"Total samples: {len(X)}, Features: {len(feature_cols)}")
    return X, y, feature_cols

def train_model(X_train, y_train, X_test, y_test):
    label_map = {'down': 0, 'flat': 1, 'up': 2}
    y_train_enc = y_train.map(label_map)
    y_test_enc = y_test.map(label_map)
    
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        max_depth=4,
        learning_rate=0.1,
        n_estimators=100,
        random_state=42
    )
    
    model.fit(X_train, y_train_enc, eval_set=[(X_test, y_test_enc)], verbose=False)
    
    y_pred = model.predict(X_test)
    y_pred_labels = pd.Series(y_pred).map({0: 'down', 1: 'flat', 2: 'up'})
    print(classification_report(y_test, y_pred_labels))
    
    return model

def main():
    logger.info("="*70)
    logger.info("Quick Model Training")
    logger.info("="*70)
    
    models = {}
    feature_names = None
    
    for horizon in HORIZONS:
        logger.info(f"\nTraining {horizon}-day model...")
        X, y, features = prepare_data(TICKERS, horizon)
        
        if feature_names is None:
            feature_names = features
        
        split = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]
        
        model = train_model(X_train, y_train, X_test, y_test)
        models[horizon] = model
    
    # Save artifacts
    artifacts_dir = Path(__file__).parent.parent.parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    with open(artifacts_dir / "model.bin", 'wb') as f:
        pickle.dump(models, f)
    
    with open(artifacts_dir / "feature_schema.json", 'w') as f:
        json.dump({"features": feature_names}, f, indent=2)
    
    with open(artifacts_dir / "model_meta.json", 'w') as f:
        json.dump({
            "model_version": f"v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "trained_at": datetime.now().isoformat(),
            "tickers": TICKERS,
            "horizons": HORIZONS,
            "model_type": "XGBoost"
        }, f, indent=2)
    
    logger.info(f"\n✓ Models saved to {artifacts_dir}")
    logger.info("Training complete!\n")

if __name__ == "__main__":
    main()
