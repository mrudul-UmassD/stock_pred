# Stock Predictor - Market-Wide Predictions & IPO Analysis

## New Features

### 1. All US Stocks Predictions
Predict all stocks in the US market:
- **S&P 500**: 500+ large-cap stocks
- **NASDAQ-100**: 100 tech-heavy stocks
- **All US Stocks**: 6000+ tradeable stocks

### 2. IPO Tracker & Profitability Analysis
Track upcoming IPOs with ML-based profitability predictions:
- Upcoming IPOs (7/14/30 days ahead)
- Price range analysis
- Market cap estimates
- Sector strength evaluation
- Underwriter quality assessment
- Sortable profitability scores

## Running Batch Predictions

### Quick Start - S&P 500 (Recommended)
```bash
cd backend
python scripts/predict_batch.py --universe sp500
```

### All Options

#### Predict S&P 500 Stocks
```bash
python scripts/predict_batch.py --universe sp500
```
- Processes: ~500 stocks
- Duration: ~20-30 minutes
- Best for: Production use

#### Predict NASDAQ-100
```bash
python scripts/predict_batch.py --universe nasdaq100
```
- Processes: ~100 stocks
- Duration: ~5-10 minutes
- Best for: Tech-focused analysis

#### Predict ALL US Stocks
```bash
python scripts/predict_batch.py --universe all
```
- Processes: 6000+ stocks
- Duration: 3-4 hours
- Best for: Comprehensive market analysis

#### Test Mode (Limited Stocks)
```bash
python scripts/predict_batch.py --universe sp500 --limit 10
```
- Processes: First 10 stocks only
- Duration: ~1 minute
- Best for: Testing

#### Custom Horizons
```bash
python scripts/predict_batch.py --universe sp500 --horizons 1 5 20
```

### Performance Settings

Edit `predict_batch.py` to adjust:
- **BATCH_SIZE**: Number of stocks per batch (default: 50)
- **MAX_WORKERS**: Parallel threads (default: 5)

```python
BATCH_SIZE = 100  # Process 100 stocks at a time
MAX_WORKERS = 10  # Use 10 parallel threads
```

## API Endpoints

### Get All Predictions with Sorting
```
GET /api/predictions/all
```

Query Parameters:
- `horizon`: 1, 5, or 20 (default: 5)
- `sort_by`: prob_up, prob_down, expected_return, ticker (default: prob_up)
- `order`: asc or desc (default: desc)
- `limit`: Max results (default: 500, max: 5000)

Example:
```bash
curl "http://localhost:8000/api/predictions/all?horizon=5&sort_by=prob_up&order=desc&limit=100"
```

### Get Ticker Universe
```
GET /api/universe/tickers
```

Query Parameters:
- `universe`: sp500, nasdaq100, all (default: sp500)

Example:
```bash
curl "http://localhost:8000/api/universe/tickers?universe=sp500"
```

### Get Upcoming IPOs
```
GET /api/ipos/upcoming
```

Query Parameters:
- `days_ahead`: Days to look ahead (default: 7, max: 30)

Example:
```bash
curl "http://localhost:8000/api/ipos/upcoming?days_ahead=14"
```

## Frontend Pages

### All Stocks Page
**URL**: http://localhost:3000/stocks

Features:
- Search by ticker
- Filter by direction (up/down/flat)
- Sort by probability or expected return
- Real-time updates
- Pagination for 1000+ stocks

### IPO Tracker Page
**URL**: http://localhost:3000/ipos

Features:
- Upcoming IPOs with dates
- Profitability predictions
- Factor analysis (sector, size, pricing, underwriters)
- Sortable by score, date, or market cap
- Detailed IPO information cards

### Individual Stock Page
**URL**: http://localhost:3000/ticker/[SYMBOL]

Example: http://localhost:3000/ticker/AAPL

## Automated Prediction Updates

