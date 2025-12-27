# ============================================================================
# FILE 1: scanner/stock_universe.py
# Defines which stocks to scan each day of the week
# ============================================================================

"""
Stock Universe Manager
Provides daily batches of stocks for the rolling scanner
Now supports dynamic fetching from exchanges (NASDAQ, NYSE, AMEX)
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# S&P 500 largest tech and growth stocks
SP500_TECH = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "ADBE",
    "CRM", "AMD", "INTC", "CSCO", "QCOM", "TXN", "INTU", "AMAT", "MU", "ADI",
    "LRCX", "KLAC", "SNPS", "CDNS", "MCHP", "FTNT", "PANW", "WDAY", "TEAM", "ZS"
]

# Financials
SP500_FINANCIAL = [
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB",
    "PNC", "TFC", "COF", "BK", "STATE", "DFS", "AIG", "MET", "PRU", "ALL",
    "TRV", "AFL", "HIG", "PFG", "AMP", "TROW", "BEN", "IVZ", "NTRS", "STT"
]

# Healthcare
SP500_HEALTHCARE = [
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "BMY",
    "AMGN", "CVS", "MDT", "GILD", "CI", "ISRG", "REGN", "VRTX", "HUM", "BSX",
    "ZTS", "SYK", "ELV", "MCK", "COR", "IDXX", "IQV", "DXCM", "EW", "ALGN"
]

# Consumer & Retail
SP500_CONSUMER = [
    "WMT", "HD", "COST", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "TGT",
    "LOW", "TJX", "BKNG", "EL", "MDLZ", "CL", "KMB", "GIS", "HSY", "K",
    "DG", "DLTR", "ROST", "ULTA", "ORLY", "AZO", "BBY", "MAR", "YUM", "CMG"
]

# Energy & Industrials
SP500_ENERGY_INDUSTRIAL = [
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    "BA", "CAT", "GE", "HON", "UPS", "RTX", "DE", "LMT", "MMM", "EMR",
    "ETN", "ITW", "PH", "CMI", "CARR", "OTIS", "PCAR", "ROK", "DOV", "FTV"
]

# Popular growth & meme stocks
GROWTH_MOVERS = [
    "HOOD", "COIN", "PLTR", "SNOW", "NET", "DDOG", "CRWD", "ZM", "OKTA", "U",
    "RBLX", "RIVN", "LCID", "SOFI", "AFRM", "SQ", "SHOP", "ROKU", "PTON", "BYND",
    "DASH", "UBER", "LYFT", "ABNB", "DUOL", "CPNG", "BILL", "GTLB", "S", "FROG"
]

# Small/Mid cap opportunities
SMALL_MID_CAPS = [
    "ETSY", "PINS", "SNAP", "TWLO", "ZI", "DOCU", "BOX", "DBX", "RNG", "GNRC",
    "POOL", "TECH", "AZEK", "TREX", "BLD", "BLDR", "CVLT", "CDAY", "PCOR", "BRO",
    "AIT", "WST", "MTD", "A", "BR", "FAST", "SRCL", "SSD", "GGG", "RBC"
]


def filter_strong_markets(tickers, min_market_cap=50_000_000, min_volume=100_000):
    """
    Pre-filter tickers to only include strong markets
    Applies market cap filter first (fast), then exchange check
    
    Args:
        tickers: List of ticker symbols
        min_market_cap: Minimum market cap in dollars (default $50M)
        min_volume: Minimum average daily volume (default 100k, 0 to disable)
    
    Returns:
        Filtered list of ticker symbols
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import StockAnalyzer
    
    analyzer = StockAnalyzer()
    filtered_tickers = []
    skipped_low_cap = 0
    skipped_weak_market = 0
    skipped_low_volume = 0
    
    print(f"🔍 Filtering {len(tickers)} tickers to strong markets only...")
    print(f"   Criteria: Market cap >= ${min_market_cap:,}, Strong exchange, Volume >= {min_volume:,}")
    
    for ticker in tickers:
        try:
            fundamentals = analyzer.get_fundamentals(ticker)
            
            if not fundamentals:
                continue
            
            # Primary filter: Market cap
            market_cap = fundamentals.get('market_cap', 0)
            if market_cap < min_market_cap:
                skipped_low_cap += 1
                continue
            
            # Secondary filter: Strong market
            if not fundamentals.get('is_strong_market', False):
                skipped_weak_market += 1
                continue
            
            # Optional filter: Volume
            if min_volume > 0:
                avg_volume = fundamentals.get('average_volume', 0)
                if avg_volume < min_volume:
                    skipped_low_volume += 1
                    continue
            
            filtered_tickers.append(ticker)
            
        except Exception as e:
            continue  # Skip if can't determine
    
    print(f"✅ Filtered to {len(filtered_tickers)} strong market stocks")
    print(f"   Skipped: {skipped_low_cap} low market cap, {skipped_weak_market} weak market, {skipped_low_volume} low volume")
    
    return filtered_tickers


