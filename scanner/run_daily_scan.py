# ============================================================================
# FILE 5: scanner/run_daily_scan.py
# Entry point for GitHub Actions
# ============================================================================

"""
Daily Scan Runner
Called by GitHub Actions to perform automated scans
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.market_scanner import MarketScanner
from utils.storage import StorageManager


def main():
    """Run daily scan"""
    print("=" * 60)
    print("🚀 HEDGE FUND SCANNER - Daily Run")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize
    scanner = MarketScanner(max_workers=10)
    storage = StorageManager()
    
    # Load existing data
    existing_hot = storage.load_hot_stocks()
    existing_warming = storage.load_warming_stocks()
    existing_watching = storage.load_watching_stocks()
    progress = storage.load_scan_progress()
    
    # Determine what to scan
    today = datetime.now().weekday()  # 0=Monday, 6=Sunday
    
    if today == 5:  # Saturday - rescan hot/warming only
        print("\n📅 Saturday: Re-scanning hot and warming stocks...")
        
        all_priority = existing_hot.get('stocks', []) + existing_warming.get('stocks', [])
        
        if all_priority:
            updated = scanner.rescan_stocks(all_priority)
            
            # Re-categorize
            new_hot = [s for s in updated if s['score']['total_score'] >= 80]
            new_warming = [s for s in updated if 70 <= s['score']['total_score'] < 80]
            
            # Clean out cold stocks
            new_hot = scanner.filter_cold_stocks(new_hot, min_score=80)
            new_warming = scanner.filter_cold_stocks(new_warming, min_score=70)
            
            storage.save_hot_stocks(new_hot)
            storage.save_warming_stocks(new_warming)
            
            print(f"\n✅ Saturday rescan complete:")
            print(f"   🔥 Hot: {len(new_hot)}")
            print(f"   🟡 Warming: {len(new_warming)}")
        else:
            print("   No stocks to rescan")
    
    elif today == 6:  # Sunday - no scan
        print("\n📅 Sunday: No scan scheduled")
        print("   Enjoy your day! Next scan: Monday 9:30am ET")
    
    else:  # Monday-Friday - full batch scan
        print(f"\n📅 Weekday scan (Day {today})...")
        
        # Scan today's batch with market filtering
        results = scanner.scan_daily_batch(today, min_market_cap=50_000_000, min_volume=100_000)
        
        # Re-scan yesterday's warming stocks (priority)
        print("\n🔄 Checking yesterday's warming stocks...")
        if existing_warming.get('stocks'):
            warming_updated = scanner.rescan_stocks(existing_warming['stocks'])
            
            # Promote to hot if qualified
            for stock in warming_updated:
                if stock['score']['total_score'] >= 80:
                    results['hot'].append(stock)
                    print(f"   📈 {stock['ticker']} graduated to HOT!")
                elif stock['score']['total_score'] >= 70:
                    results['warming'].append(stock)
        
        # Merge with existing (dedupe by ticker, keep highest score)
        final_hot = storage.merge_and_dedupe(results['hot'], existing_hot.get('stocks', []))
        final_warming = storage.merge_and_dedupe(results['warming'], existing_warming.get('stocks', []))
        final_watching = storage.merge_and_dedupe(results['watching'], existing_watching.get('stocks', []))
        
        # Clean out cold stocks
        final_hot = scanner.filter_cold_stocks(final_hot, min_score=80)
        final_warming = scanner.filter_cold_stocks(final_warming, min_score=70)
        final_watching = scanner.filter_cold_stocks(final_watching, min_score=60)
        
        # Save results
        storage.save_hot_stocks(final_hot)
        storage.save_warming_stocks(final_warming)
        storage.save_watching_stocks(final_watching)
        
        # Update progress
        progress['last_scan'] = datetime.now().isoformat()
        progress['day_of_week'] = today
        progress['total_scanned_this_week'] = progress.get('total_scanned_this_week', 0) + results['total_scanned']
        storage.save_scan_progress(progress)
        
        print(f"\n✅ Final counts after merge:")
        print(f"   🔥 Hot: {len(final_hot)}")
        print(f"   🟡 Warming: {len(final_warming)}")
        print(f"   👀 Watching: {len(final_watching)}")
        print(f"   📊 Total scanned this week: {progress['total_scanned_this_week']}")
    
    print("\n" + "=" * 60)
    print("✅ Scan complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

