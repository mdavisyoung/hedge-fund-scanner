# ============================================================================
# FILE 1: scanner/stock_universe.py
# Defines which stocks to scan each day of the week
# ============================================================================

"""
Stock Universe Manager
Provides daily batches of stocks for the rolling scanner
"""

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


def get_daily_batch(day_of_week, filter_weak_markets=True, min_market_cap=50_000_000):
    """
    Returns stock list for given day
    Optionally filters out weak markets (OTC, pink sheets)
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        filter_weak_markets: If True, apply market filtering
        min_market_cap: Minimum market cap for filtering (default $50M)
        
    Returns:
        List of ticker symbols
    """
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


def get_stock_universe_summary():
    """Returns summary of total coverage"""
    total_unique = len(set(
        SP500_TECH + SP500_FINANCIAL + SP500_HEALTHCARE + 
        SP500_CONSUMER + SP500_ENERGY_INDUSTRIAL + 
        GROWTH_MOVERS + SMALL_MID_CAPS
    ))
    
    return {
        "total_unique_stocks": total_unique,
        "tech_growth": len(SP500_TECH) + len(GROWTH_MOVERS),
        "financials": len(SP500_FINANCIAL),
        "healthcare": len(SP500_HEALTHCARE),
        "consumer": len(SP500_CONSUMER),
        "energy_industrial": len(SP500_ENERGY_INDUSTRIAL),
        "small_mid_cap": len(SMALL_MID_CAPS)
    }

