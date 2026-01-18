# stock-predict-live

Real-time US stock movement prediction dashboard using multi-source time-series data.

## Overview

This project predicts future direction (up/down/flat) for US stocks over horizons {1, 5, 20} trading days using:
- **Training Pipeline**: Jupyter Notebook for model development and artifact export
- **Backend API**: FastAPI serving predictions with real-time SSE streaming
- **Frontend Dashboard**: Next.js real-time UI with live updates
- **Storage**: SQLite database for predictions

## Architecture

```
notebooks/train.ipynb → artifacts/ → backend (FastAPI + SSE) → frontend (Next.js)
                                    ↓
                                db/predictions.db
```

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- FRED API Key (get free at https://fred.stlouisfed.org/docs/api/api_key.html)

### Environment Variables
```bash
# Required for training and backend
export FRED_API_KEY=your_fred_api_key_here
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Data Sources

### Primary Data
1. **Yahoo Finance (yfinance)**: OHLCV + Adj Close for stock tickers (10+ years history)
2. **Stooq CSV**: Fallback data source when yfinance fails or has missing data
3. **FRED API (fredapi)**: Macro indicators
   - FEDFUNDS (Federal Funds Rate)
   - CPIAUCSL (CPI)
   - UNRATE (Unemployment Rate)
   - DGS10, DGS2 (Treasury Yields)
   - T10Y2Y (Yield Curve)
   - VIXCLS (VIX)
   - USREC (Recession Indicator)

### Universe
- S&P 500 tickers from Wikipedia OR manual list
- Code supports both approaches

## Training

### Run Training Notebook
```bash
cd notebooks
jupyter notebook train.ipynb
```

The notebook performs:
1. Data ingestion from all sources
2. Feature engineering (technical + macro indicators)
3. Label generation (direction classification)
4. Walk-forward validation (no data leakage)
5. XGBoost model training
6. Artifact export

### Artifacts Generated
- `artifacts/model.bin`: Trained XGBoost model
- `artifacts/feature_schema.json`: Feature names and order
- `artifacts/model_meta.json`: Model version, tickers, horizons, thresholds

## Serving

### Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API Endpoints:
- `GET /health`: Server health check
- `GET /api/tickers`: List of available tickers
- `GET /api/predictions/overview?horizon=5&limit=200`: Overview of predictions
- `GET /api/predictions/latest?ticker=SPY&horizon=5`: Latest prediction for ticker
- `GET /api/predictions/history?ticker=SPY&horizon=5&limit=500`: Historical predictions
- `GET /api/stream?horizon=5`: SSE stream for real-time updates

### Generate Predictions
```bash
python backend/scripts/predict.py
```

This script:
1. Loads model artifacts
2. Fetches latest market and macro data
3. Generates predictions for all tickers and horizons
4. Stores predictions in SQLite database

Set up periodic execution (cron/scheduler) for automatic updates.

## Frontend

### Start Development Server
```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

### Pages
- `/`: Overview dashboard with live predictions table
- `/ticker/[symbol]`: Detailed view for specific ticker with charts
- `/health`: System health and status

### Features
- Real-time updates via SSE
- Filter by horizon (1/5/20 days)
- Search tickers
- Probability threshold filtering
- Historical prediction charts

## Streaming

The backend uses Server-Sent Events (SSE) for real-time updates:
- Client connects via EventSource
- Server pushes new predictions every 2 seconds
- Automatic reconnection on disconnect
- Frontend updates UI without page refresh

## Data Leakage Prevention

The project strictly prevents data leakage:
1. **Walk-forward validation**: Expanding window, no random splits
2. **Feature engineering**: Only uses past data (forward-fill macro without peeking)
3. **Label generation**: Forward returns computed after feature cutoff
4. **No future information**: All indicators use strictly historical windows

## Troubleshooting

### FRED API Key Missing
```
Error: FRED_API_KEY not found in environment
Solution: Export FRED_API_KEY before running notebook or backend
```

### yfinance Data Fetch Failed
```
Solution: Automatically falls back to Stooq CSV downloader
Check network connectivity and ticker symbol validity
```

### Model Artifacts Not Found
```
Solution: Run notebooks/train.ipynb to generate artifacts
Ensure artifacts/ directory contains model.bin, feature_schema.json, model_meta.json
```

### Frontend Cannot Connect to Backend
```
Solution: Ensure backend is running on port 8000
Check CORS configuration in backend/app/main.py
```

### SSE Connection Issues
```
Solution: Check browser console for EventSource errors
Verify /api/stream endpoint is accessible
Ensure no firewall blocking SSE connections
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT
