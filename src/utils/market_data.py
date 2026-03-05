import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pyotp


class AngelOneMarketData:
    def __init__(self, api_key: str, client_code: str, password: str, totp_secret: str):
        self.api_key = api_key
        self.client_code = client_code
        self.password = password
        self.totp_secret = totp_secret
        
        from SmartApi import SmartConnect
        self.obj = SmartConnect(api_key=api_key)
        
        self.connected = False
        self._login()
    
    def _login(self):
        """Login to Angel One"""
        try:
            totp = pyotp.TOTP(self.totp_secret).now()
            data = self.obj.generateSession(self.client_code, self.password, totp)
            
            if data.get('status'):
                self.obj.generateToken(data['data']['refreshToken'])
                self.connected = True
                print(f"✅ Connected to Angel One: {data['data']['clientcode']}")
                return True
            else:
                print(f"❌ Login failed: {data.get('message')}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_ltp(self, exchange: str, symbol: str, token: str) -> Optional[float]:
        """Get Last Traded Price"""
        if not self.connected:
            self._login()
        
        try:
            ltp = self.obj.ltpData(exchange, symbol, token)
            if ltp.get('status'):
                return float(ltp['data']['ltp'])
        except Exception as e:
            print(f"Error getting LTP: {e}")
        return None
    
    def get_index_quote(self, symbol: str = "NIFTY", token: str = "99926000") -> Dict:
        """Get index quote with additional data"""
        ltp = self.get_ltp("NSE", symbol, token)
        
        return {
            "symbol": symbol,
            "ltp": ltp,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_day_open(self, symbol: str, token: str) -> Optional[float]:
        """Get today's opening price"""
        try:
            # Get ONE_DAY candle for today
            df = self.get_historical_data(symbol, token, days=1, interval="ONE_DAY")
            if df is not None and not df.empty:
                return float(df['open'].iloc[-1])
        except Exception as e:
            print(f"Error getting day open: {e}")
        return None
    
    def get_historical_data(self, symbol: str, token: str, days: int = 30, interval: str = "ONE_DAY") -> Optional[pd.DataFrame]:
        """Get historical candle data"""
        if not self.connected:
            self._login()
        
        try:
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            to_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            candle = self.obj.getCandleData({
                'exchange': 'NSE',
                'symboltoken': token,
                'fromdate': from_date,
                'todate': to_date,
                'interval': interval
            })
            
            if candle.get('status'):
                df = pd.DataFrame(candle['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': int})
                return df
        except Exception as e:
            print(f"Error getting historical data: {e}")
        return None
    
    def get_market_depth(self, exchange: str, symbol: str, token: str) -> Optional[Dict]:
        """Get market depth (bid/ask)"""
        if not self.connected:
            self._login()
        
        try:
            md = self.obj.getMarketData("full", {exchange: [token]})
            if md.get('status'):
                return md['data']
        except Exception as e:
            print(f"Error getting market depth: {e}")
        return None
    
    def get_intraday_data(self, index: str = "NIFTY") -> Optional[List]:
        """Get intraday market data"""
        if not self.connected:
            self._login()
        
        try:
            data = self.obj.nseIntraday()
            if data.get('status'):
                return data['data']
        except Exception as e:
            print(f"Error getting intraday data: {e}")
        return None
    
    def get_options_data(self, symbol: str = "NIFTY", expiry: str = None) -> Optional[Dict]:
        """Get options chain data"""
        if not self.connected:
            self._login()
        
        if expiry is None:
            expiry = (datetime.now() + timedelta(days=30)).strftime('%d%b%Y').upper()
        
        try:
            oi = self.obj.oIBuildup({
                'exchange': 'NSE',
                'symbol': symbol,
                'expiry': expiry
            })
            if oi.get('status'):
                return oi['data']
        except Exception as e:
            print(f"Error getting options data: {e}")
        return None


class LiveMarketMonitor:
    def __init__(self):
        self.market_data = None
        self.last_update = None
    
    def get_current_market(self) -> Dict:
        """Get current market snapshot"""
        return {
            "status": "live",
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
    
    def calculate_pcr(self, calls_oi: int, puts_oi: int) -> float:
        """Calculate Put-Call Ratio"""
        if calls_oi == 0:
            return 1.0
        return puts_oi / calls_oi
    
    def get_market_sentiment(self, pcr: float) -> str:
        """Get market sentiment from PCR"""
        if pcr < 0.7:
            return "STRONG_BULLISH"
        elif pcr < 1.0:
            return "BULLISH"
        elif pcr > 1.5:
            return "STRONG_BEARISH"
        elif pcr > 1.0:
            return "BEARISH"
        return "NEUTRAL"


def test_market_data():
    print("\n" + "="*50)
    print("📡 ANGEL ONE MARKET DATA TEST")
    print("="*50 + "\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = '02F21hiq'
    client_code = 'M450789'
    password = '0492'
    totp_secret = 'KRFPVGCL7J2EBSHTN2JQH3USUQ'
    
    market = AngelOneMarketData(api_key, client_code, password, totp_secret)
    
    if market.connected:
        print("\n📊 Index Quotes:")
        
        indices = [
            ("NIFTY", "99926000"),
            ("BANKNIFTY", "99926009"),
        ]
        
        for symbol, token in indices:
            quote = market.get_index_quote(symbol, token)
            print(f"   {symbol}: ₹{quote['ltp']}")
        
        print("\n📈 Historical Data:")
        df = market.get_historical_data("NIFTY", "99926000", days=5)
        if df is not None:
            print(f"   Got {len(df)} days")
            print(f"   Close: {df['close'].iloc[-1]}")
            print(f"   High: {df['high'].max():.2f}")
            print(f"   Low: {df['low'].min():.2f}")
        
        print("\n📊 Intraday Data:")
        intraday = market.get_intraday_data()
        if intraday:
            print(f"   Records: {len(intraday)}")
    
    print("\n✅ Test Complete!")


if __name__ == "__main__":
    test_market_data()
