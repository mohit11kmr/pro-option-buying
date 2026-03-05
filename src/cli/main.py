"""
CLI Interface for Nifty Options Trading Toolkit
===============================================
Command-line interface for running backtests, generating signals, and managing the trading system.
"""

import argparse
import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.backtester import Backtester, HistoricalDataGenerator, StrategyBacktester
from src.utils.ml.signal_generator import AISignalGenerator, RiskAdjustedSignalGenerator
from src.trading.options_strategy import OptionsBuyingStrategy
from src.utils.paper_trading import PaperTradingEngine, OrderSide, OrderType


class ConfigManager:
    """Configuration manager supporting YAML, TOML, and ENV files."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config: Dict[str, Any] = {}
        self.config_path = config_path
        
        if config_path:
            self.load_config(config_path)
        else:
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration."""
        self.config = {
            "backtest": {
                "initial_capital": 100000,
                "commission_rate": 0.001,
                "slippage_rate": 0.0005
            },
            "strategy": {
                "name": "ma_crossover",
                "short_ma": 20,
                "long_ma": 50
            },
            "ai": {
                "confidence_threshold": 60,
                "weights": {
                    "price_prediction": 0.25,
                    "pattern_recognition": 0.25,
                    "sentiment": 0.25,
                    "options_flow": 0.25
                }
            },
            "paper_trading": {
                "initial_capital": 100000,
                "latency_ms": 100
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log"
            }
        }
    
    def load_config(self, path: str) -> None:
        """Load configuration from file."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            print(f"Config file not found: {path}, using defaults")
            self._load_default_config()
            return
        
        if path_obj.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    self.config = loaded
        elif path_obj.suffix == '.toml':
            try:
                import tomli
                with open(path, 'rb') as f:
                    self.config = tomli.load(f)
            except ImportError:
                import toml
                with open(path, 'r') as f:
                    self.config = toml.load(f)
        elif path_obj.suffix == '.json':
            with open(path, 'r') as f:
                self.config = json.load(f)
        else:
            print(f"Unsupported config format: {path_obj.suffix}")
            self._load_default_config()
    
    def save_config(self, path: str) -> None:
        """Save configuration to file."""
        path_obj = Path(path)
        
        if path_obj.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        elif path_obj.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
        else:
            print(f"Unsupported config format: {path_obj.suffix}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set config value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value


class CLIRunner:
    """CLI runner for various commands."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def run_backtest(self, args) -> Dict:
        """Run backtest with configured parameters."""
        print("\n" + "="*70)
        print("RUNNING BACKTEST")
        print("="*70)
        
        initial_capital = args.capital or self.config.get('backtest.initial_capital', 100000)
        
        if args.data:
            print(f"Loading data from: {args.data}")
            df = pd.read_csv(args.data, index_col=0, parse_dates=True)
        else:
            print("Generating synthetic data...")
            generator = HistoricalDataGenerator()
            years = args.years or 5
            df = generator.generate_with_market_events(years=years)
            print(f"Generated {len(df)} days of data")
        
        strategy_name = args.strategy or self.config.get('strategy.name', 'ma_crossover')
        strategy_params = {}
        
        if strategy_name == 'ma_crossover':
            strategy_params = {
                'short_ma': args.short_ma or self.config.get('strategy.short_ma', 20),
                'long_ma': args.long_ma or self.config.get('strategy.long_ma', 50)
            }
        elif strategy_name == 'rsi':
            strategy_params = {
                'rsi_period': args.rsi_period or 14,
                'oversold': args.oversold or 30,
                'overbought': args.overbought or 70
            }
        
        print(f"Strategy: {strategy_name}")
        print(f"Parameters: {strategy_params}")
        print(f"Initial Capital: ₹{initial_capital:,}")
        
        tester = StrategyBacktester()
        result = tester.run_strategy_backtest(df, strategy_name, strategy_params)
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            return result
        
        print(f"\n📊 Results:")
        print(f"   Initial Capital: ₹{result['initial_capital']:,.2f}")
        print(f"   Final Capital: ₹{result['final_capital']:,.2f}")
        print(f"   Total PnL: ₹{result['total_pnl']:,.2f}")
        print(f"   Returns: {result['returns_percent']:.2f}%")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Win Rate: {result['win_rate']:.2f}%")
        print(f"   Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        
        if args.output:
            output_data = {
                'config': {
                    'strategy': strategy_name,
                    'params': strategy_params,
                    'initial_capital': initial_capital,
                    'data_points': len(df)
                },
                'result': result
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\n✅ Results saved to: {args.output}")
        
        return result
    
    def compare_strategies(self, args) -> pd.DataFrame:
        """Compare multiple strategies."""
        print("\n" + "="*70)
        print("COMPARING STRATEGIES")
        print("="*70)
        
        if args.data:
            df = pd.read_csv(args.data, index_col=0, parse_dates=True)
        else:
            generator = HistoricalDataGenerator()
            years = args.years or 2
            df = generator.generate_with_market_events(years=years)
        
        tester = StrategyBacktester()
        results_df = tester.compare_strategies(df)
        
        print("\n📊 Strategy Comparison:")
        print(results_df.to_string(index=False))
        
        if args.output:
            results_df.to_csv(args.output, index=False)
            print(f"\n✅ Results saved to: {args.output}")
        
        return results_df
    
    def generate_signal(self, args) -> Dict:
        """Generate AI trading signal."""
        print("\n" + "="*70)
        print("GENERATING AI SIGNAL")
        print("="*70)
        
        if args.data:
            df = pd.read_csv(args.data, index_col=0, parse_dates=True)
        else:
            generator = HistoricalDataGenerator()
            df = generator.generate_nifty_historical_data(years=1)
        
        print(f"Data points: {len(df)}")
        
        risk_adjusted = args.risk_adjusted
        
        if risk_adjusted:
            generator = RiskAdjustedSignalGenerator()
            account_balance = args.account_balance or 100000
            result = generator.generate_signal_with_risk(df, account_balance)
            print(f"\n💰 Risk-Adjusted Signal:")
            print(f"   Position Size: ₹{result.get('position_size', 0):,.2f}")
            print(f"   Stop Loss: ₹{result.get('stop_loss', 0):,.2f}")
            print(f"   Take Profit: ₹{result.get('take_profit', 0):,.2f}")
            print(f"   Risk/Reward: {result.get('risk_reward_ratio', 0):.2f}")
        else:
            generator = AISignalGenerator()
            result = generator.generate_comprehensive_signal(df)
        
        print(f"\n🎯 Signal: {result.get('recommendation')}")
        print(f"   Score: {result.get('score')}")
        print(f"   Confidence: {result.get('confidence')}%")
        print(f"   Verdict: {result.get('verdict')}")
        
        if 'trends' in result:
            print(f"\n📈 Trends:")
            for tf, trend in result['trends'].items():
                print(f"   {tf}: {trend}")
        
        print(f"\n📝 Reasons:")
        for reason in result.get('reasons', []):
            print(f"   - {reason}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n✅ Signal saved to: {args.output}")
        
        return result
    
    def run_paper_trading(self, args) -> None:
        """Run paper trading session."""
        print("\n" + "="*70)
        print("PAPER TRADING SESSION")
        print("="*70)
        
        initial_capital = args.capital or self.config.get('paper_trading.initial_capital', 100000)
        latency = args.latency or self.config.get('paper_trading.latency_ms', 100)
        
        engine = PaperTradingEngine(initial_capital=initial_capital, latency_ms=latency)
        
        print(f"Initial Capital: ₹{initial_capital:,}")
        print(f"Simulated Latency: {latency}ms")
        
        if args.interactive:
            print("\n📝 Interactive Paper Trading Mode")
            print("Commands: buy <qty> <price>, sell <qty> <price>, status, quit")
            
            while True:
                try:
                    cmd = input("\n> ").strip().lower()
                    
                    if cmd == 'quit' or cmd == 'exit':
                        break
                    elif cmd == 'status':
                        prices = {"NIFTY": 25000}
                        summary = engine.get_portfolio_summary(prices)
                        print(f"Cash: ₹{summary['cash']:,.2f}")
                        print(f"Portfolio: ₹{summary['portfolio_value']:,.2f}")
                        print(f"P&L: ₹{summary['total_pnl']:,.2f}")
                    elif cmd.startswith('buy '):
                        parts = cmd.split()
                        if len(parts) >= 3:
                            qty = int(parts[1])
                            price = float(parts[2])
                            order = engine.place_order("NIFTY", OrderSide.BUY, qty, OrderType.MARKET, price)
                            print(f"BUY order filled: {qty} @ ₹{price}")
                    elif cmd.startswith('sell '):
                        parts = cmd.split()
                        if len(parts) >= 3:
                            qty = int(parts[1])
                            price = float(parts[2])
                            order = engine.place_order("NIFTY", OrderSide.SELL, qty, OrderType.MARKET, price)
                            print(f"SELL order filled: {qty} @ ₹{price}")
                    else:
                        print("Unknown command")
                except KeyboardInterrupt:
                    break
        else:
            print("\nRunning demo trades...")
            engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
            engine.place_order("NIFTY", OrderSide.BUY, 50, OrderType.MARKET, price=25050)
            engine.place_order("NIFTY", OrderSide.SELL, 75, OrderType.MARKET, price=25100)
            
            prices = {"NIFTY": 25100}
            summary = engine.get_portfolio_summary(prices)
            
            print(f"\n📊 Final Portfolio:")
            print(f"   Cash: ₹{summary['cash']:,.2f}")
            print(f"   Positions: {summary['positions']}")
            print(f"   Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
            print(f"   Total P&L: ₹{summary['total_pnl']:,.2f}")
            print(f"   Returns: {summary['returns_percent']:.2f}%")
    
    def generate_data(self, args) -> None:
        """Generate historical data."""
        print("\n" + "="*70)
        print("GENERATING HISTORICAL DATA")
        print("="*70)
        
        generator = HistoricalDataGenerator()
        
        years = args.years or 5
        start_price = args.start_price or 25000
        
        if args.events:
            df = generator.generate_with_market_events(years=years)
            print(f"Generated {len(df)} days with market events")
        else:
            df = generator.generate_nifty_historical_data(years=years, start_price=start_price)
            print(f"Generated {len(df)} days")
        
        print(f"Date Range: {df.index[0]} to {df.index[-1]}")
        print(f"Price Range: ₹{df['close'].min():.2f} to ₹{df['close'].max():.2f}")
        
        output_file = args.output or 'generated_data.csv'
        df.to_csv(output_file)
        print(f"✅ Data saved to: {output_file}")
    
    def show_config(self, args) -> None:
        """Show current configuration."""
        print("\n" + "="*70)
        print("CURRENT CONFIGURATION")
        print("="*70)
        
        print(json.dumps(self.config, indent=2))


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description='Nifty Options Trading Toolkit - CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-c', '--config', type=str, help='Config file path (YAML, TOML, or JSON)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('-d', '--data', type=str, help='Historical data CSV file')
    backtest_parser.add_argument('-s', '--strategy', type=str, choices=['ma_crossover', 'rsi', 'breakout', 'ai_signal'], help='Strategy name')
    backtest_parser.add_argument('--short-ma', type=int, help='Short MA period')
    backtest_parser.add_argument('--long-ma', type=int, help='Long MA period')
    backtest_parser.add_argument('--rsi-period', type=int, help='RSI period')
    backtest_parser.add_argument('--oversold', type=int, help='RSI oversold level')
    backtest_parser.add_argument('--overbought', type=int, help='RSI overbought level')
    backtest_parser.add_argument('--capital', type=float, help='Initial capital')
    backtest_parser.add_argument('--years', type=int, help='Years of data to generate')
    backtest_parser.add_argument('-o', '--output', type=str, help='Output file for results')
    
    compare_parser = subparsers.add_parser('compare', help='Compare strategies')
    compare_parser.add_argument('-d', '--data', type=str, help='Historical data CSV file')
    compare_parser.add_argument('--years', type=int, help='Years of data to generate')
    compare_parser.add_argument('-o', '--output', type=str, help='Output file for results')
    
    signal_parser = subparsers.add_parser('signal', help='Generate AI signal')
    signal_parser.add_argument('-d', '--data', type=str, help='Historical data CSV file')
    signal_parser.add_argument('--risk-adjusted', action='store_true', help='Generate risk-adjusted signal')
    signal_parser.add_argument('--account-balance', type=float, help='Account balance for risk-adjusted signal')
    signal_parser.add_argument('-o', '--output', type=str, help='Output file for signal')
    
    paper_parser = subparsers.add_parser('paper', help='Run paper trading')
    paper_parser.add_argument('--capital', type=float, help='Initial capital')
    paper_parser.add_argument('--latency', type=int, help='Simulated latency in ms')
    paper_parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    data_parser = subparsers.add_parser('generate-data', help='Generate historical data')
    data_parser.add_argument('--years', type=int, default=5, help='Years of data to generate')
    data_parser.add_argument('--start-price', type=float, help='Starting price')
    data_parser.add_argument('--events', action='store_true', help='Include market events')
    data_parser.add_argument('-o', '--output', type=str, help='Output file')
    
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = ConfigManager(args.config)
    runner = CLIRunner(config)
    
    if args.command == 'backtest':
        runner.run_backtest(args)
    elif args.command == 'compare':
        runner.compare_strategies(args)
    elif args.command == 'signal':
        runner.generate_signal(args)
    elif args.command == 'paper':
        runner.run_paper_trading(args)
    elif args.command == 'generate-data':
        runner.generate_data(args)
    elif args.command == 'config':
        runner.show_config(args)
    else:
        print(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
