import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.ml.signal_generator import AISignalGenerator, RiskAdjustedSignalGenerator
from src.utils.paper_trading import PaperTradingEngine, StructuredLogger, MetricsExporter, OrderSide, OrderType


class TestAISignalGenerator:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        np.random.seed(42)
        base = 25000
        closes = []
        for i in range(60):
            base += np.random.uniform(-100, 100)
            closes.append(base)
        
        df = pd.DataFrame({
            'open': [c + np.random.uniform(-50, 50) for c in closes],
            'high': [c + np.random.uniform(50, 100) for c in closes],
            'low': [c - np.random.uniform(50, 100) for c in closes],
            'close': closes,
            'volume': [np.random.uniform(1000000, 5000000) for _ in range(60)]
        }, index=dates)
        return df

    def test_initialization(self):
        generator = AISignalGenerator()
        assert generator.weights['price_prediction'] == 0.25

    def test_generate_comprehensive_signal(self, sample_data):
        generator = AISignalGenerator()
        result = generator.generate_comprehensive_signal(sample_data)
        
        assert 'recommendation' in result
        assert 'score' in result
        assert 'confidence' in result
        assert 'reasons' in result

    def test_price_prediction_analysis(self, sample_data):
        generator = AISignalGenerator()
        signal = generator._analyze_price_prediction(sample_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'direction' in signal

    def test_signal_history(self, sample_data):
        generator = AISignalGenerator()
        generator.generate_comprehensive_signal(sample_data)
        generator.generate_comprehensive_signal(sample_data)
        
        history = generator.get_signal_history(limit=5)
        assert len(history) == 2

    def test_update_weights(self):
        generator = AISignalGenerator()
        new_weights = {
            'price_prediction': 0.4,
            'pattern_recognition': 0.2,
            'sentiment': 0.2,
            'options_flow': 0.2
        }
        generator.update_weights(new_weights)
        
        assert generator.weights['price_prediction'] == 0.4


class TestRiskAdjustedSignalGenerator:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        base = 25000
        closes = [base + i * 10 for i in range(30)]
        
        df = pd.DataFrame({
            'open': [c + 10 for c in closes],
            'high': [c + 30 for c in closes],
            'low': [c - 30 for c in closes],
            'close': closes,
            'volume': [2000000] * 30
        }, index=dates)
        return df

    def test_initialization(self):
        generator = RiskAdjustedSignalGenerator()
        assert generator.max_position_size == 0.1
        assert generator.max_loss_per_trade == 0.02

    def test_generate_signal_with_risk(self, sample_data):
        generator = RiskAdjustedSignalGenerator()
        result = generator.generate_signal_with_risk(sample_data, account_balance=100000)
        
        assert 'position_size' in result
        assert 'stop_loss' in result
        assert 'take_profit' in result


class TestPaperTradingEngine:
    def test_initialization(self):
        engine = PaperTradingEngine(initial_capital=100000, latency_ms=50)
        assert engine.initial_capital == 100000
        assert engine.cash == 100000

    def test_place_market_order(self):
        engine = PaperTradingEngine(initial_capital=100000)
        order = engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
        
        assert order['status'] == 'FILLED'
        assert order['filled_quantity'] == 100

    def test_place_limit_order(self):
        engine = PaperTradingEngine(initial_capital=100000)
        order = engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.LIMIT, price=25000)
        
        assert order['status'] == 'FILLED'

    def test_position_tracking(self):
        engine = PaperTradingEngine(initial_capital=100000)
        engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
        
        position = engine.get_position("NIFTY")
        assert position['quantity'] == 100
        assert position['avg_price'] > 0

    def test_portfolio_value(self):
        engine = PaperTradingEngine(initial_capital=100000)
        engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
        
        portfolio = engine.get_portfolio_value({"NIFTY": 25100})
        assert portfolio > 0

    def test_order_history(self):
        engine = PaperTradingEngine(initial_capital=100000)
        engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
        
        history = engine.get_order_history()
        assert len(history) == 1

    def test_reset(self):
        engine = PaperTradingEngine(initial_capital=100000)
        engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
        engine.reset()
        
        assert engine.cash == 100000
        assert engine.positions == {}


class TestStructuredLogger:
    def test_initialization(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = StructuredLogger("test", str(log_file))
        assert logger.redact_keys is not None

    def test_log_with_redaction(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = StructuredLogger("test", str(log_file))
        
        logger.info("test_event", api_key="secret123", username="testuser")
        
        assert log_file.exists()

    def test_redact_sensitive_data(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = StructuredLogger("test", str(log_file))
        
        data = {'password': 'secret', 'token': 'abc123', 'normal_field': 'value'}
        redacted = logger._redact(data)
        
        assert redacted['password'] == '***REDACTED***'
        assert redacted['token'] == '***REDACTED***'
        assert redacted['normal_field'] == 'value'


class TestMetricsExporter:
    def test_initialization(self):
        exporter = MetricsExporter.metrics == {}

    def test_record_metric(self):
        exporter = MetricsExporter()
()
        assert exporter        exporter.record("test_metric", 100)
        
        assert "test_metric" in exporter.metrics

    def test_increment_counter(self):
        exporter = MetricsExporter()
        exporter.inc("orders_placed")
        exporter.inc("orders_placed")
        
        metrics = exporter.get_metrics()
        assert "orders_placed_total" in metrics

    def test_gauge(self):
        exporter = MetricsExporter()
        exporter.gauge("cpu_usage", 75.5)
        
        metrics = exporter.get_metrics()
        assert "cpu_usage" in metrics

    def test_timing(self):
        exporter = MetricsExporter()
        exporter.timing("request_duration", 150)
        
        metrics = exporter.get_metrics()
        assert "request_duration_duration_ms" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
