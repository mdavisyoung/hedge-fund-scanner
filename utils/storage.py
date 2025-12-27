# ============================================================================
# FILE 4: utils/storage.py
# Handles reading/writing opportunity data
# ============================================================================

"""
Storage Manager
Handles persistence of scan results and trade history
"""

import json
import os
from datetime import datetime
from pathlib import Path


class StorageManager:
    """Manages JSON file storage for scan results"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.files = {
            'hot': self.data_dir / 'hot_stocks.json',
            'warming': self.data_dir / 'warming_stocks.json',
            'watching': self.data_dir / 'watching_stocks.json',
            'progress': self.data_dir / 'scan_progress.json',
            'history': self.data_dir / 'trade_history.json'
        }
    
    def load_hot_stocks(self):
        """Load hot opportunities"""
        return self._load_json(self.files['hot'], default={'stocks': [], 'updated_at': None})
    
    def load_warming_stocks(self):
        """Load warming opportunities"""
        return self._load_json(self.files['warming'], default={'stocks': [], 'updated_at': None})
    
    def load_watching_stocks(self):
        """Load watching list"""
        return self._load_json(self.files['watching'], default={'stocks': [], 'updated_at': None})
    
    def load_scan_progress(self):
        """Load scan progress"""
        default = {
            'last_scan': None,
            'day_of_week': 0,
            'week_number': datetime.now().isocalendar()[1],
            'total_scanned_this_week': 0
        }
        return self._load_json(self.files['progress'], default=default)
    
    def load_trade_history(self):
        """Load trade history"""
        return self._load_json(self.files['history'], default={'trades': []})
    
    def save_hot_stocks(self, stocks):
        """Save hot opportunities"""
        data = {
            'stocks': stocks,
            'updated_at': datetime.now().isoformat(),
            'count': len(stocks)
        }
        self._save_json(self.files['hot'], data)
    
    def save_warming_stocks(self, stocks):
        """Save warming opportunities"""
        data = {
            'stocks': stocks,
            'updated_at': datetime.now().isoformat(),
            'count': len(stocks)
        }
        self._save_json(self.files['warming'], data)
    
    def save_watching_stocks(self, stocks):
        """Save watching list"""
        data = {
            'stocks': stocks,
            'updated_at': datetime.now().isoformat(),
            'count': len(stocks)
        }
        self._save_json(self.files['watching'], data)
    
    def save_scan_progress(self, progress):
        """Save scan progress"""
        self._save_json(self.files['progress'], progress)
    
    def save_trade_history(self, history):
        """Save trade history"""
        self._save_json(self.files['history'], history)
    
    def add_trade(self, trade_data):
        """Add a trade to history"""
        history = self.load_trade_history()
        trade_data['executed_at'] = datetime.now().isoformat()
        history['trades'].insert(0, trade_data)  # Add to front
        self.save_trade_history(history)
    
    def _load_json(self, filepath, default=None):
        """Load JSON file with error handling"""
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
        
        return default if default is not None else {}
    
    def _save_json(self, filepath, data):
        """Save JSON file with error handling"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
    
    def merge_and_dedupe(self, new_stocks, existing_stocks):
        """
        Merge new scan results with existing, removing duplicates
        Keeps highest score for each ticker
        """
        # Create dict with ticker as key
        merged = {}
        
        # Add existing
        for stock in existing_stocks:
            ticker = stock['ticker']
            merged[ticker] = stock
        
        # Add/update with new (higher scores win)
        for stock in new_stocks:
            ticker = stock['ticker']
            if ticker not in merged or stock['score']['total_score'] > merged[ticker]['score']['total_score']:
                merged[ticker] = stock
        
        # Return as sorted list
        result = list(merged.values())
        result.sort(key=lambda x: x['score']['total_score'], reverse=True)
        return result