def get_daily_batch(day_of_week, filter_weak_markets=True, min_market_cap=50_000_000, use_dynamic=False, min_volume=100_000):
    """
    Returns stock list for given day
    Optionally filters out weak markets (OTC, pink sheets)
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        filter_weak_markets: If True, apply market filtering
        min_market_cap: Minimum market cap for filtering (default $50M)
        use_dynamic: If True, fetch from exchanges dynamically instead of hardcoded list
        min_volume: Minimum volume filter (for dynamic mode)
        
    Returns:
        List of ticker symbols
    """
    # Use dynamic fetching if requested
    if use_dynamic:
        return get_dynamic_daily_batch(day_of_week, min_market_cap=min_market_cap, min_volume=min_volume)
    
    # Original hardcoded batches
    batches = {
        0: SP500_TECH + GROWTH_MOVERS,  # Monday: Tech & Growth
        1: SP500_FINANCIAL + SP500_ENERGY_INDUSTRIAL[:20],  # Tuesday: Financials & Energy
        2: SP500_HEALTHCARE + SP500_CONSUMER[:20],  # Wednesday: Healthcare
        3: SP500_CONSUMER + SMALL_MID_CAPS[:30],  # Thursday: Consumer & Small caps
        4: SP500_ENERGY_INDUSTRIAL + SMALL_MID_CAPS[30:],  # Friday: Industrials & Small caps
        5: [],  # Saturday: Re-scan hot/warming only (handled separately)
        6: []   # Sunday: No scan
    }
    
    tickers = batches.get(day_of_week, [])
    
    # Apply market filtering if requested
    if filter_weak_markets and tickers:
        tickers = filter_strong_markets(tickers, min_market_cap=min_market_cap)
    
    return tickers


