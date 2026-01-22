"""
Market data module for fetching all US stocks and IPO information.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import requests
from io import StringIO
import yfinance as yf

logger = logging.getLogger(__name__)

def get_all_us_stocks() -> List[str]:
    """
    Fetch list of all tradeable US stocks from multiple exchanges.
    
    Returns:
        List of ticker symbols
    """
    all_tickers = []
    
    try:
        # Method 1: Get NASDAQ stocks
        logger.info("Fetching NASDAQ listed stocks...")
        nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
        response = requests.get(nasdaq_url, timeout=10)
        
        if response.status_code == 200:
            # Parse pipe-delimited file
            df = pd.read_csv(StringIO(response.text), sep='|')
            # Filter for actual stocks (not test symbols)
            df = df[df['Test Issue'] == 'N']
            df = df[df['Financial Status'].notna()]
            # Extract symbols
            nasdaq_tickers = df['Symbol'].str.strip().tolist()
            all_tickers.extend(nasdaq_tickers)
            logger.info(f"✓ Found {len(nasdaq_tickers)} NASDAQ stocks")
    except Exception as e:
        logger.error(f"Failed to fetch NASDAQ stocks: {e}")
    
    try:
        # Method 2: Get NYSE stocks via FTP
        logger.info("Fetching NYSE listed stocks...")
        # Alternative: use yfinance screener or API
        # For now, use a curated list of major NYSE stocks
        nyse_majors = [
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'BLK',  # Financials
            'XOM', 'CVX', 'COP', 'SLB', 'PSX', 'VLO', 'MPC',  # Energy
            'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY',  # Healthcare
            'V', 'MA', 'PYPL', 'DIS', 'HD', 'MCD', 'NKE', 'SBUX',  # Consumer
            'BA', 'CAT', 'GE', 'HON', 'MMM', 'DE', 'UPS', 'LMT',  # Industrials
            'T', 'VZ', 'CMCSA',  # Telecom
        ]
        all_tickers.extend(nyse_majors)
        logger.info(f"✓ Added {len(nyse_majors)} major NYSE stocks")
    except Exception as e:
        logger.error(f"Failed to fetch NYSE stocks: {e}")
    
    # Remove duplicates and invalid symbols
    all_tickers = list(set(all_tickers))
    all_tickers = [t for t in all_tickers if t and len(t) <= 5 and not any(c in t for c in ['$', '^', '='])]
    
    # Sort alphabetically
    all_tickers.sort()
    
    logger.info(f"✓ Total unique US stocks: {len(all_tickers)}")
    return all_tickers


def get_sp500_stocks() -> List[str]:
    """
    Get S&P 500 stock list from Wikipedia.
    
    Returns:
        List of S&P 500 ticker symbols
    """
    try:
        logger.info("Fetching S&P 500 stocks...")
        
        # Add user agent to avoid 403 errors
        import urllib.request
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req) as response:
            tables = pd.read_html(response.read())
            df = tables[0]
            tickers = df['Symbol'].str.replace('.', '-').tolist()
            logger.info(f"✓ Found {len(tickers)} S&P 500 stocks")
            return tickers
    except Exception as e:
        logger.error(f"Failed to fetch S&P 500 stocks from Wikipedia: {e}")
        
        # Fallback: Use curated list of major S&P 500 stocks
        logger.info("Using fallback S&P 500 list...")
        fallback_sp500 = [
            # Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AVGO', 'ORCL', 'CRM',
            'ADBE', 'CSCO', 'ACN', 'TXN', 'QCOM', 'AMD', 'INTC', 'IBM', 'INTU', 'NOW',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'C', 'SCHW', 'AXP', 'USB',
            'PNC', 'TFC', 'COF', 'BK', 'STT', 'AIG', 'MET', 'PRU', 'AFL', 'ALL',
            # Healthcare
            'UNH', 'JNJ', 'LLY', 'PFE', 'ABBV', 'TMO', 'ABT', 'MRK', 'DHR', 'BMY',
            'AMGN', 'CVS', 'ELV', 'CI', 'HUM', 'GILD', 'VRTX', 'REGN', 'ZTS', 'ISRG',
            # Consumer
            'AMZN', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'TJX', 'DIS', 'BKNG',
            'CMG', 'ABNB', 'MAR', 'GM', 'F', 'TSLA', 'ORLY', 'AZO', 'YUM', 'DPZ',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
            # Industrials
            'BA', 'HON', 'UPS', 'RTX', 'LMT', 'CAT', 'GE', 'DE', 'MMM', 'FDX',
            # Materials
            'LIN', 'APD', 'SHW', 'ECL', 'DD', 'NEM', 'FCX', 'NUE', 'VMC', 'MLM',
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PEG', 'XEL', 'ED',
            # Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'WELL', 'DLR', 'SBAC', 'AVB',
            # Communication
            'GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS', 'CHTR', 'EA',
            # ETFs and popular
            'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI',
        ]
        
        # Remove duplicates
        fallback_sp500 = list(set(fallback_sp500))
        fallback_sp500.sort()
        
        logger.info(f"✓ Using {len(fallback_sp500)} curated S&P 500 stocks")
        return fallback_sp500


def get_nasdaq100_stocks() -> List[str]:
    """
    Get NASDAQ-100 stock list.
    
    Returns:
        List of NASDAQ-100 ticker symbols
    """
    try:
        logger.info("Fetching NASDAQ-100 stocks...")
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        tables = pd.read_html(url)
        df = tables[4]  # The component table
        tickers = df['Ticker'].tolist()
        logger.info(f"✓ Found {len(tickers)} NASDAQ-100 stocks")
        return tickers
    except Exception as e:
        logger.error(f"Failed to fetch NASDAQ-100 stocks: {e}")
        return []


def get_upcoming_ipos(days_ahead: int = 7) -> List[Dict]:
    """
    Fetch upcoming IPOs for the next N days.
    
    Args:
        days_ahead: Number of days to look ahead
        
    Returns:
        List of IPO dictionaries with details
    """
    ipos = []
    
    try:
        # Method 1: Use IPOScoop (scraped data)
        logger.info(f"Fetching upcoming IPOs for next {days_ahead} days...")
        
        # Alternative: Use NASDAQ IPO Calendar API
        # For demo purposes, create sample data structure
        # In production, integrate with:
        # - NASDAQ IPO Calendar API
        # - IEX Cloud IPO Calendar
        # - SEC EDGAR filings
        # - Financial data providers (Bloomberg, Refinitiv)
        
        # Sample IPO data structure (replace with actual API calls)
        today = datetime.now()
        sample_ipos = [
            {
                'symbol': 'NEWIPO1',
                'company_name': 'Sample Tech Inc.',
                'ipo_date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'price_range_low': 18.0,
                'price_range_high': 22.0,
                'expected_price': 20.0,
                'shares_offered': 10000000,
                'market_cap_estimate': 500000000,
                'sector': 'Technology',
                'exchange': 'NASDAQ',
                'underwriters': 'Goldman Sachs, Morgan Stanley',
            },
            {
                'symbol': 'NEWIPO2',
                'company_name': 'Healthcare Innovations LLC',
                'ipo_date': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
                'price_range_low': 12.0,
                'price_range_high': 15.0,
                'expected_price': 13.5,
                'shares_offered': 8000000,
                'market_cap_estimate': 300000000,
                'sector': 'Healthcare',
                'exchange': 'NYSE',
                'underwriters': 'JP Morgan, Citigroup',
            }
        ]
        
        # Try to fetch from yfinance IPO calendar (if available)
        try:
            # Note: yfinance doesn't have direct IPO calendar
            # Would need integration with proper IPO data provider
            pass
        except:
            pass
        
        ipos = sample_ipos
        logger.info(f"✓ Found {len(ipos)} upcoming IPOs")
        
    except Exception as e:
        logger.error(f"Failed to fetch IPOs: {e}")
    
    return ipos


def predict_ipo_profitability(ipo_data: Dict) -> Dict:
    """
    Predict whether an IPO will be profitable based on historical patterns.
    
    Args:
        ipo_data: IPO information dictionary
        
    Returns:
        Dictionary with profitability prediction and score
    """
    # Simple heuristic model (replace with actual ML model)
    score = 50.0  # Base score
    
    # Factor 1: Sector performance
    hot_sectors = ['Technology', 'Healthcare', 'CleanTech', 'FinTech']
    if ipo_data.get('sector') in hot_sectors:
        score += 15
    
    # Factor 2: Market cap size
    market_cap = ipo_data.get('market_cap_estimate', 0)
    if market_cap > 1_000_000_000:  # > $1B
        score += 10
    elif market_cap < 100_000_000:  # < $100M
        score -= 10
    
    # Factor 3: Price range spread (tight range = more confidence)
    price_low = ipo_data.get('price_range_low', 0)
    price_high = ipo_data.get('price_range_high', 1)
    if price_high > 0:
        spread_pct = ((price_high - price_low) / price_high) * 100
        if spread_pct < 15:  # Tight range
            score += 10
        elif spread_pct > 30:  # Wide range = uncertainty
            score -= 10
    
    # Factor 4: Underwriter quality
    premium_underwriters = ['Goldman Sachs', 'Morgan Stanley', 'JP Morgan', 'Citigroup']
    underwriters = ipo_data.get('underwriters', '')
    if any(uw in underwriters for uw in premium_underwriters):
        score += 10
    
    # Clamp score between 0 and 100
    score = max(0, min(100, score))
    
    # Determine profitability prediction
    if score >= 70:
        prediction = 'Highly Profitable'
        confidence = 'High'
    elif score >= 55:
        prediction = 'Likely Profitable'
        confidence = 'Medium'
    elif score >= 40:
        prediction = 'Neutral'
        confidence = 'Low'
    else:
        prediction = 'Risky'
        confidence = 'Low'
    
    return {
        'prediction': prediction,
        'confidence': confidence,
        'score': round(score, 1),
        'factors': {
            'sector_strength': ipo_data.get('sector') in hot_sectors,
            'market_cap_adequate': market_cap > 100_000_000,
            'price_range_tight': spread_pct < 15 if price_high > 0 else False,
            'premium_underwriters': any(uw in underwriters for uw in premium_underwriters)
        }
    }


def get_market_universe(universe_type: str = "sp500") -> List[str]:
    """
    Get stock universe based on type.
    
    Args:
        universe_type: 'all', 'sp500', 'nasdaq100', 'russell3000'
        
    Returns:
        List of ticker symbols
    """
    if universe_type == "sp500":
        return get_sp500_stocks()
    elif universe_type == "nasdaq100":
        return get_nasdaq100_stocks()
    elif universe_type == "all":
        return get_all_us_stocks()
    else:
        # Default to S&P 500
        return get_sp500_stocks()


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== Testing Market Data Module ===\n")
    
    # Test S&P 500
    sp500 = get_sp500_stocks()
    print(f"S&P 500 stocks: {len(sp500)}")
    print(f"Sample: {sp500[:10]}")
    
    # Test NASDAQ-100
    nasdaq100 = get_nasdaq100_stocks()
    print(f"\nNASDAQ-100 stocks: {len(nasdaq100)}")
    print(f"Sample: {nasdaq100[:10]}")
    
    # Test All US Stocks
    all_stocks = get_all_us_stocks()
    print(f"\nAll US stocks: {len(all_stocks)}")
    print(f"Sample: {all_stocks[:10]}")
    
    # Test IPOs
    ipos = get_upcoming_ipos(days_ahead=7)
    print(f"\nUpcoming IPOs: {len(ipos)}")
    for ipo in ipos:
        print(f"\n{ipo['company_name']} ({ipo['symbol']})")
        print(f"  Date: {ipo['ipo_date']}")
        print(f"  Price Range: ${ipo['price_range_low']}-${ipo['price_range_high']}")
        
        # Test profitability prediction
        prediction = predict_ipo_profitability(ipo)
        print(f"  Profitability: {prediction['prediction']} (Score: {prediction['score']})")
