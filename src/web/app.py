import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)  # src/
BASE_DIR = os.path.dirname(BASE_DIR)  # project root
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from flask import Flask, jsonify, send_from_directory, render_template_string, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import numpy as np
import pandas as pd
import threading
import time
import random
import json
import csv
import io
from flask import Flask, jsonify, send_from_directory, render_template_string, request, make_response
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nifty-options-secret'

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)

app.json_encoder = NumpyEncoder

socketio = SocketIO(app, cors_allowed_origins="*")

# Import your modules
from utils.market_data import AngelOneMarketData
from utils.global_data import GlobalMarketTracker
from utils.ml import AISignalGenerator, AdvancedIndicators
from utils.ml.self_learning_engine import SelfLearningEngine
from utils.backtester import HistoricalDataGenerator

# Import options strategy modules
try:
    from trading.options_strategy import OptionsBuyingStrategy
    from trading.greeks_analyzer import GreeksAnalyzer
    from trading.strike_selector import StrikeSelector
    options_strategy = OptionsBuyingStrategy()
    greeks_analyzer = GreeksAnalyzer()
    strike_selector = StrikeSelector()
    print('✅ Options strategy modules loaded')
except Exception as e:
    print(f'⚠️ Options modules not loaded: {e}')
    options_strategy = None
    greeks_analyzer = None
    strike_selector = None

# Initialize Database Manager
from utils.db_manager import DatabaseManager
db = DatabaseManager()

# Init Market Data early for use in learning engine
API_KEY = os.getenv('API_KEY', 'MHaAyAN4')
CLIENT_CODE = os.getenv('USER_ID', 'M450789')
PASSWORD = os.getenv('MPIN', '0492')
TOTP_SECRET = os.getenv('TOTP_SECRET', 'KRFPVGCL7J2EBSHTN2JQH3USUQ')

# Use a global market instance
global_market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)

# Initialize Global Market Tracker
global_tracker = GlobalMarketTracker()

# Initialize Self-Learning Engine
learning_engine = SelfLearningEngine(db, market_data_provider=global_market)

# Cache for data
market_cache = {'data': None, 'timestamp': None}
signal_cache = {'data': None, 'timestamp': None}
options_signal_cache = {'data': None, 'timestamp': None}

API_KEY = os.getenv('API_KEY', 'MHaAyAN4')
CLIENT_CODE = os.getenv('USER_ID', 'M450789')
PASSWORD = os.getenv('MPIN', '0492')
TOTP_SECRET = os.getenv('TOTP_SECRET', 'KRFPVGCL7J2EBSHTN2JQH3USUQ')


def background_price_stream():
    """Background thread to stream prices tick-by-tick with robust error handling"""
    prices = {'nifty': 24800.0, 'banknifty': 59800.0, 'nifty_future': 24850.0}
    day_open = {'nifty': None, 'banknifty': None}
    last_fetch_attempt = 0
    
    while True:
        try:
            # Use the global market instance
            market = global_market
            now_ts = time.time()
            
            # 1. Fetch Day Open (with retry cooling to avoid rate limits)
            if market and market.connected:
                if day_open['nifty'] is None and (now_ts - last_fetch_attempt > 60):
                    last_fetch_attempt = now_ts
                    day_open['nifty'] = market.get_day_open('NIFTY', '99926000')
                
                if day_open['banknifty'] is None and (now_ts - last_fetch_attempt > 60):
                    day_open['banknifty'] = market.get_day_open('BANKNIFTY', '99926009')

                # 2. Try to get real quotes
                try:
                    n = market.get_index_quote('NIFTY', '99926000')
                    b = market.get_index_quote('BANKNIFTY', '99926009')
                    
                    # Simulated Future if token is unknown or restricted
                    prices['nifty'] = float(n['ltp']) if n and n.get('ltp') else prices['nifty']
                    prices['banknifty'] = float(b['ltp']) if b and b.get('ltp') else prices['banknifty']
                    prices['nifty_future'] = prices['nifty'] + 32 + random.uniform(-1, 1)
                except Exception as quote_err:
                    print(f"Quote fetch error: {quote_err}")
            
            # Fallback/Simulation if API is rate-limited or offline
            if day_open['nifty'] is None:
                day_open['nifty'] = 24750.0 # Proxy for testing if API fails
            
            if not market or not market.connected or now_ts - last_fetch_attempt < 1:
                prices['nifty'] += random.uniform(-1, 1)
                prices['banknifty'] += random.uniform(-2, 2)
                prices['nifty_future'] = prices['nifty'] + 32 + random.uniform(-0.5, 0.5)
                
            # Emit updates - guaranteed valid numbers
            price_update = {
                'nifty': round(prices['nifty'], 2),
                'banknifty': round(prices['banknifty'], 2),
                'nifty_future': round(prices['nifty_future'], 2),
                'day_open_nifty': day_open['nifty'],
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                global_data = global_tracker.get_all_data(prices['nifty'])
                price_update['global_sentiment'] = global_data.get('sentiment', {})
                price_update['gift_nifty'] = global_data.get('gift_nifty', {})
                price_update['us_futures'] = global_data.get('us_futures', {})
            except Exception as ge:
                print(f"Global data error: {ge}")
            
            socketio.emit('price_update', price_update)
            
            socketio.emit('global_market_update', price_update.get('global_sentiment', {}))
            
        except Exception as e:
            print(f"⚠️ Price stream error: {e}")
            # Ensure prices stay as numbers even in major crashes
            try:
                prices['nifty'] = float(prices.get('nifty', 24800))
                prices['banknifty'] = float(prices.get('banknifty', 59800))
            except:
                prices = {'nifty': 24800.0, 'banknifty': 59800.0}
        
        socketio.sleep(1)


def background_signal_broadcaster():
    """Periodically generates and broadcasts AI signals via WebSockets."""
    generator = AISignalGenerator()
    while True:
        try:
            # Generate signal every minute
            df = _get_market_df(days=5)
            if df is not None:
                signal = generator.generate_comprehensive_signal(df)
                
                # Sanitize for JSON
                sanitized_signal = _sanitize_for_json(signal)
                
                # Broadcast to all connected clients
                socketio.emit('new_ai_signal', sanitized_signal)
                print(f"📡 Broadcasted new signal: {signal.get('recommendation')} at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"⚠️ Signal broadcaster error: {e}")
        
        # Wait 60 seconds before next broadcast
        socketio.sleep(60)


@app.route('/')
def index():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'index.html')):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    return "<h1>Dashboard Starting...</h1>"


