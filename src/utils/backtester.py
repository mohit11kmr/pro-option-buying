import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import random


class Backtester:
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, df: pd.DataFrame, strategy_func, params: Dict = None) -> Dict:
        """Run backtest on historical data"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        params = params or {}
        
        for i in range(1, len(df)):
            current_bar = df.iloc[i]
            
            signal = strategy_func(df.iloc[:i+1], params)
            
            if signal == 'BUY' and not self.positions:
                position_size = self.capital * 0.95 / current_bar['close']
                self.positions.append({
                    'entry_price': current_bar['close'],
                    'entry_date': current_bar.name,
                    'size': position_size,
                    'type': 'LONG'
                })
                self.trades.append({
                    'date': current_bar.name,
                    'action': 'BUY',
                    'price': current_bar['close'],
                    'capital': self.capital
                })
            
            elif signal == 'SELL' and self.positions:
                for pos in self.positions:
                    pnl = (current_bar['close'] - pos['entry_price']) * pos['size']
                    self.capital += pnl
                    self.trades.append({
                        'date': current_bar.name,
                        'action': 'SELL',
                        'price': current_bar['close'],
                        'pnl': pnl,
                        'capital': self.capital
                    })
                self.positions = []
            
            equity = self.capital
            if self.positions:
                unrealized_pnl = (current_bar['close'] - self.positions[0]['entry_price']) * self.positions[0]['size']
                equity += unrealized_pnl
            
            self.equity_curve.append({
                'date': current_bar.name,
                'equity': equity,
                'capital': self.capital
            })
        
        if self.positions:
            final_bar = df.iloc[-1]
            for pos in self.positions:
                pnl = (final_bar['close'] - pos['entry_price']) * pos['size']
                self.capital += pnl
                self.trades.append({
                    'date': final_bar.name,
                    'action': 'CLOSE',
                    'price': final_bar['close'],
                    'pnl': pnl,
                    'capital': self.capital
                })
            self.positions = []
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        if not self.trades:
            return {'error': 'No trades executed'}
        
        closes = [t['capital'] for t in self.equity_curve]
        peaks = pd.Series(closes).cummax()
        drawdowns = (pd.Series(closes) - peaks) / peaks * 100
        
        winning_trades = [t for t in self.trades if 'pnl' in t and t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trades if 'pnl' in t and t.get('pnl', 0) <= 0]
        
        total_pnl = self.capital - self.initial_capital
        returns = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_pnl': total_pnl,
            'returns_percent': returns,
            'total_trades': len([t for t in self.trades if t['action'] == 'SELL']),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / (len(winning_trades) + len(losing_trades)) * 100 if (winning_trades + losing_trades) else 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': drawdowns.min(),
            'sharpe_ratio': self._calculate_sharpe(),
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def _calculate_sharpe(self, risk_free_rate: float = 0.06) -> float:
        if len(self.equity_curve) < 2:
            return 0
        
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i]['equity'] - self.equity_curve[i-1]['equity']) / self.equity_curve[i-1]['equity']
            returns.append(ret)
        
        if not returns or np.std(returns) == 0:
            return 0
        
        excess_returns = np.mean(returns) - risk_free_rate / 252
        return np.sqrt(252) * excess_returns / np.std(returns)


class HistoricalDataGenerator:
    def __init__(self):
        self.base_price = 25000
        
    def generate_nifty_historical_data(self, years: int = 20, start_price: float = None) -> pd.DataFrame:
        """Generate realistic historical NIFTY 50 data"""
        
        if start_price is None:
            start_price = 2500
        
        total_days = years * 252
        start_date = datetime.now() - timedelta(days=total_days)
        
        dates = pd.date_range(start=start_date, periods=total_days, freq='B')
        
        prices = [start_price]
        trend = 0.0003
        volatility = 0.015
        
        for i in range(len(dates) - 1):
            change = np.random.normal(trend, volatility)
            new_price = prices[-1] * (1 + change)
            
            if i % 252 == 0:
                trend = np.random.normal(0.0002, 0.0002)
                volatility = np.random.uniform(0.012, 0.025)
            
            prices.append(new_price)
        
        data = {
            'open': [],
            'high': [],
            'low': [],
            'close': prices[:-1],
            'volume': []
        }
        
        for close in data['close']:
            daily_range = close * np.random.uniform(0.008, 0.025)
            open_price = close + np.random.uniform(-daily_range/2, daily_range/2)
            high_price = max(open_price, close) + np.random.uniform(0, daily_range/2)
            low_price = min(open_price, close) - np.random.uniform(0, daily_range/2)
            
            data['open'].append(round(open_price, 2))
            data['high'].append(round(high_price, 2))
            data['low'].append(round(low_price, 2))
            data['volume'].append(int(np.random.uniform(2000000, 10000000)))
        
        df = pd.DataFrame(data, index=dates[:-1])
        df.index.name = 'timestamp'
        
        return df
    
    def generate_with_market_events(self, years: int = 20) -> pd.DataFrame:
        """Generate data with realistic market events"""
        
        df = self.generate_nifty_historical_data(years, start_price=2500)
        
        closes = df['close'].values.copy()
        
        crisis_periods = [
            (500, 700, 0.015),  
            (2000, 2100, 0.02),  
        ]
        
        for start, end, impact in crisis_periods:
            if start < len(closes):
                end = min(end, len(closes))
                for i in range(start, end):
                    closes[i] *= (1 - impact / (end - start))
        
        df['close'] = closes
        
        df['high'] = df['close'] * 1.005
        df['low'] = df['close'] * 0.995
        df['open'] = df['close'] * (1 + np.random.uniform(-0.002, 0.002, len(df)))
        
        return df


class StrategyBacktester:
    def __init__(self):
        self.backtester = Backtester()
        
    def ma_crossover_strategy(self, df: pd.DataFrame, params: Dict) -> str:
        """Moving Average Crossover Strategy"""
        short_ma = params.get('short_ma', 20)
        long_ma = params.get('long_ma', 50)
        
        if len(df) < long_ma:
            return 'HOLD'
        
        short = df['close'].rolling(short_ma).mean().iloc[-1]
        long = df['close'].rolling(long_ma).mean().iloc[-1]
        short_prev = df['close'].rolling(short_ma).mean().iloc[-2]
        long_prev = df['close'].rolling(long_ma).mean().iloc[-2]
        
        if short_prev <= long_prev and short > long:
            return 'BUY'
        elif short_prev >= long_prev and short < long:
            return 'SELL'
        
        return 'HOLD'
    
    def rsi_strategy(self, df: pd.DataFrame, params: Dict) -> str:
        """RSI Strategy"""
        rsi_period = params.get('rsi_period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        if len(df) < rsi_period + 1:
            return 'HOLD'
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < oversold:
            return 'BUY'
        elif current_rsi > overbought:
            return 'SELL'
        
        return 'HOLD'
    
    def breakout_strategy(self, df: pd.DataFrame, params: Dict) -> str:
        """Breakout Strategy"""
        lookback = params.get('lookback', 20)
        
        if len(df) < lookback:
            return 'HOLD'
        
        recent_high = df['high'].iloc[-lookback:-1].max()
        recent_low = df['low'].iloc[-lookback:-1].min()
        
        current_close = df['close'].iloc[-1]
        
        if current_close > recent_high:
            return 'BUY'
        elif current_close < recent_low:
            return 'SELL'
        
        return 'HOLD'
    
    def ai_signal_strategy(self, df: pd.DataFrame, params: Dict = None) -> str:
        """AI Signal Based Strategy"""
        from utils.ml import AISignalGenerator
        
        if len(df) < 30:
            return 'HOLD'
        
        try:
            generator = AISignalGenerator()
            signal = generator.generate_comprehensive_signal(df)
            return signal.get('recommendation', 'HOLD')
        except:
            return 'HOLD'
    
    def run_strategy_backtest(self, df: pd.DataFrame, strategy_name: str, params: Dict = None) -> Dict:
        """Run backtest for a specific strategy"""
        
        strategies = {
            'ma_crossover': self.ma_crossover_strategy,
            'rsi': self.rsi_strategy,
            'breakout': self.backtester,
            'ai_signal': self.ai_signal_strategy
        }
        
        if strategy_name not in strategies:
            return {'error': f'Unknown strategy: {strategy_name}'}
        
        if strategy_name == 'breakout':
            return self.backtester.run_backtest(df, self.breakout_strategy, params)
        
        strategy_func = strategies[strategy_name]
        
        return self.backtester.run_backtest(df, strategy_func, params)
    
    def compare_strategies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compare multiple strategies"""
        
        strategies = [
            ('MA_Crossover_20_50', 'ma_crossover', {'short_ma': 20, 'long_ma': 50}),
            ('MA_Crossover_10_30', 'ma_crossover', {'short_ma': 10, 'long_ma': 30}),
            ('RSI_Oversold', 'rsi', {'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
            ('Breakout_20', 'breakout', {'lookback': 20}),
            ('Breakout_10', 'breakout', {'lookback': 10}),
        ]
        
        results = []
        
        for name, strategy, params in strategies:
            print(f"Testing {name}...")
            try:
                result = self.run_strategy_backtest(df, strategy, params)
                results.append({
                    'Strategy': name,
                    'Returns (%)': result.get('returns_percent', 0),
                    'Total Trades': result.get('total_trades', 0),
                    'Win Rate (%)': result.get('win_rate', 0),
                    'Max Drawdown (%)': result.get('max_drawdown', 0),
                    'Sharpe Ratio': result.get('sharpe_ratio', 0),
                    'Profit Factor': result.get('profit_factor', 0)
                })
            except Exception as e:
                print(f"Error: {e}")
        
        return pd.DataFrame(results)


def run_full_backtest():
    print("\n" + "="*70)
    print("📊 NIFTY 50 BACKTESTING SYSTEM")
    print("="*70 + "\n")
    
    print("📈 Generating Historical Data (20 Years)...")
    
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=20)
    
    print(f"✅ Generated {len(df)} days of data")
    print(f"   Date Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"   Starting Price: ₹{df['close'].iloc[0]:.2f}")
    print(f"   Ending Price: ₹{df['close'].iloc[-1]:.2f}")
    
    df.to_csv('nifty_historical_20yr.csv')
    print("   Saved to nifty_historical_20yr.csv\n")
    
    print("="*70)
    print("🤖 Running AI Strategy Backtest")
    print("="*70)
    
    tester = StrategyBacktester()
    
    result = tester.run_strategy_backtest(df, 'ai_signal', {})
    
    if 'error' not in result:
        print(f"\n📊 Results:")
        print(f"   Initial Capital: ₹{result['initial_capital']:,.2f}")
        print(f"   Final Capital: ₹{result['final_capital']:,.2f}")
        print(f"   Total PnL: ₹{result['total_pnl']:,.2f}")
        print(f"   Returns: {result['returns_percent']:.2f}%")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Winning: {result['winning_trades']}")
        print(f"   Losing: {result['losing_trades']}")
        print(f"   Win Rate: {result['win_rate']:.2f}%")
        print(f"   Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    else:
        print(f"Error: {result['error']}")
    
    print("\n" + "="*70)
    print("📊 Comparing Strategies")
    print("="*70)
    
    comparison_df = tester.compare_strategies(df)
    print("\n")
    print(comparison_df.to_string(index=False))
    
    comparison_df.to_csv('backtest_comparison.csv', index=False)
    print("\n✅ Saved to backtest_comparison.csv")
    
    return result, comparison_df


if __name__ == "__main__":
    run_full_backtest()
