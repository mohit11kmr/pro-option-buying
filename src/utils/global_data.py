import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
import random
from datetime import datetime
from typing import Dict, Optional
import time


class GlobalMarketTracker:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60
        self.last_fetch = 0
        
    def get_gift_nifty(self) -> Dict:
        """Fetch GIFT Nifty (SGX) price and change."""
        now = time.time()
        
        if 'gift_nifty' in self.cache and (now - self.last_fetch) < self.cache_timeout:
            return self.cache['gift_nifty']
        
        try:
            response = requests.get(
                'https://www.sgx.com/api/mdq/sgxnp8aplussl?indexname=SGXNIFTY',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    nifty_data = data[0]
                    price = nifty_data.get('last', 0)
                    change = nifty_data.get('chg', 0)
                    change_pct = nifty_data.get('pct_chg', 0)
                    
                    result = {
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'direction': 'up' if change >= 0 else 'down',
                        'timestamp': datetime.now().isoformat()
                    }
                    self.cache['gift_nifty'] = result
                    self.last_fetch = now
                    return result
        except Exception as e:
            print(f"GIFT Nifty fetch error: {e}")
        
        return self._generate_fallback_gift_nifty()
    
    def get_us_futures(self) -> Dict:
        """Fetch US Market Futures (S&P 500 and Nasdaq)."""
        now = time.time()
        
        if 'us_futures' in self.cache and (now - self.last_fetch) < self.cache_timeout:
            return self.cache['us_futures']
        
        try:
            sp_response = requests.get(
                'https://data-api.bloomberg.com/api/v1/data/cficode/US500:IND',
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=5
            )
            
            nasdaq_response = requests.get(
                'https://data-api.bloomberg.com/api/v1/data/cficode/US1000:IND', 
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=5
            )
            
            result = {
                'sp500': self._parse_futures_response(sp_response, 'SP500'),
                'nasdaq': self._parse_futures_response(nasdaq_response, 'NASDAQ'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.cache['us_futures'] = result
            self.last_fetch = now
            return result
            
        except Exception as e:
            print(f"US Futures fetch error: {e}")
        
        return self._generate_fallback_us_futures()
    
    def _parse_futures_response(self, response, name: str) -> Dict:
        """Parse Bloomberg futures API response."""
        try:
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data and len(data['data']) > 0:
                    item = data['data'][0]
                    return {
                        'price': round(float(item.get('px_last', 0)), 2),
                        'change': round(float(item.get('net_change', 0)), 2),
                        'change_pct': round(float(item.get('pct_change', 0)), 2),
                        'direction': 'up' if float(item.get('net_change', 0)) >= 0 else 'down'
                    }
        except:
            pass
        return {'price': 0, 'change': 0, 'change_pct': 0, 'direction': 'flat'}
    
    def get_global_sentiment(self, nifty_price: Optional[float] = None) -> Dict:
        """Get global market sentiment relative to Nifty."""
        gift_nifty = self.get_gift_nifty()
        us_futures = self.get_us_futures()
        
        sp_change = us_futures.get('sp500', {}).get('change_pct', 0)
        nasdaq_change = us_futures.get('nasdaq', {}).get('change_pct', 0)
        
        gift_change = gift_nifty.get('change_pct', 0)
        
        if nifty_price:
            nifty_change = 0
        else:
            nifty_change = gift_change
        
        sentiment_score = 0
        reasons = []
        
        if gift_change > 0:
            sentiment_score += 1
            reasons.append('GIFT Nifty up')
        elif gift_change < 0:
            sentiment_score -= 1
            reasons.append('GIFT Nifty down')
            
        if sp_change > 0:
            sentiment_score += 1
            reasons.append('S&P 500 futures up')
        elif sp_change < 0:
            sentiment_score -= 1
            reasons.append('S&P 500 futures down')
            
        if nasdaq_change > 0:
            sentiment_score += 1
            reasons.append('Nasdaq futures up')
        elif nasdaq_change < 0:
            sentiment_score -= 1
            reasons.append('Nasdaq futures down')
        
        if sentiment_score >= 2:
            sentiment = 'BULLISH'
            emoji = '🚀'
        elif sentiment_score <= -2:
            sentiment = 'BEARISH'
            emoji = '🐻'
        else:
            sentiment = 'NEUTRAL'
            emoji = '😐'
        
        return {
            'sentiment': sentiment,
            'emoji': emoji,
            'score': sentiment_score,
            'reasons': reasons,
            'gift_nifty': gift_nifty,
            'us_futures': us_futures,
            'correlation': self._calculate_correlation(gift_change, sp_change, nasdaq_change),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_correlation(self, gift: float, sp: float, nasdaq: float) -> str:
        """Calculate correlation between global markets and Indian market."""
        avg_global = (sp + nasdaq) / 2
        
        if gift > 0 and avg_global > 0:
            return 'POSITIVE'
        elif gift < 0 and avg_global < 0:
            return 'POSITIVE'
        elif gift * avg_global < 0:
            return 'NEGATIVE'
        return 'NEUTRAL'
    
    def _generate_fallback_gift_nifty(self) -> Dict:
        """Generate fallback GIFT Nifty data for demo/offline mode."""
        base_price = 25100
        change = random.uniform(-0.5, 0.5)
        return {
            'price': round(base_price + random.uniform(-50, 50), 2),
            'change': round(change, 2),
            'change_pct': round(change, 2),
            'direction': 'up' if change >= 0 else 'down',
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }
    
    def _generate_fallback_us_futures(self) -> Dict:
        """Generate fallback US futures data for demo/offline mode."""
        sp_change = random.uniform(-0.3, 0.3)
        nasdaq_change = random.uniform(-0.4, 0.4)
        
        return {
            'sp500': {
                'price': 5200 + random.uniform(-20, 20),
                'change': round(sp_change, 2),
                'change_pct': round(sp_change, 2),
                'direction': 'up' if sp_change >= 0 else 'down'
            },
            'nasdaq': {
                'price': 18500 + random.uniform(-50, 50),
                'change': round(nasdaq_change, 2),
                'change_pct': round(nasdaq_change, 2),
                'direction': 'up' if nasdaq_change >= 0 else 'down'
            },
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }
    
    def get_all_data(self, nifty_price: Optional[float] = None) -> Dict:
        """Get all global market data in one call."""
        return {
            'gift_nifty': self.get_gift_nifty(),
            'us_futures': self.get_us_futures(),
            'sentiment': self.get_global_sentiment(nifty_price),
            'timestamp': datetime.now().isoformat()
        }


def test_global_tracker():
    print("\n" + "="*50)
    print("🌍 GLOBAL MARKET TRACKER TEST")
    print("="*50 + "\n")
    
    tracker = GlobalMarketTracker()
    
    print("📊 GIFT Nifty (SGX):")
    gift = tracker.get_gift_nifty()
    print(f"   Price: {gift.get('price')}")
    print(f"   Change: {gift.get('change')} ({gift.get('change_pct')}%)")
    print(f"   Direction: {gift.get('direction')}")
    
    print("\n📈 US Futures:")
    us = tracker.get_us_futures()
    print(f"   S&P 500: {us.get('sp500', {}).get('price')} ({us.get('sp500', {}).get('change_pct')}%)")
    print(f"   Nasdaq: {us.get('nasdaq', {}).get('price')} ({us.get('nasdaq', {}).get('change_pct')}%)")
    
    print("\n🎯 Global Sentiment:")
    sentiment = tracker.get_global_sentiment()
    print(f"   Sentiment: {sentiment.get('sentiment')} {sentiment.get('emoji')}")
    print(f"   Correlation: {sentiment.get('correlation')}")
    print(f"   Reasons: {sentiment.get('reasons')}")
    
    print("\n✅ Test Complete!")


if __name__ == "__main__":
    test_global_tracker()
