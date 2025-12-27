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


def get_daily_batch(day_of_week):
    """
    Returns stock list for given day (0=Monday, 5=Saturday)
    
    Args:
        day_of_week: 0-6 (0=Monday, 6=Sunday)
        
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
    
    return batches.get(day_of_week, [])


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

