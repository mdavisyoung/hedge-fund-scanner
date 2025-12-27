# ============================================================================
# FILE 3: scanner/market_scanner.py
# Main scanning engine that orchestrates daily scans
# ============================================================================

"""
Market Scanner
Scans stocks, scores opportunities, manages hot/warming/watching lists
"""

import sys
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import StockAnalyzer
from scanner.scoring import TradeScorer
from scanner.stock_universe import get_daily_batch


class MarketScanner:
    """Main scanner class"""
    
    def __init__(self, max_workers=10):
        self.analyzer = StockAnalyzer()
        self.scorer = TradeScorer()
        self.max_workers = max_workers
        
    def scan_daily_batch(self, day_of_week=None, min_market_cap=50_000_000, min_volume=100_000):
        """
        Scan today's batch of stocks with market filtering
        
        Args:
            day_of_week: 0-6, if None uses today
            min_market_cap: Minimum market cap filter (default $50M)
            min_volume: Minimum average volume filter (default 100k, 0 to disable)
            
        Returns:
            Dict with hot, warming, watching stocks
        """
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        
        print(f"📅 Scanning batch for day {day_of_week}...")
        
        # Get stock list (already filtered by get_daily_batch if enabled)
        tickers = get_daily_batch(day_of_week, filter_weak_markets=True, min_market_cap=min_market_cap)
        print(f"📊 Processing {len(tickers)} stocks (after market filtering)...")
        print(f"   Filters: Market cap >= ${min_market_cap:,}, Strong exchange, Volume >= {min_volume:,}")
        
        results = {
            'hot': [],
            'warming': [],
            'watching': [],
            'scanned_at': datetime.now().isoformat(),
            'day_of_week': day_of_week,
            'total_scanned': len(tickers)
        }
        
        # Parallel scanning with filters applied in _scan_single_stock
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self._scan_single_stock, ticker, min_market_cap, min_volume): ticker 
                for ticker in tickers
            }
            
            completed = 0
            filtered_out = 0
            for future in as_completed(future_to_ticker):
                completed += 1
                if completed % 50 == 0:
                    print(f"   Progress: {completed}/{len(tickers)} stocks...")
                
                result = future.result()
                if result:  # None if filtered out
                    score = result['score']['total_score']
                    if score >= 80:
                        results['hot'].append(result)
                    elif score >= 70:
                        results['warming'].append(result)
                    elif score >= 60:
                        results['watching'].append(result)
                else:
                    filtered_out += 1
        
        # Sort by score
        results['hot'].sort(key=lambda x: x['score']['total_score'], reverse=True)
        results['warming'].sort(key=lambda x: x['score']['total_score'], reverse=True)
        results['watching'].sort(key=lambda x: x['score']['total_score'], reverse=True)
        
        print(f"✅ Scan complete!")
        print(f"   🔥 Hot: {len(results['hot'])}")
        print(f"   🟡 Warming: {len(results['warming'])}")
        print(f"   👀 Watching: {len(results['watching'])}")
        
        return results
    
    def _scan_single_stock(self, ticker, min_market_cap=50_000_000, min_volume=100_000):
        """Scan and score a single stock with market filtering"""
        try:
            # Get evaluation
            evaluation = self.analyzer.evaluate_stock(ticker)
            
            if 'error' in evaluation:
                return None
            
            fundamentals = evaluation['fundamentals']
            
            # PRIMARY FILTER: Market cap (fast check)
            market_cap = fundamentals.get('market_cap', 0)
            if market_cap < min_market_cap:
                return None  # Skip low market cap stocks
            
            # SECONDARY FILTER: Strong market only (NYSE, NASDAQ, AMEX)
            if not fundamentals.get('is_strong_market', False):
                return None  # Skip OTC, pink sheets, etc.
            
            # OPTIONAL FILTER: Average volume (liquidity check)
            if min_volume > 0:
                avg_volume = fundamentals.get('average_volume', 0)
                if avg_volume < min_volume:
                    return None  # Skip low volume stocks
            
            stock_type = evaluation['stock_type']
            
            # Get price data for technical analysis
            price_data = self.analyzer.get_stock_data(ticker, "3mo")
            
            # Score the trade
            score_result = self.scorer.score_stock(
                fundamentals, 
                price_data, 
                stock_type
            )
            
            # Calculate entry/exit levels
            current_price = fundamentals['current_price']
            stop_loss = current_price * 0.90  # 10% stop
            target = current_price * 1.15  # 15% target
            risk_reward = (target - current_price) / (current_price - stop_loss)
            
            return {
                'ticker': ticker,
                'name': fundamentals['name'],
                'stock_type': stock_type,
                'score': score_result,
                'fundamentals': {
                    'current_price': current_price,
                    'pe_ratio': fundamentals['pe_ratio'],
                    'revenue_growth': fundamentals['revenue_growth'],
                    'roe': fundamentals['roe'],
                    'market_cap': fundamentals['market_cap'],
                    'beta': fundamentals['beta']
                },
                'trade_plan': {
                    'entry_price': round(current_price, 2),
                    'stop_loss': round(stop_loss, 2),
                    'target': round(target, 2),
                    'risk_reward_ratio': round(risk_reward, 2)
                },
                'criteria_met': evaluation['passed'],
                'criteria_total': evaluation['total'],
                'rating': evaluation['rating'],
                'scanned_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   Error scanning {ticker}: {str(e)}")
            return None
    
    def rescan_stocks(self, stock_list):
        """
        Re-scan specific stocks (for warming/hot updates)
        
        Args:
            stock_list: List of stock dicts with 'ticker' key
            
        Returns:
            Updated list with new scores
        """
        print(f"🔄 Re-scanning {len(stock_list)} stocks...")
        
        updated = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._scan_single_stock, stock['ticker']): stock 
                for stock in stock_list
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    updated.append(result)
        
        updated.sort(key=lambda x: x['score']['total_score'], reverse=True)
        
        print(f"✅ Re-scan complete: {len(updated)} stocks updated")
        return updated
    
    def filter_cold_stocks(self, stock_list, min_score=60):
        """Remove stocks below minimum score"""
        return [s for s in stock_list if s['score']['total_score'] >= min_score]

