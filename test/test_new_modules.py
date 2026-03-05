"""
Comprehensive Test Suite for New Modules
=========================================
Tests all newly implemented modules for functionality and integration.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_live_order_executor():
    """Test live order executor functionality."""
    from utils.live_order_executor import LiveOrderExecutor, OrderTracker

    # Mock SmartAPI
    with patch('smartapi_python.SmartConnect') as mock_smartapi:
        mock_instance = Mock()
        mock_smartapi.return_value = mock_instance

        executor = LiveOrderExecutor(
            api_key="test_key",
            client_code="test_client",
            password="test_pass",
            totp_secret="test_totp"
        )

        # Test order placement
        order = executor.place_live_order(
            symbol="NIFTY",
            quantity=1,
            entry_price=24800,
            stop_loss=24650,
            target=25100
        )

        assert order is not None
        assert 'order_id' in order
        print("✅ Live Order Executor test passed")

def test_regime_classifier():
    """Test market regime classifier."""
    from utils.ml.regime_classifier import RegimeClassifier

    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'close': np.random.uniform(24000, 25000, 100),
        'high': np.random.uniform(24100, 25100, 100),
        'low': np.random.uniform(23900, 24900, 100),
        'volume': np.random.uniform(1000000, 5000000, 100)
    })

    classifier = RegimeClassifier()
    classifier.fit(data)

    result = classifier.predict(data)
    assert 'regime' in result
    assert 'confidence' in result
    assert result['regime'] in ['BULLISH', 'BEARISH', 'SIDEWAYS']
    print("✅ Regime Classifier test passed")

def test_deep_price_predictor():
    """Test deep price predictor."""
    from utils.ml.deep_price_predictor import LSTMPredictor

    # Create sample data
    data = pd.DataFrame({
        'close': np.sin(np.linspace(0, 4*np.pi, 200)) * 1000 + 24000
    })

    predictor = LSTMPredictor()
    predictor.fit(data)

    forecast = predictor.predict_next()
    assert len(forecast) > 0
    assert 'forecast' in forecast[0]
    print("✅ Deep Price Predictor test passed")

def test_telegram_bot():
    """Test Telegram bot functionality."""
    from utils.telegram_bot import TradingTelegramBot

    with patch('telegram.ext.Application') as mock_app:
        bot = TradingTelegramBot(token="test_token", chat_id="123456")

        # Test alert sending
        result = bot.send_alert("Test message", alert_type="info")
        assert result is True
        print("✅ Telegram Bot test passed")

def test_discord_bot():
    """Test Discord bot functionality."""
    from utils.discord_bot import TradingDiscordBot

    with patch('discord.ext.commands.Bot') as mock_bot:
        bot = TradingDiscordBot(token="test_token")

        # Test embed creation
        embed = bot.create_portfolio_embed({
            'capital': 100000,
            'pnl': 2500,
            'positions': []
        })
        assert embed is not None
        print("✅ Discord Bot test passed")

def test_monte_carlo_simulator():
    """Test Monte Carlo simulator."""
    from utils.monte_carlo_simulator import MonteCarloSimulator

    simulator = MonteCarloSimulator()

    # Generate sample returns
    returns = np.random.normal(0.001, 0.02, 252)  # 1 year of daily returns

    paths = simulator.generate_paths(returns, 100, 30)  # 100 paths, 30 days
    assert paths.shape[0] == 100
    assert paths.shape[1] == 30

    var_result = simulator.calculate_var_cvar(returns)
    assert 'VaR_95' in var_result
    assert 'CVaR_95' in var_result
    print("✅ Monte Carlo Simulator test passed")

def test_stress_tester():
    """Test stress tester."""
    from utils.stress_tester import StressTester

    tester = StressTester()

    # Sample portfolio
    portfolio = {
        'NIFTY': {'quantity': 1, 'price': 24800},
        'BANKNIFTY': {'quantity': 1, 'price': 48000}
    }

    results = tester.run_all_stress_tests(portfolio)

    assert len(results) == 5  # 5 stress scenarios
    for scenario_name, result in results.items():
        assert 'initial_value' in result
        assert 'final_value' in result
        assert 'max_loss' in result

    print("✅ Stress Tester test passed")

def test_tradingview_integration():
    """Test TradingView webhook integration."""
    from src.web.tradingview_integration import TradingViewWebhookHandler

    handler = TradingViewWebhookHandler()

    # Test signal parsing
    webhook_data = {
        'symbol': 'NIFTY',
        'signal': 'BUY',
        'entry': 24800,
        'tp': 25100,
        'sl': 24650
    }

    signal = handler.parse_webhook(webhook_data)
    assert signal.symbol == 'NIFTY'
    assert signal.signal_type == 'BUY'
    assert signal.entry_price == 24800

    print("✅ TradingView Integration test passed")

def test_threecommas_integration():
    """Test 3Commas integration."""
    from src.web.threecommas_integration import ThreeCommasAPI

    with patch('requests.request') as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {'id': '12345'}
        mock_request.return_value = mock_response

        api = ThreeCommasAPI(api_key="test_key", api_secret="test_secret")

        result = api.create_smart_trade({
            'pair': 'USDT_BTC',
            'position': {'type': 'buy'},
            'take_profit': {'price': 50000}
        })

        assert result['id'] == '12345'
        print("✅ 3Commas Integration test passed")

def test_multi_broker_adapter():
    """Test multi-broker adapter."""
    from src.web.multi_broker_adapter import MultiBrokerAdapter, AngelOneBroker

    adapter = MultiBrokerAdapter()

    # Mock broker
    mock_broker = Mock(spec=AngelOneBroker)
    mock_broker.connect.return_value = True
    mock_broker.get_account_info.return_value = {
        'balance': 100000,
        'margin': 50000
    }

    adapter.register_broker('angel_one', mock_broker)
    success = adapter.connect_all_brokers()

    assert success == [True]
    assert len(adapter.get_all_accounts()) == 1

    print("✅ Multi-Broker Adapter test passed")

def test_api_v2():
    """Test API v2 functionality."""
    from src.web.api_v2 import TradingAPIv2
    from flask import Flask

    app = Flask(__name__)
    api = TradingAPIv2(app)

    # Test API initialization
    assert api.api is not None
    assert api.app == app

    print("✅ API v2 test passed")

if __name__ == "__main__":
    print("🧪 Running comprehensive test suite for new modules...")
    print("=" * 60)

    test_functions = [
        test_live_order_executor,
        test_regime_classifier,
        test_deep_price_predictor,
        test_telegram_bot,
        test_discord_bot,
        test_monte_carlo_simulator,
        test_stress_tester,
        test_tradingview_integration,
        test_threecommas_integration,
        test_multi_broker_adapter,
        test_api_v2
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! System is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")