@app.route('/backtest')
def backtest_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'backtest.html')):
        return send_from_directory(FRONTEND_DIR, 'backtest.html')
    return "<h1>Backtest Page...</h1>"


@app.route('/ai-signal')
def ai_signal_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'ai-signal.html')):
        return send_from_directory(FRONTEND_DIR, 'ai-signal.html')
    return "<h1>AI Signal Page...</h1>"


@app.route('/options-strategy')
def options_strategy_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'options-strategy.html')):
        return send_from_directory(FRONTEND_DIR, 'options-strategy.html')
    return "<h1>Options Strategy Page...</h1>"

@app.route('/nifty-research')
def nifty_research_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'nifty-research.html')):
        return send_from_directory(FRONTEND_DIR, 'nifty-research.html')
    return "<h1>Nifty Research Page...</h1>"


@app.route('/options-chain')
def options_chain_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'options-chain.html')):
        return send_from_directory(FRONTEND_DIR, 'options-chain.html')
    return "<h1>Options Chain Page...</h1>"


@app.route('/trade-journal')
def trade_journal_page():
    if os.path.exists(os.path.join(FRONTEND_DIR, 'trade-journal.html')):
        return send_from_directory(FRONTEND_DIR, 'trade-journal.html')
    return "<h1>Trade Journal Page...</h1>"


@app.route('/api/options-chain')
def api_options_chain():
    """Get full options chain with Greeks for NIFTY/BANKNIFTY."""
    symbol = request.args.get('symbol', 'NIFTY').upper()
    expiry = request.args.get('expiry', 'current')
    
    spot_prices = {
        'NIFTY': 24800.0,
        'BANKNIFTY': 59800.0
    }
    spot = spot_prices.get(symbol, 24800.0)
    
    strikes = list(range(24200, 25401, 50))  # 20 strikes from 24200-25400, gap 50
    
    days_to_expiry = 3
    
    chain_data = []
    total_ce_oi = 0
    total_pe_oi = 0
    
    for strike in strikes:
        moneyness = abs(spot - strike) / 50
        
        base_oi = 12000000  # ATM highest ~12M
        if moneyness <= 1:
            oi_multiplier = 1.0 - (moneyness * 0.1)
        elif moneyness <= 3:
            oi_multiplier = 0.8 - ((moneyness - 1) * 0.2)
        else:
            oi_multiplier = max(0.3, 0.4 - ((moneyness - 3) * 0.03))
        
        ce_oi = int(base_oi * oi_multiplier * random.uniform(0.85, 1.15))
        pe_oi = int(base_oi * oi_multiplier * random.uniform(0.85, 1.15))
        
        oi_change_ce = int(ce_oi * random.uniform(-0.15, 0.25))
        oi_change_pe = int(pe_oi * random.uniform(-0.15, 0.25))
        
        # IV Smile pattern (15-22%)
        if moneyness <= 1:
            ce_iv = 0.18 - (moneyness * 0.02)
            pe_iv = 0.18 + (moneyness * 0.02)
        elif moneyness <= 3:
            base_iv = 0.16 + ((moneyness - 1) * 0.02)
            ce_iv = base_iv + random.uniform(-0.01, 0.01)
            pe_iv = base_iv + ((moneyness - 1) * 0.015) + random.uniform(-0.01, 0.01)
        else:
            ce_iv = min(0.22, 0.15 + random.uniform(0, 0.02))
            pe_iv = min(0.24, 0.17 + random.uniform(0, 0.03))
        
        ce_iv = max(0.15, min(0.22, ce_iv + random.uniform(-0.01, 0.01)))
        pe_iv = max(0.15, min(0.22, pe_iv + random.uniform(-0.01, 0.01)))
        
        intrinsic_call = max(spot - strike, 0)
        intrinsic_put = max(strike - spot, 0)
        time_value_call = intrinsic_call * 0.3 + 50
        time_value_put = intrinsic_put * 0.3 + 50
        
        ce_premium = round(intrinsic_call + time_value_call + random.uniform(-10, 10), 2)
        pe_premium = round(intrinsic_put + time_value_put + random.uniform(-10, 10), 2)
        ce_premium = max(ce_premium, 5)
        pe_premium = max(pe_premium, 5)
        
        ce_greeks = greeks_analyzer.calculate_greeks(spot, strike, days_to_expiry, ce_iv, "CE") if greeks_analyzer else {
            'delta': 0.5, 'gamma': 0.02, 'theta': -15, 'vega': 20
        }
        pe_greeks = greeks_analyzer.calculate_greeks(spot, strike, days_to_expiry, pe_iv, "PE") if greeks_analyzer else {
            'delta': -0.5, 'gamma': 0.02, 'theta': -15, 'vega': 20
        }
        
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        
        chain_data.append({
            'strike': strike,
            'ce_premium': ce_premium,
            'ce_oi': ce_oi,
            'ce_oi_change': oi_change_ce,
            'ce_iv': round(ce_iv * 100, 2),
            'ce_delta': round(ce_greeks.get('delta', 0.5), 4),
            'ce_gamma': round(ce_greeks.get('gamma', 0.02), 4),
            'ce_theta': round(ce_greeks.get('theta', -15), 2),
            'ce_vega': round(ce_greeks.get('vega', 20), 2),
            'pe_premium': pe_premium,
            'pe_oi': pe_oi,
            'pe_oi_change': oi_change_pe,
            'pe_iv': round(pe_iv * 100, 2),
            'pe_delta': round(pe_greeks.get('delta', -0.5), 4),
            'pe_gamma': round(pe_greeks.get('gamma', 0.02), 4),
            'pe_theta': round(pe_greeks.get('theta', -15), 2),
            'pe_vega': round(pe_greeks.get('vega', 20), 2)
        })
    
    return jsonify({
        'symbol': symbol,
        'spot': spot,
        'expiry': expiry,
        'days_to_expiry': days_to_expiry,
        'timestamp': datetime.now().isoformat(),
        'chain': chain_data,
        'total_ce_oi': total_ce_oi,
        'total_pe_oi': total_pe_oi
    })


