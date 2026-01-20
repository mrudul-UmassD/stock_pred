"""
Inference module for loading model artifacts and making predictions.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Global cache for loaded artifacts
_artifacts_cache = {
    "model": None,
    "schema": None,
    "meta": None,
    "loaded": False
}

def load_artifacts(force_reload: bool = False) -> Tuple[Optional[object], Optional[Dict], Optional[Dict]]:
    """
    Load model artifacts from disk.
    
    Args:
        force_reload: Force reload even if already cached
        
    Returns:
        Tuple of (model, feature_schema, model_meta) or (None, None, None) if not found
    """
    global _artifacts_cache
    
    # Return cached if available and not forcing reload
    if _artifacts_cache["loaded"] and not force_reload:
        return (
            _artifacts_cache["model"],
            _artifacts_cache["schema"],
            _artifacts_cache["meta"]
        )
    
    try:
        model_path = ARTIFACTS_DIR / "model.bin"
        schema_path = ARTIFACTS_DIR / "feature_schema.json"
        meta_path = ARTIFACTS_DIR / "model_meta.json"
        
        # Check if files exist
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None, None, None
        
        # Load model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"✓ Loaded model from {model_path}")
        
        # Load feature schema
        feature_schema = None
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                feature_schema = json.load(f)
            logger.info(f"✓ Loaded feature schema: {len(feature_schema.get('features', []))} features")
        
        # Load model metadata
        model_meta = None
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                model_meta = json.load(f)
            logger.info(f"✓ Loaded model meta: version {model_meta.get('model_version')}")
        
        # Cache artifacts
        _artifacts_cache["model"] = model
        _artifacts_cache["schema"] = feature_schema
        _artifacts_cache["meta"] = model_meta
        _artifacts_cache["loaded"] = True
        
        return model, feature_schema, model_meta
        
    except Exception as e:
        logger.error(f"Error loading artifacts: {e}")
        return None, None, None

def get_dummy_prediction() -> Dict:
    """
    Return dummy prediction when model is not available (dev mode).
    
    Returns:
        Dict with neutral prediction
    """
    return {
        "direction": "flat",
        "prob_up": 0.33,
        "prob_down": 0.33,
        "prob_flat": 0.34,
        "expected_return": 0.0,
        "is_dummy": True
    }

def predict_for_ticker(
    ticker: str,
    horizon: int,
    features_df: pd.DataFrame,
    use_dummy_if_missing: bool = False
) -> Optional[Dict]:
    """
    Generate prediction for a ticker at a specific horizon.
    
    Args:
        ticker: Stock symbol
        horizon: Prediction horizon in days (1, 5, or 20)
        features_df: DataFrame with computed features (single row or last row will be used)
        use_dummy_if_missing: Return dummy prediction if model not found (dev mode)
        
    Returns:
        Dict with prediction:
            - direction: 'up', 'down', or 'flat'
            - prob_up: Probability of up movement
            - prob_down: Probability of down movement
            - prob_flat: Probability of flat movement
            - expected_return: Expected return estimate
        Returns None if prediction fails
    """
    try:
        # Load artifacts
        model, feature_schema, model_meta = load_artifacts()
        
        # Check if model loaded
        if model is None:
            if use_dummy_if_missing:
                logger.warning(f"Model not loaded, returning dummy prediction for {ticker}")
                return get_dummy_prediction()
            else:
                logger.error(f"Model not loaded, cannot predict for {ticker}")
                return None
        
        # Get model for specific horizon (models are stored as dict per horizon)
        if isinstance(model, dict):
            horizon_model = model.get(horizon)
            if horizon_model is None:
                logger.error(f"No model found for horizon {horizon}")
                if use_dummy_if_missing:
                    return get_dummy_prediction()
                return None
        else:
            # Single model for all horizons (legacy)
            horizon_model = model
        
        # Validate horizon
        if model_meta and 'horizons' in model_meta:
            if horizon not in model_meta['horizons']:
                logger.error(f"Invalid horizon {horizon}, model supports {model_meta['horizons']}")
                return None
        
        # Get latest features (last row)
        if features_df.empty:
            logger.error(f"Empty features dataframe for {ticker}")
            return None
        
        latest_features = features_df.iloc[-1:]
        
        # Align features with schema
        if feature_schema and 'features' in feature_schema:
            required_features = feature_schema['features']
            
            # Check if all required features are present
            missing_features = set(required_features) - set(latest_features.columns)
            if missing_features:
                logger.warning(f"Missing features for {ticker}: {missing_features}")
                # Fill missing features with 0 (not ideal, but handles schema changes)
                for feat in missing_features:
                    latest_features[feat] = 0
            
            # Select and order features according to schema
            X = latest_features[required_features].values
        else:
            # Use all numeric features
            X = latest_features.select_dtypes(include=[np.number]).values
        
        # Make prediction
        proba = horizon_model.predict_proba(X)[0]
        pred_class = horizon_model.predict(X)[0]
        
        # Map class to direction (assumes classes are 0=down, 1=flat, 2=up)
        class_to_direction = {0: 'down', 1: 'flat', 2: 'up'}
        direction = class_to_direction.get(pred_class, 'flat')
        
        # Expected return (simplified)
        # up: +threshold, flat: 0, down: -threshold
        thresholds = model_meta.get('thresholds', {'up': 0.02, 'down': -0.02}) if model_meta else {'up': 0.02, 'down': -0.02}
        expected_returns = {
            'up': thresholds.get('up', 0.02),
            'flat': 0.0,
            'down': thresholds.get('down', -0.02)
        }
        expected_return = sum(proba[i] * list(expected_returns.values())[i] for i in range(len(proba)))
        
        result = {
            "direction": direction,
            "prob_up": float(proba[2]) if len(proba) > 2 else 0.33,  # Assumes up is class 2
            "prob_down": float(proba[0]) if len(proba) > 0 else 0.33,  # Assumes down is class 0
            "prob_flat": float(proba[1]) if len(proba) > 1 else 0.34,  # Assumes flat is class 1
            "expected_return": float(expected_return),
            "is_dummy": False
        }
        
        logger.info(f"✓ Prediction for {ticker} (horizon={horizon}): {direction} (prob={max(proba):.2f})")
        return result
        
    except Exception as e:
        logger.error(f"Error predicting for {ticker}: {e}")
        if use_dummy_if_missing:
            return get_dummy_prediction()
        return None

def get_model_info() -> Optional[Dict]:
    """
    Get information about the loaded model.
    
    Returns:
        Dict with model information or None if not loaded
    """
    try:
        model, feature_schema, model_meta = load_artifacts()
        
        if model is None:
            return None
        
        info = {
            "model_loaded": True,
            "model_type": type(model).__name__,
            "num_features": len(feature_schema.get('features', [])) if feature_schema else 0,
            "model_version": model_meta.get('model_version') if model_meta else "unknown",
            "horizons": model_meta.get('horizons', []) if model_meta else [],
            "tickers": model_meta.get('tickers', []) if model_meta else [],
            "created_at": model_meta.get('created_at') if model_meta else None
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return None

if __name__ == "__main__":
    # Test inference module
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Testing inference module...")
    print("="*60)
    
    # Try to load artifacts
    model, schema, meta = load_artifacts()
    
    if model is None:
        print("\n⚠ No model found - testing dummy mode")
        
        # Create dummy features
        import pandas as pd
        import numpy as np
        
        dummy_features = pd.DataFrame({
            'return_1d': [0.01],
            'sma_5': [100.0],
            'sma_20': [98.0],
            'rsi_14': [55.0],
            'macd': [0.5],
            'bb_width': [0.1]
        })
        
        # Test prediction with dummy
        result = predict_for_ticker(
            "TEST",
            horizon=5,
            features_df=dummy_features,
            use_dummy_if_missing=True
        )
        
        print(f"\nDummy prediction result:")
        print(json.dumps(result, indent=2))
    else:
        print("\n✓ Model loaded successfully")
        info = get_model_info()
        print(f"\nModel info:")
        print(json.dumps(info, indent=2))
