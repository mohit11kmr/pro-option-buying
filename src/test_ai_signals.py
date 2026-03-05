import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


API_KEY = '02F21hiq'
CLIENT_CODE = 'M450789'
TOTP_SECRET = 'KRFPVGCL7J2EBSHTN2JQH3USUQ'


class MarketDataFetcher:
    def __init__(self):
        self.base_url = "https://apiconnect.angelone.in"
        self.session = requests.Session()
        self.access_token = None
        self.feed_token = None
        
    def login(self, client_code, totp_secret):
        try:
            import pyotp
            totp = pyotp.TOTP(totp_secret).now()
        except:
            print("Install pyotp: pip install pyotp")
            return False
        
        url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
        payload = {
            "clientCode": client_code,
            "password": "0492",
            "totp": totp
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Token": API_KEY
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('status') and data.get('data'):
                self.access_token = data['data']['jwtToken']
                self.feed_token = data['data']['feedToken']
                print(f"✅ Login successful for {client_code}")
                return True
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                print("⚠️ API credentials may have changed. Please update .env file")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_historical_data(self, symbol, exchange, from_date, to_date, interval):
        if not self.access_token:
            print("❌ Not logged in")
            return None
            
        url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
        
        params = {
            "exchange": exchange,
            "symboltoken": symbol,
            "fromdate": from_date,
            "todate": to_date,
            "interval": interval
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            data = response.json()
            
            if data.get('status'):
                candles = data['data']
                df = pd.DataFrame(candles)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df = df.astype({
                    'open': float, 'high': float, 'low': float, 
                    'close': float, 'volume': int
                })
                return df
            else:
                print(f"❌ Error getting data: {data.get('message')}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_market_depth(self, exchange, symbol_token):
        if not self.access_token:
            return None
            
        url = f"{self.base_url}/rest/secure/angelbroking/market/v1/quote"
        
        params = {
            "exchange": exchange,
            "symboltoken": symbol_token
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('status') and data.get('data'):
                return data['data']
            return None
        except:
            return None


def generate_realistic_market_data(base_price=25700, days=60):
    """Generate realistic-looking market data for testing"""
    np.random.seed(datetime.now().microsecond)
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='D')
    
    prices = [base_price]
    for i in range(days - 1):
        change = np.random.normal(0.001, 0.015)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    data = {
        'open': [],
        'high': [],
        'low': [],
        'close': prices,
        'volume': []
    }
    
    for close in prices:
        daily_range = close * np.random.uniform(0.005, 0.025)
        open_price = close + np.random.uniform(-daily_range/2, daily_range/2)
        high_price = max(open_price, close) + np.random.uniform(0, daily_range/2)
        low_price = min(open_price, close) - np.random.uniform(0, daily_range/2)
        
        data['open'].append(round(open_price, 2))
        data['high'].append(round(high_price, 2))
        data['low'].append(round(low_price, 2))
        data['volume'].append(int(np.random.uniform(2000000, 8000000)))
    
    df = pd.DataFrame(data, index=dates)
    return df


def test_ai_signals():
    print("\n" + "="*60)
    print("🧪 TESTING AI SIGNAL GENERATOR")
    print("="*60 + "\n")
    
    from utils.ml import AISignalGenerator, RiskAdjustedSignalGenerator
    from utils.ai_integration import AIIntegration
    from utils.ml.price_predictor import PricePredictor
    from utils.ml.pattern_recognizer import CandlestickPatternRecognizer
    from utils.ml.sentiment_analyzer import SentimentAnalyzer
    
    fetcher = MarketDataFetcher()
    
    print("📡 Attempting to login to Angel One...")
    df = None
    
    if fetcher.login(CLIENT_CODE, TOTP_SECRET):
        print("\n📊 Fetching NIFTY 50 historical data...")
        
        to_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        from_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
        
        NIFTY_TOKEN = "99926000"
        df = fetcher.get_historical_data(NIFTY_TOKEN, "NSE", from_date, to_date, "ONE_DAY")
    
    # Try to load cached live data first
    if os.path.exists('nifty_live.csv'):
        try:
            cached_df = pd.read_csv('nifty_live.csv', index_col='timestamp', parse_dates=True)
            if len(cached_df) >= 5:
                df = cached_df
                print(f"\n📈 Using cached live data: {len(df)} days")
        except:
            pass
    
    if df is None or len(df) < 30:
        print("\n📈 Using simulated market data...")
        df = generate_realistic_market_data(base_price=24900, days=60)
    
    print(f"\n📊 Market Data Summary:")
    print(f"   Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"   Days: {len(df)}")
    print(f"   Latest Close: {df['close'].iloc[-1]:.2f}")
    print(f"   30-Day High: {df['high'].max():.2f}")
    print(f"   30-Day Low: {df['low'].min():.2f}")
    print(f"   Avg Volume: {df['volume'].mean()/1000000:.1f}M")
    
    print("\n" + "="*60)
    print("🤖 AI SIGNAL ANALYSIS")
    print("="*60)
    
    generator = AISignalGenerator()
    signal = generator.generate_comprehensive_signal(df)
    
    print(f"\n🎯 FINAL RECOMMENDATION: {signal['recommendation']}")
    print(f"📊 Overall Score: {signal['score']}")
    print(f"🎯 Confidence: {signal['confidence']}%")
    
    print(f"\n📊 COMPONENT BREAKDOWN:")
    for comp, score in signal.get('components', {}).items():
        bar_len = int(abs(score) * 5)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        sign = "+" if score > 0 else "-"
        print(f"   {comp:20s}: [{bar}] {sign}{abs(score)}")
    
    print(f"\n📝 REASONS:")
    for reason in signal.get('reasons', []):
        print(f"   • {reason}")
    
    print("\n" + "-"*60)
    print("📈 DETAILED ANALYSIS")
    print("-"*60)
    
    print("\n   [Price Prediction]")
    price_pred = PricePredictor()
    prediction = price_pred.predict_next_candles(df, num_predictions=5)
    if 'error' not in prediction:
        print(f"      Direction: {prediction.get('direction')}")
        print(f"      Confidence: {prediction.get('confidence')}%")
        print(f"      Trend: {prediction.get('trend_strength')}")
        print(f"      Support: {prediction.get('support')}")
        print(f"      Resistance: {prediction.get('resistance')}")
    
    print("\n   [Pattern Recognition]")
    patterns = CandlestickPatternRecognizer()
    pattern_result = patterns.recognize_all_patterns(df)
    print(f"      Signal: {pattern_result.get('signal')}")
    print(f"      Strength: {pattern_result.get('strength')}")
    if pattern_result.get('patterns'):
        print(f"      Patterns Found: {len(pattern_result['patterns'])}")
        for p in pattern_result['patterns'][:3]:
            print(f"         - {p.get('pattern')} ({p.get('direction')})")
    
    print("\n   [Sentiment Analysis]")
    sample_news = [
        "NIFTY trades near all-time high with FII buying",
        "RBI maintains accommodative stance",
        "Global markets show mixed cues",
        "IT and banking sectors lead gains"
    ]
    sentiment = SentimentAnalyzer()
    news_sent = sentiment.analyze_news(sample_news)
    print(f"      Sentiment: {news_sent.get('overall_sentiment')}")
    print(f"      Market Mood: {news_sent.get('market_mood')}")
    
    print("\n" + "-"*60)
    print("💰 RISK-ADJUSTED SIGNAL")
    print("-"*60)
    
    risk_gen = RiskAdjustedSignalGenerator()
    account_balance = 100000
    risk_signal = risk_gen.generate_signal_with_risk(df, account_balance)
    
    print(f"\n   Recommendation: {risk_signal['recommendation']}")
    print(f"   Position Size: ₹{risk_signal.get('position_size', 0):.2f}")
    print(f"   Stop Loss: ₹{risk_signal.get('stop_loss', 0):.2f}")
    print(f"   Take Profit: ₹{risk_signal.get('take_profit', 0):.2f}")
    print(f"   Risk/Reward: {risk_signal.get('risk_reward_ratio', 0):.2f}")
    print(f"   Max Risk: ₹{risk_signal.get('max_risk_amount', 0):.2f}")
    
    integration = AIIntegration()
    print("\n" + "="*60)
    print("📱 TELEGRAM MESSAGE:")
    print("="*60)
    print(integration.format_signal_for_telegram(signal))
    
    return signal


def watch_market_sentiment():
    print("\n\n" + "="*60)
    print("📊 MARKET SENTIMENT MONITOR")
    print("="*60)
    
    from utils.ml.sentiment_analyzer import SentimentAnalyzer, OptionsSentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    
    print("\n📰 NEWS SENTIMENT")
    print("-"*40)
    
    news_samples = [
        ("Bullish", "NIFTY breaks 25800 resistance with strong volume"),
        ("Bullish", "FIIs buy 3000Cr, domestic flows continue"),
        ("Bullish", "RBI keeps rates unchanged, markets rally"),
        ("Bearish", "Global markets cautious on Fed comments"),
        ("Neutral", "Q4 earnings season begins next week")
    ]
    
    news_texts = [n[1] for n in news_samples]
    sentiment = analyzer.analyze_news(news_texts)
    
    print(f"   Overall: {sentiment['overall_sentiment']}")
    print(f"   Score: {sentiment['sentiment_score']}")
    print(f"   Mood: {sentiment['market_mood']}")
    
    print("\n📊 OPTIONS MARKET SENTIMENT")
    print("-"*40)
    
    options_analyzer = OptionsSentimentAnalyzer()
    
    scenarios = [
        {"calls_oi": 4500000, "puts_oi": 3500000, "name": "Strong Bullish"},
        {"calls_oi": 3500000, "puts_oi": 4500000, "name": "Strong Bearish"},
        {"calls_oi": 3000000, "puts_oi": 2800000, "name": "Slightly Bullish"},
        {"calls_oi": 2800000, "puts_oi": 3000000, "name": "Slightly Bearish"},
    ]
    
    for opts in scenarios:
        opts_data = {
            'calls_oi': opts['calls_oi'],
            'puts_oi': opts['puts_oi'],
            'calls_change_oi': 100000,
            'puts_change_oi': 50000
        }
        result = options_analyzer.analyze_options_data(opts_data)
        print(f"   {opts['name']}: PCR={result['put_call_ratio']} -> {result['sentiment']}")
    
    print("\n📈 INDICATOR-BASED SENTIMENT")
    print("-"*40)
    
    indicators_list = [
        {"fii_activity": 5000, "vix": 12, "put_call_ratio": 0.6, "market_breadth": 0.7, "name": "Bullish"},
        {"fii_activity": -5000, "vix": 25, "put_call_ratio": 1.5, "market_breadth": 0.3, "name": "Bearish"},
    ]
    
    for ind in indicators_list:
        market_data = {'indicators': ind}
        result = analyzer.analyze_market_sentiment_indicators(market_data)
        print(f"   {ind['name']}: {result['overall_sentiment']} ({result['sentiment_score']})")
        for sig in result['signals']:
            print(f"      - {sig}")


if __name__ == "__main__":
    print("\n" + "🔷"*20)
    print("   🤖 AI TRADING SIGNAL TESTER")
    print("🔷"*20)
    
    signal = test_ai_signals()
    watch_market_sentiment()
    
    print("\n\n✅ Testing Complete!")
    print("="*60)