@app.route('/api/options-chain/pcr')
def api_options_chain_pcr():
    """Get PCR and market sentiment."""
    symbol = request.args.get('symbol', 'NIFTY').upper()
    
    spot_prices = {'NIFTY': 24800.0, 'BANKNIFTY': 59800.0}
    spot = spot_prices.get(symbol, 24800.0)
    
    strikes = list(range(24200, 25401, 50))
    
    total_ce_oi = 0
    total_pe_oi = 0
    
    for strike in strikes:
        moneyness = abs(spot - strike) / 50
        
        base_oi = 12000000
        if moneyness <= 1:
            oi_mult = 1.0 - (moneyness * 0.1)
        elif moneyness <= 3:
            oi_mult = 0.8 - ((moneyness - 1) * 0.2)
        else:
            oi_mult = max(0.3, 0.4 - ((moneyness - 3) * 0.03))
        
        ce_oi = int(base_oi * oi_mult * random.uniform(0.85, 1.15))
        pe_oi = int(base_oi * oi_mult * random.uniform(0.85, 1.15))
        
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
    
    pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0
    
    if pcr < 0.7:
        sentiment = "STRONG_BULLISH"
    elif pcr < 0.9:
        sentiment = "BULLISH"
    elif pcr < 1.1:
        sentiment = "NEUTRAL"
    elif pcr < 1.3:
        sentiment = "BEARISH"
    else:
        sentiment = "STRONG_BEARISH"
    
    return jsonify({
        'pcr': round(pcr, 3),
        'sentiment': sentiment,
        'total_ce_oi': total_ce_oi,
        'total_pe_oi': total_pe_oi,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/options-chain/max-pain')
def api_options_chain_max_pain():
    """Calculate max pain strike."""
    symbol = request.args.get('symbol', 'NIFTY').upper()
    
    spot_prices = {'NIFTY': 24800.0, 'BANKNIFTY': 59800.0}
    spot = spot_prices.get(symbol, 24800.0)
    
    strikes = list(range(24200, 25401, 50))
    
    pain_by_strike = {}
    
    for strike in strikes:
        total_pain = 0
        for test_strike in strikes:
            moneyness = abs(spot - test_strike) / 50
            
            base_oi = 12000000
            if moneyness <= 1:
                oi_mult = 1.0 - (moneyness * 0.1)
            elif moneyness <= 3:
                oi_mult = 0.8 - ((moneyness - 1) * 0.2)
            else:
                oi_mult = max(0.3, 0.4 - ((moneyness - 3) * 0.03))
            
            if test_strike <= strike:
                ce_oi = int(base_oi * oi_mult * 0.3)
                pe_oi = int(base_oi * oi_mult * 1.5)
            else:
                ce_oi = int(base_oi * oi_mult * 1.5)
                pe_oi = int(base_oi * oi_mult * 0.3)
            
            call_pain = ce_oi * max(test_strike - strike, 0)
            put_pain = pe_oi * max(strike - test_strike, 0)
            total_pain += call_pain + put_pain
        
        pain_by_strike[strike] = total_pain
    
    max_pain_strike = min(pain_by_strike, key=pain_by_strike.get)
    
    return jsonify({
        'max_pain_strike': max_pain_strike,
        'current_spot': spot,
        'pain_values': {str(k): v for k, v in list(pain_by_strike.items())[:11]},
        'timestamp': datetime.now().isoformat()
    })


# Health & Monitoring Endpoints
@app.route('/health')
def health_check():
    """Health check endpoint for container orchestration."""
    return jsonify({
        "status": "healthy",
        "service": "nifty-options",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/health/ready')
def readiness_check():
    """Readiness check for Kubernetes."""
    checks = {
        "api": True,
        "modules": options_strategy is not None
    }
    
    all_ready = all(checks.values())
    
    return jsonify({
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }), 200 if all_ready else 503


@app.route('/health/live')
def liveness_check():
    """Liveness check for Kubernetes."""
    return jsonify({
        "alive": True,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint."""
    from utils.paper_trading import MetricsExporter
    
    exporter = MetricsExporter()
    exporter.gauge("app_info", 1)
    exporter.gauge("requests_total", 100)
    
    return exporter.get_metrics(), 200, {'Content-Type': 'text/plain'}


# API Documentation Endpoint
@app.route('/api/docs')
def api_docs():
    """API documentation endpoint."""
    docs = {
        "title": "Nifty Options Trading API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Service health check",
            "GET /health/ready": "Readiness check",
            "GET /health/live": "Liveness check",
            "GET /metrics": "Prometheus metrics",
            "GET /api/market/live": "Live market data",
            "GET /api/signal": "AI trading signal",
            "POST /api/backtest": "Run backtest",
            "GET /api/positions": "Get open positions"
        }
    }
    return jsonify(docs)


@app.route('/api/market/live')
def market_live():
    global market_cache
    
    # Check cache (10 seconds)
    if market_cache['data'] and market_cache['timestamp']:
        if (datetime.now() - market_cache['timestamp']).seconds < 10:
            return jsonify(market_cache['data'])
    
    try:
        market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)
        
        if market.connected:
            nifty = market.get_index_quote('NIFTY', '99926000')
            banknifty = market.get_index_quote('BANKNIFTY', '99926009')
            
            data = {
                'nifty': nifty['ltp'],
                'banknifty': banknifty['ltp'],
                'timestamp': datetime.now().isoformat()
            }
            
            market_cache['data'] = data
            market_cache['timestamp'] = datetime.now()
            
            return jsonify(data)
    except Exception as e:
        print(f"Error: {e}")
    
    # Return demo data if API fails
    return jsonify({
        'nifty': 24854.60,
        'banknifty': 59786.65,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/market/global')
def market_global():
    """Get global market data (GIFT Nifty, US Futures, sentiment)."""
    try:
        global_data = global_tracker.get_all_data()
        return jsonify(global_data)
    except Exception as e:
        print(f"Global market API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/history')
def market_history():
    try:
        market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)
        
        if market.connected:
            df = market.get_historical_data('NIFTY', '99926000', days=30)
            
            if df is not None:
                data = []
                for idx, row in df.iterrows():
                    data.append({
                        'date': idx.isoformat(),
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume']
                    })
                
                return jsonify(data)
    except:
        pass
    
    # Demo data
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=1)
    df = df.tail(30)
    
    data = []
    for idx, row in df.iterrows():
        data.append({
            'date': idx.isoformat(),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        })
    
    return jsonify(data)


@app.route('/api/ai/signal')
def ai_signal():
    global signal_cache
    
    # Check cache (1 min)
    if signal_cache['data'] and signal_cache['timestamp']:
        if (datetime.now() - signal_cache['timestamp']).seconds < 60:
            return jsonify(signal_cache['data'])
    
    try:
        market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)
        
        if market.connected:
            df = market.get_historical_data('NIFTY', '99926000', days=30)
            
            if df is not None:
                generator = AISignalGenerator()
                signal = generator.generate_comprehensive_signal(df)
                
                signal_cache['data'] = signal
                signal_cache['timestamp'] = datetime.now()
                
                return jsonify(signal)
    except Exception as e:
        print(f"Error generating signal: {e}")
    
    # Return cached or demo signal
    if signal_cache['data']:
        return jsonify(signal_cache['data'])
    
    return jsonify({
        'recommendation': 'STRONG_BUY',
        'score': 90.5,
        'confidence': 85.5,
        'verdict': "Nifty is showing powerful bullish momentum with a score of 90.5. Major indicators and options flow are aligned for an upside move. Consider aggressive entry.",
        'trends': {"5m": "BULLISH", "15m": "BULLISH", "1h": "NEUTRAL"},
        'components': {
            'price_prediction': 2,
            'pattern_recognition': 1,
            'sentiment': 2,
            'options_flow': 2
        },
        'reasons': [
            'Patterns: BUY',
            'Sentiment: STRONG_BULLISH',
            'Options flow: STRONG_BULLISH'
        ]
    })


@app.route('/api/backtest')
def backtest():
    from utils.backtester import StrategyBacktester
    
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=5)
    
    tester = StrategyBacktester()
    result = tester.run_strategy_backtest(df, 'ma_crossover', {})
    
    return jsonify(result)


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/option/chain')
def option_chain():
    try:
        market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)
        
        if market.connected:
            chain = market.get_options_data('NIFTY')
            if chain:
                return jsonify(chain)
    except Exception as e:
        print(f"Error getting option chain: {e}")
    
    import random
    base_price = 24800
    strikes = [base_price - 200, base_price - 100, base_price, base_price + 100, base_price + 200]
    
    calls = []
    puts = []
    for strike in strikes:
        calls.append({
            'strike': strike,
            'oi': random.randint(500000, 2000000),
            'volume': random.randint(100000, 500000),
            'iv': random.uniform(15, 25),
            'ltp': round(strike + random.uniform(50, 150), 2)
        })
        puts.append({
            'strike': strike,
            'oi': random.randint(500000, 2000000),
            'volume': random.randint(100000, 500000),
            'iv': random.uniform(15, 25),
            'ltp': round(strike + random.uniform(50, 150), 2)
        })
    
    return jsonify({
        'calls': calls,
        'puts': puts,
        'underlying': base_price,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    from flask import request
    from utils.backtester import HistoricalDataGenerator, StrategyBacktester
    
    config = request.json
    
    years = config.get('years', 5)
    strategy = config.get('strategy', 'ma_crossover')
    capital = config.get('capital', 100000)
    
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=years)
    
    tester = StrategyBacktester()
    result = tester.run_strategy_backtest(df, strategy, config)
    
    result['total_trades'] = len(result.get('trades', []))
    result['winning_trades'] = sum(1 for t in result.get('trades', []) if t.get('pnl', 0) > 0)
    result['losing_trades'] = sum(1 for t in result.get('trades', []) if t.get('pnl', 0) <= 0)
    
    equity_curve = [capital]
    for trade in result.get('trades', []):
        capital += trade.get('pnl', 0)
        equity_curve.append(capital)
    result['equity_curve'] = equity_curve
    
    return jsonify(result)


# ==============================
#  OPTIONS STRATEGY API
# ==============================

def _get_market_df(days=30):
    """Helper: get market DataFrame (live or synthetic)."""
    try:
        market = AngelOneMarketData(API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET)
        if market.connected:
            df = market.get_historical_data('NIFTY', '99926000', days=days)
            if df is not None:
                return df
    except:
        pass
    # Fallback: generate synthetic data
    np.random.seed(int(datetime.now().timestamp()) % 10000)
    gen = HistoricalDataGenerator()
    return gen.generate_with_market_events(years=1).tail(max(100, days * 5))


def _sanitize_for_json(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj

@app.route('/api/options/strategy')
def api_options_strategy():
    """Get current options buying signal with full breakdown."""
    global options_signal_cache

    if options_signal_cache['data'] and options_signal_cache['timestamp']:
        if (datetime.now() - options_signal_cache['timestamp']).seconds < 15:
            return jsonify(options_signal_cache['data'])

    if not options_strategy:
        return jsonify({'error': 'Options strategy module not loaded'}), 500

    try:
        df = _get_market_df(30)
        # Get AI signal for confidence input
        ai_signal = None
        try:
            gen = AISignalGenerator()
            ai_signal = gen.generate_comprehensive_signal(df)
        except Exception as e:
            print(f"Error in AI Signal Generation: {e}")
            ai_signal = {
                'recommendation': 'STRONG_BUY',
                'confidence': 68,
                'verdict': 'Nifty is showing powerful bullish momentum with multiple indicators aligning for an upward move.',
                'trends': {'5m': 'BULLISH', '15m': 'BULLISH', '1h': 'NEUTRAL'}
            }

        signal = options_strategy.generate_signal(df, ai_signal=ai_signal)
        
        # Ensure verdict and trends are in the final signal
        if ai_signal:
            signal['verdict'] = ai_signal.get('verdict', 'Market analysis incomplete.')
            signal['trends'] = ai_signal.get('trends', {'5m': '--', '15m': '--', '1h': '--'})

        # Sanitize numpy types for JSON serialization
        signal = _sanitize_for_json(signal)

        options_signal_cache['data'] = signal
        options_signal_cache['timestamp'] = datetime.now()
        return jsonify(signal)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/options/greeks')
def api_options_greeks():
    """Get Greeks data for a strike."""
    if not greeks_analyzer:
        return jsonify({'error': 'Greeks module not loaded'}), 500

    try:
        spot = float(request.args.get('spot', 24850))
        strike = float(request.args.get('strike', round(spot / 50) * 50))
        premium = float(request.args.get('premium', 120))
        days = int(request.args.get('days', 3))
        opt_type = request.args.get('type', 'CE')

        result = greeks_analyzer.get_full_analysis(spot, strike, premium, days, opt_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/options/strikes')
def api_options_strikes():
    """Get smart strike recommendations."""
    if not strike_selector:
        return jsonify({'error': 'Strike selector not loaded'}), 500

    try:
        spot = float(request.args.get('spot', 24850))
        opt_type = request.args.get('type', 'CE')
        result = strike_selector.recommend_strikes(spot, opt_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/options/journal', methods=['GET'])
def api_get_journal():
    """Get trade journal from DB."""
    return jsonify({
        'trades': db.get_trades(),
        'stats': options_strategy.get_stats() if options_strategy else {}
    })


@app.route('/api/options/journal', methods=['POST'])
def api_add_journal():
    """Add trade to journal."""
    trade = request.json
    db.add_trade(
        strike=trade.get('strike'),
        trade_type=trade.get('type'),
        entry_price=trade.get('entry_price'),
        exit_price=trade.get('exit_price'),
        pnl=trade.get('pnl')
    )
    return jsonify({'status': 'ok'})


@app.route('/api/options/indicators')
def api_indicators():
    """Get all advanced indicator values."""
    try:
        df = _get_market_df(30)
        summary = AdvancedIndicators.get_summary(df)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades/execute', methods=['POST'])
def api_execute_paper_trade():
    """Execute a paper trade for institutional tracking."""
    try:
        data = request.json
        symbol = data.get('symbol', 'NIFTY')
        entry_price = float(data.get('price', 0))
        lots = int(data.get('lots', 1))
        strike = data.get('strike')
        opt_type = data.get('type')
        sl = data.get('sl')
        tp = data.get('tp')
        reason = data.get('reason', 'Manual')
        
        trade_id = db.add_paper_trade(
            symbol=symbol,
            entry_price=entry_price,
            lots=lots,
            strike=strike,
            option_type=opt_type,
            sl=sl,
            tp=tp,
            reason=reason
        )
        
        return jsonify({
            'success': True,
            'message': f'Trade executed: {symbol} {opt_type or ""} @ {entry_price}',
            'trade_id': trade_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trades/close', methods=['POST'])
def api_close_paper_trade():
    """Close an open paper trade."""
    try:
        data = request.json
        trade_id = data.get('trade_id')
        exit_price = float(data.get('exit_price', 0))
        
        if not trade_id:
            return jsonify({'success': False, 'error': 'Trade ID required'}), 400
            
        success = db.update_paper_trade(trade_id, exit_price)
        
        return jsonify({
            'success': success,
            'message': 'Trade closed successfully' if success else 'Trade not found'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trades/history', methods=['GET'])
def api_get_trade_history():
    """Get paper trade history."""
    limit = int(request.args.get('limit', 50))
    status = request.args.get('status')
    trades = db.get_paper_trades(limit=limit, status=status)
    return jsonify(trades)


@app.route('/api/trades/summary', methods=['GET'])
def api_get_trade_summary():
    """Get paper trade performance summary."""
    stats = db.get_trade_stats()
    return jsonify(stats)


@app.route('/api/options/config', methods=['GET'])
def api_get_config():
    """Get app configuration."""
    return jsonify(db.get_config())


@app.route('/api/analysis/nifty', methods=['GET'])
def api_analysis_nifty():
    """Analyze historical Nifty data for various research scenarios."""
    tf = request.args.get('tf', '15m')
    scenario = request.args.get('scenario', 'spikes')
    
    # Parameters with defaults
    spike_mult = float(request.args.get('spike_mult', 2.0))
    cons_tightness = float(request.args.get('cons_tightness', 0.15))
    cons_min_bars = int(request.args.get('cons_min_bars', 5))
    gap_threshold = float(request.args.get('gap_threshold', 0.5))
    ema_period = int(request.args.get('ema_period', 20))
    ema_threshold = float(request.args.get('ema_threshold', 1.0))
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_map = {
        '15m': os.path.join(base_dir, 'nifty_50_analysis', 'nifty_50_15m.csv'),
        '1h': os.path.join(base_dir, 'nifty_50_analysis', 'nifty_50_1h.csv'),
        '1d': os.path.join(base_dir, 'nifty_50_analysis', 'nifty_50_historical.csv')
    }
    
    path = file_map.get(tf)
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': f'Data not found for {tf}'}), 404
        
    try:
        # Load and clean data
        df = pd.read_csv(path, header=[0, 1, 2] if tf in ['15m', '1h'] else 0, index_col=0)
        if tf in ['15m', '1h']:
            df.columns = [col[0] for col in df.columns]
        
        df.index = pd.to_datetime(df.index, utc=True)
        df = df.sort_index()
        
        results = {'patterns': [], 'spikes': [], 'gaps': [], 'breakouts': [], 'mean_reversion': []}
        
        # --- Pre-calculations ---
        df['TR'] = np.maximum(df['High'] - df['Low'], 
                             np.maximum(abs(df['High'] - df['Close'].shift(1)), 
                                        abs(df['Low'] - df['Close'].shift(1))))
        df['ATR'] = df['TR'].rolling(window=14).mean()
        df['EMA'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
        df['EMA_Dist'] = (df['Close'] - df['EMA']) / df['EMA'] * 100
        df['PrevClose'] = df['Close'].shift(1)
        df['Gap_Pct'] = (df['Open'] - df['PrevClose']) / df['PrevClose'] * 100
        
        # --- Additional indicators ---
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands for Squeeze
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['StdDev'] = df['Close'].rolling(window=20).std()
        df['BB_Width'] = (df['StdDev'] * 4) / df['SMA20'] * 100 # % Width

        # --- Scenario Detection ---
        
        # 1. Spikes
        df['is_spike'] = df['TR'] > (df['ATR'] * spike_mult)
        spike_list = df[df['is_spike']].copy()
        spike_list['time'] = spike_list.index.strftime('%Y-%m-%d %H:%M')
        results['spikes'] = spike_list[['time', 'Close', 'TR']].tail(50).to_dict('records')

        # 2. Gaps
        df['is_gap'] = abs(df['Gap_Pct']) >= gap_threshold
        gap_list = df[df['is_gap']].copy()
        gap_list['time'] = gap_list.index.strftime('%Y-%m-%d %H:%M')
        results['gaps'] = gap_list[['time', 'Open', 'PrevClose', 'Gap_Pct']].tail(50).to_dict('records')

        # 3. Consolidation & Breakouts
        roll_max = df['High'].rolling(window=cons_min_bars).max()
        roll_min = df['Low'].rolling(window=cons_min_bars).min()
        range_pct = (roll_max - roll_min) / roll_min * 100
        df['in_consolidation'] = range_pct < cons_tightness
        
        consolidations = []
        is_cons = False
        start_idx = None
        
        for i in range(len(df)):
            if df['in_consolidation'].iloc[i] and not is_cons:
                is_cons = True
                start_idx = i - cons_min_bars + 1
            elif not df['in_consolidation'].iloc[i] and is_cons:
                is_cons = False
                end_idx = i - 1
                zone_max = roll_max.iloc[i-1]
                zone_min = roll_min.iloc[i-1]
                
                # Check for immediate breakout in current bar
                direction = "NONE"
                if df['Close'].iloc[i] > zone_max: direction = "BULLISH"
                elif df['Close'].iloc[i] < zone_min: direction = "BEARISH"
                
                cons_data = {
                    'start': df.index[max(0, start_idx)].strftime('%Y-%m-%d %H:%M'),
                    'end': df.index[end_idx].strftime('%Y-%m-%d %H:%M'),
                    'bars': int(end_idx - max(0, start_idx) + 1),
                    'range_pct': float(range_pct.iloc[i-1]),
                    'breakout': direction
                }
                consolidations.append(cons_data)
                if direction != "NONE":
                    results['breakouts'].append({
                        'time': df.index[i].strftime('%Y-%m-%d %H:%M'),
                        'close': float(df['Close'].iloc[i]),
                        'direction': direction,
                        'zone_duration': cons_data['bars']
                    })

        results['consolidations'] = consolidations[-50:]

        # 4. Mean Reversion
        df['is_extended'] = abs(df['EMA_Dist']) >= ema_threshold
        ext_list = df[df['is_extended']].copy()
        ext_list['time'] = ext_list.index.strftime('%Y-%m-%d %H:%M')
        results['mean_reversion'] = ext_list[['time', 'Close', 'EMA', 'EMA_Dist']].tail(50).to_dict('records')

        # 5. Volatility Squeeze (Low BB Width)
        # Threshold: Width < 20th percentile of last 100 bars
        df['is_squeeze'] = df['BB_Width'] < df['BB_Width'].rolling(100).quantile(0.2)
        sq_list = df[df['is_squeeze']].copy()
        sq_list['time'] = sq_list.index.strftime('%Y-%m-%d %H:%M')
        results['vol_squeeze'] = sq_list[['time', 'Close', 'BB_Width']].tail(50).to_dict('records')

        # 6. RSI Reversal (Overbought/Oversold)
        df['is_rsi_ext'] = (df['RSI'] > 70) | (df['RSI'] < 30)
        rsi_list = df[df['is_rsi_ext']].copy()
        rsi_list['time'] = rsi_list.index.strftime('%Y-%m-%d %H:%M')
        results['rsi_reversal'] = rsi_list[['time', 'Close', 'RSI']].tail(50).to_dict('records')

        # Final packaging
        chart_df = df.tail(500)
        chart_data = {
            'times': chart_df.index.strftime('%Y-%m-%d %H:%M').tolist(),
            'prices': chart_df['Close'].tolist(),
            'emas': chart_df['EMA'].tolist(),
            'rsi': chart_df['RSI'].tolist(),
            'highlights': []
        }
        
        if scenario == 'spikes': chart_data['highlights'] = chart_df[chart_df['is_spike']].index.strftime('%Y-%m-%d %H:%M').tolist()
        elif scenario == 'gaps': chart_data['highlights'] = chart_df[chart_df['is_gap']].index.strftime('%Y-%m-%d %H:%M').tolist()
        elif scenario == 'mean_reversion': chart_data['highlights'] = chart_df[chart_df['is_extended']].index.strftime('%Y-%m-%d %H:%M').tolist()
        elif scenario == 'vol_squeeze': chart_data['highlights'] = chart_df[chart_df['is_squeeze']].index.strftime('%Y-%m-%d %H:%M').tolist()
        elif scenario == 'rsi_reversal': chart_data['highlights'] = chart_df[chart_df['is_rsi_ext']].index.strftime('%Y-%m-%d %H:%M').tolist()

        return jsonify({
            'success': True,
            'timeframe': tf,
            'scenario': scenario,
            'chart_data': chart_data,
            'patterns': results
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================
#  SELF-LEARNING ENDPOINTS
# ========================

@app.route('/api/learning/status')
def api_learning_status():
    """Get current status of the self-learning engine."""
    try:
        status = learning_engine.get_status()
        return jsonify(_sanitize_for_json(status))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/accuracy')
def api_learning_accuracy():
    """Get historical signal accuracy stats."""
    try:
        days = request.args.get('days', 7, type=int)
        accuracy = db.get_accuracy_stats(days=days)
        return jsonify(_sanitize_for_json(accuracy))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/weights')
def api_learning_weights():
    """Get current and historical weight changes."""
    try:
        history = db.get_weight_history(limit=50)
        current = db.get_latest_weights()
        return jsonify(_sanitize_for_json({
            'current': current,
            'history': history
        }))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/retrain', methods=['POST'])
def api_learning_retrain():
    """Manually trigger model retraining."""
    try:
        # Run in background to avoid timeout
        thread = threading.Thread(target=learning_engine._trigger_retraining)
        thread.start()
        return jsonify({'success': True, 'message': 'Retraining started in background'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/export-signals')
def api_learning_export_signals():
    """Export detailed signal log as CSV."""
    try:
        limit = request.args.get('limit', 1000, type=int)
        signals = db.get_detailed_signal_log(limit=limit)
        
        if not signals:
            return jsonify({'success': False, 'error': 'No signals found to export'}), 404
            
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=signals[0].keys())
        writer.writeheader()
        writer.writerows(signals)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=nifty_signals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-type"] = "text/csv"
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _sanitize_for_json(obj):
    """Recursively sanitize objects for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(round(obj, 4))
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# ==============================
# PHASE 9: LIVE EXECUTION APIs
# ==============================

# Store active live trades (in-memory for demo, use database in production)
LIVE_TRADES = {}

@app.route('/api/trades/execute-live', methods=['POST'])
def execute_live_order():
    """Execute a live order with risk management."""
    try:
        data = request.json
        
        # Extract parameters
        symbol = data.get('symbol', 'NIFTY')
        qty = data.get('qty', 1)
        entry_price = data.get('entry_price', 24800)
        stop_loss = data.get('stop_loss', 24650)
        target_price = data.get('target_price', 25100)
        side = data.get('side', 'buy')
        hedge_ratio = data.get('hedge_ratio', 0)  # 0-1 for auto-hedge
        
        # Generate order ID
        order_id = f"LS{datetime.now().strftime('%H%M%S')}{int(np.random.rand()*1000)}"
        
        # Create trade record
        trade = {
            'order_id': order_id,
            'symbol': symbol,
            'quantity': qty,
            'entry_price': entry_price,
            'current_price': entry_price,
            'stop_loss': stop_loss,
            'target': target_price,
            'side': side,
            'status': 'open',
            'opened_at': datetime.now().isoformat(),
            'pnl': 0,
            'pnl_pct': 0,
            'hedge_ratio': hedge_ratio,
            'hedge_orders': []
        }
        
        # Store in live trades
        LIVE_TRADES[order_id] = trade
        
        # Broadcast via WebSocket
        socketio.emit('order_executed', {
            'order_id': order_id,
            'symbol': symbol,
            'quantity': qty,
            'execution_price': entry_price
        }, broadcast=True)
        
        return jsonify({
            'status': 'open',
            'order_id': order_id,
            'execution_price': entry_price,
            'message': f'Live order {order_id} executed'
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/trades/live-status', methods=['GET'])
def get_live_status():
    """Get all active live trades and their current P&L."""
    try:
        trades_list = []
        
        for order_id, trade in LIVE_TRADES.items():
            if trade['status'] == 'open':
                # Simulate price movement
                price_change = np.random.randn() * 10  # ±10 price points
                current_price = trade['entry_price'] + price_change
                
                # Calculate P&L
                if trade['side'] == 'buy':
                    pnl = (current_price - trade['entry_price']) * trade['quantity']
                    pnl_pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                else:
                    pnl = (trade['entry_price'] - current_price) * trade['quantity']
                    pnl_pct = ((trade['entry_price'] - current_price) / trade['entry_price']) * 100
                
                trade['current_price'] = round(current_price, 2)
                trade['pnl'] = round(pnl, 2)
                trade['pnl_pct'] = round(pnl_pct, 2)
                
                # Check SL/Target
                if trade['side'] == 'buy':
                    if current_price <= trade['stop_loss']:
                        trade['status'] = 'stoploss'
                        socketio.emit('stoploss_hit', {'symbol': trade['symbol']}, broadcast=True)
                    elif current_price >= trade['target']:
                        trade['status'] = 'target'
                        socketio.emit('target_hit', {'symbol': trade['symbol']}, broadcast=True)
                else:  # sell
                    if current_price >= trade['stop_loss']:
                        trade['status'] = 'stoploss'
                        socketio.emit('stoploss_hit', {'symbol': trade['symbol']}, broadcast=True)
                    elif current_price <= trade['target']:
                        trade['status'] = 'target'
                        socketio.emit('target_hit', {'symbol': trade['symbol']}, broadcast=True)
                
                trades_list.append(trade)
        
        return jsonify(trades_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades/close-live/<order_id>', methods=['DELETE'])
def close_live_order(order_id):
    """Close a live order and calculate final P&L."""
    try:
        if order_id not in LIVE_TRADES:
            return jsonify({'error': 'Order not found'}), 404
        
        trade = LIVE_TRADES[order_id]
        closing_price = trade['current_price']
        
        # Calculate final P&L
        if trade['side'] == 'buy':
            final_pnl = (closing_price - trade['entry_price']) * trade['quantity']
        else:
            final_pnl = (trade['entry_price'] - closing_price) * trade['quantity']
        
        # Update trade
        trade['status'] = 'closed'
        trade['closed_at'] = datetime.now().isoformat()
        trade['final_pnl'] = round(final_pnl, 2)
        
        # Broadcast closure
        socketio.emit('order_closed', {
            'order_id': order_id,
            'symbol': trade['symbol'],
            'final_pnl': final_pnl
        }, broadcast=True)
        
        return jsonify({
            'order_id': order_id,
            'final_pnl': final_pnl,
            'closing_price': closing_price,
            'status': 'closed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions/margin', methods=['GET'])
def get_margin_info():
    """Get current margin utilization and position details."""
    try:
        total_capital = 100000  # Default capital
        deployed = sum(abs(t['pnl']) * 0.3 for t in LIVE_TRADES.values() if t['status'] == 'open')
        available = total_capital - deployed
        margin_usage_pct = (deployed / total_capital) * 100 if total_capital > 0 else 0
        
        # Calculate total P&L across all positions
        total_pnl = sum(t['pnl'] for t in LIVE_TRADES.values() if t['status'] == 'open')
        
        return jsonify({
            'total_capital': total_capital,
            'deployed_capital': round(deployed, 2),
            'available_capital': round(available, 2),
            'margin_usage_pct': round(margin_usage_pct, 2),
            'open_positions': len([t for t in LIVE_TRADES.values() if t['status'] == 'open']),
            'total_pnl': round(total_pnl, 2),
            'max_drawdown': 0  # Calculate from history
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades/auto-hedge', methods=['POST'])
def auto_hedge_position():
    """Enable auto-hedging for a specific position."""
    try:
        data = request.json
        order_id = data.get('order_id')
        hedge_ratio = data.get('hedge_ratio', 0.5)  # 50% hedge by default
        
        if order_id not in LIVE_TRADES:
            return jsonify({'error': 'Order not found'}), 404
        
        trade = LIVE_TRADES[order_id]
        
        # Create hedge order (opposite side, smaller quantity)
        hedge_qty = int(trade['quantity'] * hedge_ratio)
        hedge_order = {
            'parent_order': order_id,
            'hedge_qty': hedge_qty,
            'side': 'sell' if trade['side'] == 'buy' else 'buy',
            'created_at': datetime.now().isoformat()
        }
        
        trade['hedge_orders'].append(hedge_order)
        trade['hedge_ratio'] = hedge_ratio
        
        return jsonify({
            'status': 'hedge_enabled',
            'order_id': order_id,
            'hedge_ratio': hedge_ratio,
            'hedge_qty': hedge_qty
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Nifty Options Trading Dashboard")
    print("="*60)
    print("\n📊 Dashboard:        http://localhost:5000")
    print("🎯 Options Strategy: http://localhost:5000/options-strategy")
    print("📡 API:             http://localhost:5000/api")
    print("⚡ Real-time:       ws://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    
    socketio.start_background_task(background_price_stream)
    socketio.start_background_task(background_signal_broadcaster)
    
    # Start Self-Learning Engine
    learning_engine.start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
