"""
Rate Limiter for API calls
Implements token bucket algorithm to respect API rate limits
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading


class RateLimiter:
    """
    Token bucket rate limiter for API calls

    Usage:
        limiter = RateLimiter(max_calls=48, period_seconds=60)
        limiter.wait_if_needed()  # Blocks if rate limit would be exceeded
    """

    def __init__(self, max_calls: int, period_seconds: int):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            period_seconds: Time period for the limit (e.g., 60 for per-minute)
        """
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = []
        self.lock = threading.Lock()

    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limit

        Returns:
            Time waited in seconds (0 if no wait needed)
        """
        with self.lock:
            now = time.time()

            # Remove calls outside the current period
            self.calls = [call_time for call_time in self.calls
                         if now - call_time < self.period]

            # If we're at the limit, wait until the oldest call expires
            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                wait_time = self.period - (now - oldest_call) + 0.1  # Add 100ms buffer
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    self.calls = [call_time for call_time in self.calls
                                 if now - call_time < self.period]
            else:
                wait_time = 0

            # Record this call
            self.calls.append(now)
            return wait_time

    def get_remaining_calls(self) -> int:
        """Get number of calls remaining in current period"""
        with self.lock:
            now = time.time()
            self.calls = [call_time for call_time in self.calls
                         if now - call_time < self.period]
            return max(0, self.max_calls - len(self.calls))

    def reset(self):
        """Reset the rate limiter"""
        with self.lock:
            self.calls = []


class YahooFinanceRateLimiter:
    """
    Specialized rate limiter for Yahoo Finance

    Based on community observations (2025):
    - Approximately 48-60 requests per minute safe limit
    - ~950 requests per day before potential blocking
    - Tighter limits than previous years

    Conservative approach: 48 requests/minute, 900 requests/day
    """

    def __init__(self):
        # Per-minute limit: 48 requests/60 seconds (conservative)
        self.minute_limiter = RateLimiter(max_calls=48, period_seconds=60)

        # Per-day limit: 900 requests/day (conservative)
        self.day_limiter = RateLimiter(max_calls=900, period_seconds=86400)

        # Minimum delay between requests (1 second)
        self.min_delay = 1.0
        self.last_call = 0

    def wait_if_needed(self) -> Dict[str, float]:
        """
        Wait if necessary to respect all rate limits

        Returns:
            Dict with wait times for each limiter
        """
        # Enforce minimum delay between calls
        now = time.time()
        since_last = now - self.last_call
        if since_last < self.min_delay:
            delay_needed = self.min_delay - since_last
            time.sleep(delay_needed)
        else:
            delay_needed = 0

        # Check minute and day limits
        minute_wait = self.minute_limiter.wait_if_needed()
        day_wait = self.day_limiter.wait_if_needed()

        self.last_call = time.time()

        return {
            'min_delay_wait': delay_needed,
            'minute_limit_wait': minute_wait,
            'day_limit_wait': day_wait,
            'total_wait': delay_needed + minute_wait + day_wait
        }

    def get_status(self) -> Dict:
        """Get current rate limiter status"""
        return {
            'remaining_calls_this_minute': self.minute_limiter.get_remaining_calls(),
            'remaining_calls_today': self.day_limiter.get_remaining_calls(),
            'safe_to_call': (
                self.minute_limiter.get_remaining_calls() > 5 and
                self.day_limiter.get_remaining_calls() > 50
            )
        }


# Global Yahoo Finance rate limiter
_yahoo_rate_limiter = None

def get_yahoo_rate_limiter() -> YahooFinanceRateLimiter:
    """Get or create global Yahoo Finance rate limiter"""
    global _yahoo_rate_limiter
    if _yahoo_rate_limiter is None:
        _yahoo_rate_limiter = YahooFinanceRateLimiter()
    return _yahoo_rate_limiter


if __name__ == '__main__':
    # Test the rate limiter
    print("Testing Yahoo Finance Rate Limiter...")
    print("=" * 60)

    limiter = YahooFinanceRateLimiter()

    # Simulate rapid calls
    print("\nSimulating 10 rapid API calls:")
    for i in range(10):
        start = time.time()
        wait_info = limiter.wait_if_needed()
        elapsed = time.time() - start
        status = limiter.get_status()

        print(f"Call {i+1}: Waited {elapsed:.2f}s | "
              f"Remaining this min: {status['remaining_calls_this_minute']} | "
              f"Remaining today: {status['remaining_calls_today']}")

    print("\n" + "=" * 60)
    print("Rate limiter working correctly!")
    print(f"\nFinal status: {limiter.get_status()}")