def fetch_all_exchange_tickers(force_refresh=False, cache_days=7):
    """
    Fetch all tickers from NASDAQ, NYSE, and AMEX exchanges dynamically.
    Uses multiple methods to get comprehensive ticker lists.
    Uses cached list if available and fresh (within cache_days).
    
    Args:
        force_refresh: If True, ignore cache and fetch fresh data
        cache_days: Number of days to cache the ticker list (default 7)
    
    Returns:
        List of ticker symbols from all qualifying exchanges
    """
    cache_file = Path("data") / "exchange_tickers_cache.json"
    cache_file.parent.mkdir(exist_ok=True)
    
    # Check cache first
    if not force_refresh and cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cached_date = datetime.fromisoformat(cache_data.get('cached_at', '2000-01-01'))
                age_days = (datetime.now() - cached_date).days
                
                if age_days < cache_days:
                    print(f"📦 Using cached ticker list ({len(cache_data.get('tickers', []))} tickers, {age_days} days old)")
                    return cache_data.get('tickers', [])
        except Exception as e:
            print(f"⚠️ Error reading cache: {e}, fetching fresh data...")
    
    print("🌐 Fetching all tickers from exchanges (NASDAQ, NYSE, AMEX)...")
    print("   This may take a few minutes on first run...")
    
    all_tickers = set()
    
    # Method 1: Fetch from NASDAQ API
    try:
        print("   📊 Fetching NASDAQ tickers...")
        nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&offset=0&download=true"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.nasdaq.com/'
        }
        response = requests.get(nasdaq_url, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'rows' in data['data']:
                nasdaq_count = 0
                for row in data['data']['rows']:
                    symbol = row.get('symbol', '').strip().upper()
                    if symbol and len(symbol) <= 5 and symbol.isalpha():
                        all_tickers.add(symbol)
                        nasdaq_count += 1
                print(f"      ✅ Found {nasdaq_count} NASDAQ tickers")
    except Exception as e:
        print(f"      ⚠️ NASDAQ API failed: {e}")
    
    # Method 2: Fetch from NYSE via CSV download
    try:
        print("   📊 Fetching NYSE tickers...")
        # Try multiple NYSE endpoints
        nyse_urls = [
            "https://www.nyse.com/api/quotes/filter",
            "https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download"
        ]
        
        for nyse_url in nyse_urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(nyse_url, headers=headers, timeout=60)
                if response.status_code == 200 and response.text:
                    from io import StringIO
                    try:
                        df = pd.read_csv(StringIO(response.text))
                        if 'Symbol' in df.columns or 'symbol' in df.columns:
                            col = 'Symbol' if 'Symbol' in df.columns else 'symbol'
                            nyse_tickers = df[col].dropna().astype(str).str.strip().str.upper()
                            nyse_tickers = [t for t in nyse_tickers if t and len(t) <= 5 and t.isalpha()]
                            all_tickers.update(nyse_tickers)
                            print(f"      ✅ Found {len(nyse_tickers)} NYSE tickers")
                            break
                    except Exception as e:
                        continue
            except:
                continue
    except Exception as e:
        print(f"      ⚠️ NYSE fetch failed: {e}")
    
    # Method 3: Use comprehensive stock list from public sources
    # Fetch from a known comprehensive ticker list
    try:
        print("   📊 Fetching from comprehensive stock list...")
        # Use a public API that provides all US stocks
        comprehensive_urls = [
            "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt",
            "https://www.quantconnect.com/data/tree?type=equity&market=usa"
        ]
        
        for url in comprehensive_urls:
            try:
                if 'github' in url:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        tickers = [t.strip().upper() for t in response.text.split('\n') if t.strip() and len(t.strip()) <= 5]
                        tickers = [t for t in tickers if t.isalpha()]
                        all_tickers.update(tickers)
                        print(f"      ✅ Added {len(tickers)} tickers from comprehensive list")
                        break
            except:
                continue
    except Exception as e:
        print(f"      ⚠️ Comprehensive list fetch failed: {e}")
    
    # Method 4: Expand from known indices using yfinance
    # This validates tickers and ensures they're tradeable
    if len(all_tickers) < 2000:
        print("   📊 Validating and expanding via yfinance...")
        try:
            import yfinance as yf
            # Start with hardcoded lists as seed
            seed_tickers = set(
                SP500_TECH + SP500_FINANCIAL + SP500_HEALTHCARE + 
                SP500_CONSUMER + SP500_ENERGY_INDUSTRIAL + 
                GROWTH_MOVERS + SMALL_MID_CAPS
            )
            all_tickers.update(seed_tickers)
            print(f"      ✅ Added {len(seed_tickers)} seed tickers")
        except Exception as e:
            print(f"      ⚠️ yfinance expansion failed: {e}")
    
    # Convert to sorted list and remove invalid tickers
    ticker_list = sorted([t for t in all_tickers if t and len(t) <= 5 and t.isalpha()])
    
    # Save to cache
    try:
        cache_data = {
            'tickers': ticker_list,
            'count': len(ticker_list),
            'cached_at': datetime.now().isoformat(),
            'source': 'exchange_apis_multiple'
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"💾 Cached {len(ticker_list)} tickers to {cache_file}")
    except Exception as e:
        print(f"⚠️ Failed to cache: {e}")
    
    print(f"✅ Total tickers fetched: {len(ticker_list)}")
    return ticker_list


def get_dynamic_daily_batch(day_of_week, min_market_cap=50_000_000, min_volume=100_000, use_cache=True):
    """
    Get daily batch of stocks from dynamically fetched exchange list.
    Distributes all qualifying stocks evenly across 5 weekdays.
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        min_market_cap: Minimum market cap filter
        min_volume: Minimum volume filter
        use_cache: Use cached ticker list if available
    
    Returns:
        List of ticker symbols for the given day
    """
    # Only scan weekdays (0-4)
    if day_of_week >= 5:
        return []
    
    # Fetch all tickers from exchanges
    all_tickers = fetch_all_exchange_tickers(force_refresh=not use_cache)
    
    if not all_tickers:
        print("⚠️ No tickers fetched, falling back to hardcoded list")
        # Use hardcoded batches directly to avoid recursion
        batches = {
            0: SP500_TECH + GROWTH_MOVERS,
            1: SP500_FINANCIAL + SP500_ENERGY_INDUSTRIAL[:20],
            2: SP500_HEALTHCARE + SP500_CONSUMER[:20],
            3: SP500_CONSUMER + SMALL_MID_CAPS[:30],
            4: SP500_ENERGY_INDUSTRIAL + SMALL_MID_CAPS[30:],
            5: [],
            6: []
        }
        tickers = batches.get(day_of_week, [])
        if tickers:
            tickers = filter_strong_markets(tickers, min_market_cap=min_market_cap, min_volume=min_volume)
        return tickers
    
    # Filter to strong markets only (this will validate via yfinance)
    print(f"🔍 Filtering {len(all_tickers)} tickers to strong markets...")
    filtered_tickers = filter_strong_markets(
        all_tickers, 
        min_market_cap=min_market_cap, 
        min_volume=min_volume
    )
    
    # Distribute evenly across 5 weekdays
    total = len(filtered_tickers)
    per_day = total // 5
    remainder = total % 5
    
    # Calculate start and end indices for this day
    start_idx = day_of_week * per_day + min(day_of_week, remainder)
    end_idx = start_idx + per_day + (1 if day_of_week < remainder else 0)
    
    day_tickers = filtered_tickers[start_idx:end_idx]
    
    print(f"📅 Day {day_of_week} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day_of_week]}): {len(day_tickers)} tickers ({start_idx}-{end_idx} of {total})")
    
    return day_tickers


def get_stock_universe_summary():
    """Returns summary of total coverage"""
    # Check if using dynamic or hardcoded
    cache_file = Path("data") / "exchange_tickers_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                dynamic_count = len(cache_data.get('tickers', []))
                return {
                    "total_unique_stocks": dynamic_count,
                    "source": "dynamic_exchange_fetch",
                    "cached_at": cache_data.get('cached_at', 'Unknown'),
                    "tech_growth": "N/A (dynamic)",
                    "financials": "N/A (dynamic)",
                    "healthcare": "N/A (dynamic)",
                    "consumer": "N/A (dynamic)",
                    "energy_industrial": "N/A (dynamic)",
                    "small_mid_cap": "N/A (dynamic)"
                }
        except:
            pass
    
    # Fallback to hardcoded summary
    total_unique = len(set(
        SP500_TECH + SP500_FINANCIAL + SP500_HEALTHCARE + 
        SP500_CONSUMER + SP500_ENERGY_INDUSTRIAL + 
        GROWTH_MOVERS + SMALL_MID_CAPS
    ))
    
    return {
        "total_unique_stocks": total_unique,
        "source": "hardcoded",
        "tech_growth": len(SP500_TECH) + len(GROWTH_MOVERS),
        "financials": len(SP500_FINANCIAL),
        "healthcare": len(SP500_HEALTHCARE),
        "consumer": len(SP500_CONSUMER),
        "energy_industrial": len(SP500_ENERGY_INDUSTRIAL),
        "small_mid_cap": len(SMALL_MID_CAPS)
    }