### Cron Job Setup (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add daily prediction run at 6 PM
0 18 * * * cd /path/to/backend && python scripts/predict_batch.py --universe sp500
```

### Windows Task Scheduler
```powershell
# Create scheduled task for daily run
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts/predict_batch.py --universe sp500" -WorkingDirectory "E:\ML Projects\Stock predictor\backend"
$trigger = New-ScheduledTaskTrigger -Daily -At 6pm
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "StockPredictions" -Description "Daily stock prediction run"
```

## IPO Data Sources

The IPO module currently uses sample data. To integrate real IPO data:

### Option 1: IEX Cloud (Recommended)
```python
# In market_data.py
import os
IEX_TOKEN = os.getenv('IEX_CLOUD_TOKEN')
url = f"https://cloud.iexapis.com/stable/stock/market/upcoming-ipos?token={IEX_TOKEN}"
```

### Option 2: NASDAQ IPO Calendar
```python
url = "https://www.nasdaq.com/api/v1/calendar/ipos"
```

### Option 3: SEC EDGAR Filings
Parse S-1 registration statements from SEC EDGAR.

## Database Schema

### Predictions Table
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    ticker TEXT NOT NULL,
    horizon INTEGER NOT NULL,
    direction TEXT NOT NULL,
    prob_up REAL NOT NULL,
    prob_down REAL NOT NULL,
    prob_flat REAL NOT NULL,
    expected_return REAL,
    model_version TEXT
);

CREATE INDEX idx_ticker_horizon_ts ON predictions(ticker, horizon, ts DESC);
CREATE INDEX idx_horizon_prob_up ON predictions(horizon, prob_up DESC);
```

## Performance Optimization Tips

### 1. Use Batch Processing
Process stocks in batches to manage memory:
```python
BATCH_SIZE = 50  # Adjust based on available RAM
```

### 2. Parallel Processing
Increase workers for faster processing:
```python
MAX_WORKERS = 10  # Adjust based on CPU cores
```

### 3. Database Indexing
Add indexes for common queries:
```sql
CREATE INDEX idx_horizon_direction ON predictions(horizon, direction);
CREATE INDEX idx_ticker_ts ON predictions(ticker, ts DESC);
```

### 4. Caching
Cache model artifacts to avoid repeated loading:
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_artifacts_cached():
    return load_artifacts()
```

## Monitoring

### Check Prediction Coverage
```sql
-- Count predictions per horizon
SELECT horizon, COUNT(DISTINCT ticker) as stock_count
FROM predictions
WHERE ts > datetime('now', '-1 day')
GROUP BY horizon;
```

### View Latest Predictions
```sql
-- Top 10 highest probability UP predictions
SELECT ticker, prob_up, prob_down, prob_flat, expected_return
FROM predictions
WHERE horizon = 5
ORDER BY prob_up DESC
LIMIT 10;
```

### Monitor Batch Progress
Check logs during batch run:
```bash
tail -f backend/logs/predictions.log
```

## Troubleshooting

### Issue: Slow Predictions
**Solution**: Reduce batch size or increase workers
```bash
# Edit predict_batch.py
BATCH_SIZE = 25  # Smaller batches
MAX_WORKERS = 3  # Fewer workers
```

### Issue: Memory Errors
**Solution**: Process in smaller universes
```bash
# Instead of 'all', use sp500
python scripts/predict_batch.py --universe sp500 --limit 100
```

### Issue: API Rate Limits
**Solution**: Add delays between requests
```python
import time
time.sleep(0.5)  # 500ms delay between API calls
```

## Future Enhancements

1. **Real-time IPO Data**: Integrate with IPO data providers
2. **Portfolio Tracking**: Track selected stocks
3. **Alerts**: Email/SMS notifications for high-probability predictions
4. **Backtesting**: Historical accuracy tracking
5. **Sector Analysis**: Industry-level predictions
6. **Options Predictions**: Volatility and options strategies

## Support

For issues or questions:
1. Check logs: `backend/logs/`
2. Review API errors: `/api/health`
3. Test single ticker: `python scripts/predict.py`
4. Report issues: GitHub Issues

---

**Last Updated**: January 22, 2026
**Version**: 2.0.0 - Market-Wide Edition
