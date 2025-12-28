# ============================================================================
# FILE 1: scanner/stock_universe.py - OPTIMIZED VERSION
# Defines which stocks to scan each day of the week
# ============================================================================

"""
Stock Universe Manager - OPTIMIZED
Provides daily batches of stocks for the rolling scanner
Now supports dynamic fetching from exchanges (NASDAQ, NYSE, AMEX)
KEY FIX: Pre-filters during fetch using BULK data (no slow API calls)
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

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


def fetch_all_exchange_tickers(force_refresh=False, cache_days=7, min_market_cap=50_000_000, min_volume=100_000):
    """
    Fetch all tickers from NASDAQ, NYSE, and AMEX exchanges dynamically.
    
    KEY OPTIMIZATION: Pre-filters during fetch using BULK data from APIs.
    No individual stock API calls needed - everything filtered in one pass!
    
    Args:
        force_refresh: If True, ignore cache and fetch fresh data
        cache_days: Number of days to cache the ticker list (default 7)
        min_market_cap: Minimum market cap filter (default $50M)
        min_volume: Minimum volume filter (default 100k, 0 to disable)
    
    Returns:
        List of PRE-FILTERED ticker symbols from qualifying exchanges
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
                
                # Check if filters match
                cached_filters = cache_data.get('filters', {})
                if (age_days < cache_days and 
                    cached_filters.get('min_market_cap') == min_market_cap and
                    cached_filters.get('min_volume') == min_volume):
                    print(f"[CACHE] Using cached PRE-FILTERED ticker list")
                    print(f"   {len(cache_data.get('tickers', []))} tickers (cached {age_days} days ago)")
                    print(f"   Filters: Market cap >= ${min_market_cap:,}, Volume >= {min_volume:,}")
                    return cache_data.get('tickers', [])
        except Exception as e:
            print(f"[WARNING] Error reading cache: {e}, fetching fresh data...")

    print("[FETCH] Fetching and PRE-FILTERING tickers from exchanges...")
    print(f"   Filters: Market cap >= ${min_market_cap:,}, Volume >= {min_volume:,}")
    print(f"   This will take ~2-5 minutes, then cached for {cache_days} days...")
    
    qualifying_tickers = []
    stats = {'total_fetched': 0, 'filtered_market_cap': 0, 'filtered_exchange': 0, 'filtered_volume': 0}
    
    # ============================================================================
    # METHOD 1: NASDAQ API (BEST - Provides market cap, volume, exchange in bulk)
    # ============================================================================
    try:
        print("\n   [API] Fetching from NASDAQ API (primary source)...")
        nasdaq_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25000&offset=0&download=true"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.nasdaq.com/'
        }
        
        response = requests.get(nasdaq_url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'rows' in data['data']:
                for row in data['data']['rows']:
                    stats['total_fetched'] += 1
                    
                    # Extract data
                    symbol = row.get('symbol', '').strip().upper()
                    exchange = row.get('exchange', '').upper()
                    
                    # Parse market cap (comes as string like "$1.5B" or "$500M")
                    market_cap_str = row.get('marketCap', '0')
                    try:
                        # Remove $ and convert B/M to numbers
                        market_cap = 0
                        if isinstance(market_cap_str, str):
                            market_cap_str = market_cap_str.replace('$', '').replace(',', '').strip()
                            if 'B' in market_cap_str:
                                market_cap = float(market_cap_str.replace('B', '')) * 1_000_000_000
                            elif 'M' in market_cap_str:
                                market_cap = float(market_cap_str.replace('M', '')) * 1_000_000
                            elif 'T' in market_cap_str:
                                market_cap = float(market_cap_str.replace('T', '')) * 1_000_000_000_000
                            else:
                                market_cap = float(market_cap_str) if market_cap_str else 0
                        elif isinstance(market_cap_str, (int, float)):
                            market_cap = float(market_cap_str)
                    except (ValueError, AttributeError):
                        market_cap = 0
                    
                    # Parse volume
                    volume = 0
                    volume_str = row.get('volume', '0')
                    try:
                        if isinstance(volume_str, str):
                            volume_str = volume_str.replace(',', '').strip()
                            volume = int(float(volume_str)) if volume_str else 0
                        elif isinstance(volume_str, (int, float)):
                            volume = int(volume_str)
                    except (ValueError, AttributeError):
                        volume = 0
                    
                    # Validate symbol
                    if not symbol or len(symbol) > 5 or not symbol.replace('.', '').isalpha():
                        continue

                    # FILTER 1: Market cap
                    if market_cap < min_market_cap:
                        stats['filtered_market_cap'] += 1
                        continue

                    # FILTER 2: Volume (if enabled)
                    if min_volume > 0 and volume < min_volume:
                        stats['filtered_volume'] += 1
                        continue
                    
                    # Passed all filters!
                    if symbol not in qualifying_tickers:
                        qualifying_tickers.append(symbol)
                
                print(f"      [OK] NASDAQ API: Found {len(qualifying_tickers)} qualifying tickers")
                print(f"         Filtered out: {stats['filtered_market_cap']} (low market cap), "
                      f"{stats['filtered_volume']} (low volume)")

    except Exception as e:
        print(f"      [WARNING] NASDAQ API failed: {e}")
    
    # ============================================================================
    # METHOD 2: Add hardcoded high-quality stocks (safety net)
    # ============================================================================
    print("\n   [SAFETY] Adding curated high-quality stocks as safety net...")
    safety_net = list(set(
        SP500_TECH + SP500_FINANCIAL + SP500_HEALTHCARE +
        SP500_CONSUMER + SP500_ENERGY_INDUSTRIAL +
        GROWTH_MOVERS + SMALL_MID_CAPS
    ))

    added = 0
    for ticker in safety_net:
        if ticker not in qualifying_tickers:
            qualifying_tickers.append(ticker)
            added += 1

    print(f"      [OK] Added {added} curated tickers to ensure quality stocks included")

    # ============================================================================
    # Final cleanup and sorting
    # ============================================================================
    # Remove any duplicates and sort alphabetically
    qualifying_tickers = sorted(list(set(qualifying_tickers)))

    print(f"\n[SUCCESS] Total qualifying tickers: {len(qualifying_tickers)}")
    print(f"   Will be distributed across 5 weekdays (~{len(qualifying_tickers)//5} per day)")
    
    # Save to cache
    try:
        cache_data = {
            'tickers': qualifying_tickers,
            'count': len(qualifying_tickers),
            'cached_at': datetime.now().isoformat(),
            'filters': {
                'min_market_cap': min_market_cap,
                'min_volume': min_volume
            },
            'stats': stats,
            'source': 'nasdaq_api_bulk_filtered'
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"[CACHE] Cached to {cache_file} (valid for {cache_days} days)")
    except Exception as e:
        print(f"[WARNING] Failed to cache: {e}")
    
    return qualifying_tickers


def get_daily_batch(day_of_week, filter_weak_markets=True, min_market_cap=50_000_000, use_dynamic=False, min_volume=100_000):
    """
    Returns stock list for given day.
    
    KEY DESIGN: When using dynamic mode, tickers are ALREADY PRE-FILTERED
    during fetch, so we just divide them across the week.
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        filter_weak_markets: Ignored in dynamic mode (already filtered)
        min_market_cap: Minimum market cap for filtering (default $50M)
        use_dynamic: If True, fetch from exchanges dynamically instead of hardcoded list
        min_volume: Minimum volume filter (for dynamic mode)
        
    Returns:
        List of ticker symbols for this day
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
    
    # Apply market filtering if requested (only for hardcoded mode)
    if filter_weak_markets and tickers:
        tickers = filter_strong_markets_legacy(tickers, min_market_cap=min_market_cap)
    
    return tickers


def filter_strong_markets_legacy(tickers, min_market_cap=50_000_000, min_volume=100_000):
    """
    Legacy filter for hardcoded lists only.
    For dynamic mode, filtering happens during fetch (much faster).
    
    This validates hardcoded tickers meet minimum requirements.
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
    
    print(f"[VALIDATE] Validating {len(tickers)} hardcoded tickers...")
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
    
    print(f"[OK] Validated {len(filtered_tickers)} tickers")
    if skipped_low_cap + skipped_weak_market + skipped_low_volume > 0:
        print(f"   Skipped: {skipped_low_cap} low market cap, {skipped_weak_market} weak market, {skipped_low_volume} low volume")
    
    return filtered_tickers


def get_dynamic_daily_batch(day_of_week, min_market_cap=50_000_000, min_volume=100_000, use_cache=True):
    """
    Get daily batch of stocks from dynamically fetched exchange list.
    
    KEY OPTIMIZATION: Tickers are ALREADY PRE-FILTERED during fetch!
    We just divide the pre-filtered list across 5 weekdays.
    
    This means scanning ALL stocks over the WEEK, not all in one day.
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        min_market_cap: Minimum market cap filter
        min_volume: Minimum volume filter
        use_cache: Use cached ticker list if available
    
    Returns:
        List of ticker symbols for the given day (~20% of total universe)
    """
    # Only scan weekdays (0-4)
    if day_of_week >= 5:
        print("[WEEKEND] Weekend - no dynamic scan scheduled")
        return []
    
    # Fetch all tickers (ALREADY PRE-FILTERED during fetch!)
    all_tickers = fetch_all_exchange_tickers(
        force_refresh=not use_cache,
        min_market_cap=min_market_cap,
        min_volume=min_volume
    )
    
    if not all_tickers:
        print("[WARNING] No tickers fetched, falling back to hardcoded list")
        batches = {
            0: SP500_TECH + GROWTH_MOVERS,
            1: SP500_FINANCIAL + SP500_ENERGY_INDUSTRIAL[:20],
            2: SP500_HEALTHCARE + SP500_CONSUMER[:20],
            3: SP500_CONSUMER + SMALL_MID_CAPS[:30],
            4: SP500_ENERGY_INDUSTRIAL + SMALL_MID_CAPS[30:],
        }
        return batches.get(day_of_week, [])
    
    # Distribute evenly across 5 weekdays
    total = len(all_tickers)
    per_day = total // 5
    remainder = total % 5
    
    # Calculate start and end indices for this day
    start_idx = day_of_week * per_day + min(day_of_week, remainder)
    end_idx = start_idx + per_day + (1 if day_of_week < remainder else 0)
    
    day_tickers = all_tickers[start_idx:end_idx]
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print(f"\n[BATCH] {day_names[day_of_week]} batch: {len(day_tickers)} tickers")
    print(f"   Range: {start_idx} to {end_idx} of {total} total")
    print(f"   Weekly coverage: {(day_of_week+1)*20}% complete")
    
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
                cached_date = cache_data.get('cached_at', 'Unknown')
                stats = cache_data.get('stats', {})
                
                return {
                    "total_unique_stocks": dynamic_count,
                    "per_day_average": dynamic_count // 5,
                    "source": "dynamic_exchange_fetch",
                    "cached_at": cached_date,
                    "filters": cache_data.get('filters', {}),
                    "stats": stats
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
        "per_day_average": total_unique // 5,
        "source": "hardcoded",
        "tech_growth": len(SP500_TECH) + len(GROWTH_MOVERS),
        "financials": len(SP500_FINANCIAL),
        "healthcare": len(SP500_HEALTHCARE),
        "consumer": len(SP500_CONSUMER),
        "energy_industrial": len(SP500_ENERGY_INDUSTRIAL),
        "small_mid_cap": len(SMALL_MID_CAPS)
    }
