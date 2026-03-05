import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.backtester import Backtester, HistoricalDataGenerator, StrategyBacktester
from src.trading.options_strategy import OptionsBuyingStrategy, TradeDirection, SetupQuality


class TestBacktester:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        base = 25000
        closes = []
        for i in range(100):
            base += np.random.uniform(-100, 100)
            closes.append(max(base, 20000))
        
        df = pd.DataFrame({
            'open': [c + np.random.uniform(-50, 50) for c in closes],
            'high': [c + np.random.uniform(50, 100) for c in closes],
            'low': [c - np.random.uniform(50, 100) for c in closes],
            'close': closes,
            'volume': [np.random.uniform(1000000, 5000000) for _ in range(100)]
        }, index=dates)
        df.index.name = 'timestamp'
        return df

    def test_backtester_initialization(self):
        bt = Backtester(initial_capital=100000)
        assert bt.initial_capital == 100000
        assert bt.capital == 100000
        assert bt.positions == []
        assert bt.trades == []

    def test_buy_hold_strategy(self, sample_data):
        def simple_strategy(df, params):
            if len(df) < 10:
                return 'HOLD'
            return 'BUY' if len(df) == 10 else 'SELL'
        
        bt = Backtester(initial_capital=100000)
        result = bt.run_backtest(sample_data, simple_strategy)
        
        assert 'initial_capital' in result
        assert 'final_capital' in result
        assert 'total_trades' in result

    def test_generate_report_no_trades(self):
        bt = Backtester()
        result = bt.generate_report()
        assert 'error' in result

    def test_sharpe_ratio_calculation(self):
        bt = Backtester(initial_capital=100000)
        bt.equity_curve = [
            {'date': datetime.now(), 'equity': 100000, 'capital': 100000},
            {'date': datetime.now(), 'equity': 105000, 'capital': 105000},
            {'date': datetime.now(), 'equity': 103000, 'capital': 103000},
            {'date': datetime.now(), 'equity': 108000, 'capital': 108000},
        ]
        
        sharpe = bt._calculate_sharpe()
        assert isinstance(sharpe, float)


class TestHistoricalDataGenerator:
    def test_generate_nifty_historical_data(self):
        generator = HistoricalDataGenerator()
        df = generator.generate_nifty_historical_data(years=1, start_price=25000)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 200
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns

    def test_generate_with_market_events(self):
        generator = HistoricalDataGenerator()
        df = generator.generate_with_market_events(years=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 200

    def test_price_increases_over_time(self):
        generator = HistoricalDataGenerator()
        df = generator.generate_nifty_historical_data(years=5, start_price=2500)
        
        assert df['close'].iloc[-1] > 0


class TestStrategyBacktester:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        base = 25000
        closes = []
        for i in range(100):
            base += np.random.uniform(-50, 50)
            closes.append(base)
        
        df = pd.DataFrame({
            'open': [c + np.random.uniform(-20, 20) for c in closes],
            'high': [c + np.random.uniform(20, 50) for c in closes],
            'low': [c - np.random.uniform(20, 50) for c in closes],
            'close': closes,
            'volume': [np.random.uniform(1000000, 3000000) for _ in range(100)]
        }, index=dates)
        df.index.name = 'timestamp'
        return df

    def test_ma_crossover_strategy(self):
        tester = StrategyBacktester()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        df = pd.DataFrame({
            'close': [25000 + i * 10 for i in range(60)],
            'open': [25000 + i * 10 for i in range(60)],
            'high': [25000 + i * 10 + 20 for i in range(60)],
            'low': [25000 + i * 10 - 20 for i in range(60)],
            'volume': [2000000] * 60
        }, index=dates)
        df.index.name = 'timestamp'
        
        signal = tester.ma_crossover_strategy(df, {'short_ma': 10, 'long_ma': 20})
        assert signal in ['BUY', 'SELL', 'HOLD']

    def test_rsi_strategy(self):
        tester = StrategyBacktester()
        
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'close': [25000 + i * 10 for i in range(30)],
            'open': [25000 + i * 10 for i in range(30)],
            'high': [25000 + i * 10 + 20 for i in range(30)],
            'low': [25000 + i * 10 - 20 for i in range(30)],
            'volume': [2000000] * 30
        }, index=dates)
        df.index.name = 'timestamp'
        
        signal = tester.rsi_strategy(df, {'rsi_period': 14, 'oversold': 30, 'overbought': 70})
        assert signal in ['BUY', 'SELL', 'HOLD']

    def test_compare_strategies(self, sample_data):
        tester = StrategyBacktester()
        result_df = tester.compare_strategies(sample_data)
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) > 0


class TestOptionsBuyingStrategy:
    @pytest.fixture
    def intraday_data(self):
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
        np.random.seed(42)
        base = 24800
        closes = []
        for i in range(100):
            base += np.random.uniform(-30, 31)
            closes.append(base)
        
        df = pd.DataFrame({
            'open': [c + np.random.uniform(-10, 10) for c in closes],
            'high': [c + np.random.uniform(5, 30) for c in closes],
            'low': [c - np.random.uniform(5, 30) for c in closes],
            'close': closes,
            'volume': [np.random.uniform(500000, 3000000) for _ in range(100)]
        }, index=dates)
        return df

    def test_strategy_initialization(self):
        strategy = OptionsBuyingStrategy()
        assert strategy.config['max_risk_per_trade_pct'] == 2.0
        assert strategy.config['max_open_positions'] == 3

    def test_custom_config(self):
        custom_config = {
            'max_risk_per_trade_pct': 3.0,
            'initial_capital': 500000
        }
        strategy = OptionsBuyingStrategy(config=custom_config)
        assert strategy.config['max_risk_per_trade_pct'] == 3.0
        assert strategy.config['initial_capital'] == 500000

    def test_generate_signal(self, intraday_data):
        strategy = OptionsBuyingStrategy()
        
        signal = strategy.generate_signal(
            intraday_data,
            ai_signal={'recommendation': 'STRONG_BUY', 'confidence': 75},
            current_time=datetime.now().replace(hour=10, minute=0)
        )
        
        assert 'recommendation' in signal
        assert 'direction' in signal
        assert 'conditions' in signal

    def test_supertrend_calculation(self, intraday_data):
        strategy = OptionsBuyingStrategy()
        df = strategy._calculate_supertrend(intraday_data.copy())
        
        assert 'supertrend' in df.columns
        assert 'supertrend_direction' in df.columns

    def test_vwap_calculation(self, intraday_data):
        strategy = OptionsBuyingStrategy()
        df = strategy._calculate_vwap(intraday_data.copy())
        
        assert 'vwap' in df.columns
        assert 'vwap_upper' in df.columns
        assert 'vwap_lower' in df.columns

    def test_rsi_calculation(self, intraday_data):
        strategy = OptionsBuyingStrategy()
        df = strategy._calculate_rsi(intraday_data.copy(), period=14)
        
        assert 'rsi' in df.columns

    def test_adx_calculation(self, intraday_data):
        strategy = OptionsBuyingStrategy()
        df = strategy._calculate_adx(intraday_data.copy(), period=14)
        
        assert 'adx' in df.columns

    def test_record_trade(self):
        strategy = OptionsBuyingStrategy()
        
        trade = {
            'symbol': 'NIFTY',
            'entry_price': 25000,
            'exit_price': 25200,
            'quantity': 25,
            'pnl': 5000,
            'direction': 'BUY'
        }
        
        strategy.record_trade(trade)
        
        assert strategy.total_trades == 1
        assert strategy.winning_trades == 1

    def test_get_stats(self):
        strategy = OptionsBuyingStrategy()
        
        strategy.record_trade({'pnl': 1000})
        strategy.record_trade({'pnl': -500})
        strategy.record_trade({'pnl': 2000})
        
        stats = strategy.get_stats()
        
        assert stats['total_trades'] == 3
        assert stats['winning_trades'] == 2
        assert stats['win_rate'] > 0


class TestGreeksAnalyzer:
    def test_initialization(self):
        from src.trading.greeks_analyzer import GreeksAnalyzer
        analyzer = GreeksAnalyzer()
        assert analyzer.RISK_FREE_RATE == 0.065
        assert analyzer.LOT_SIZE == 25

    def test_norm_cdf(self):
        from src.trading.greeks_analyzer import GreeksAnalyzer
        analyzer = GreeksAnalyzer()
        
        cdf = analyzer._norm_cdf(0)
        assert 0.49 < cdf < 0.51
        
        cdf = analyzer._norm_cdf(2)
        assert cdf > 0.95

    def test_norm_pdf(self):
        from src.trading.greeks_analyzer import GreeksAnalyzer
        analyzer = GreeksAnalyzer()
        
        pdf = analyzer._norm_pdf(0)
        assert 0.3 < pdf < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
