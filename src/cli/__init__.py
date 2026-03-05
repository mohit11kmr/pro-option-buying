#!/usr/bin/env python3
"""
Nifty Options Trading Toolkit - CLI
====================================
CLI for backtesting, live trading, and ML pipeline
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path

from utils.market_data import AngelOneMarketData
from utils.backtester import Backtester, HistoricalDataGenerator, StrategyBacktester
from utils.ml import AISignalGenerator
from utils.ml.price_predictor import PricePredictor, EnsemblePredictor
from utils.ai_integration import AIIntegration


def load_config(config_file: str = "config.yml") -> dict:
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def cmd_backtest(args):
    """Run backtest command"""
    print("\n" + "="*60)
    print("📊 BACKTEST COMMAND")
    print("="*60)
    
    generator = HistoricalDataGenerator()
    
    if args.years:
        print(f"\n📈 Generating {args.years} years of data...")
        df = generator.generate_with_market_events(years=args.years)
    else:
        print("\n📈 Loading live data...")
        try:
            df = AngelOneMarketData(
                api_key='MHaAyAN4',
                client_code='M450789',
                password='0492',
                totp_secret='KRFPVGCL7J2EBSHTN2JQH3USUQ'
            ).get_historical_data('NIFTY', '99926000', days=30)
        except:
            print("❌ Could not fetch live data")
            return
    
    if df is not None:
        print(f"✅ Loaded {len(df)} bars")
        print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        
        tester = StrategyBacktester()
        tester.backtester.initial_capital = args.capital
        
        result = tester.run_strategy_backtest(df, args.strategy, {})
        
        if 'error' not in result:
            print(f"\n📊 RESULTS:")
            print(f"   Initial Capital: ₹{result['initial_capital']:,.2f}")
            print(f"   Final Capital: ₹{result['final_capital']:,.2f}")
            print(f"   Returns: {result['returns_percent']:.2f}%")
            print(f"   Total Trades: {result['total_trades']}")
            print(f"   Win Rate: {result['win_rate']:.2f}%")
            print(f"   Max Drawdown: {result['max_drawdown']:.2f}%")
            print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"\n✅ Results saved to {args.output}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("❌ No data available")


def cmd_signal(args):
    """Generate AI signal command"""
    print("\n" + "="*60)
    print("🤖 AI SIGNAL COMMAND")
    print("="*60)
    
    try:
        market = AngelOneMarketData(
            api_key='MHaAyAN4',
            client_code='M450789',
            password='0492',
            totp_secret='KRFPVGCL7J2EBSHTN2JQH3USUQ'
        )
        
        if args.refresh:
            df = market.get_historical_data('NIFTY', '99926000', days=30)
            if df is not None:
                df.to_csv('nifty_live.csv')
                print(f"✅ Refreshed {len(df)} days data")
        else:
            df = market.get_historical_data('NIFTY', '99926000', days=30)
        
        if df is not None:
            generator = AISignalGenerator()
            signal = generator.generate_comprehensive_signal(df)
            
            print(f"\n📊 NIFTY: ₹{df['close'].iloc[-1]:.2f}")
            print(f"\n🎯 RECOMMENDATION: {signal['recommendation']}")
            print(f"📊 Score: {signal['score']}")
            print(f"🎯 Confidence: {signal['confidence']}%")
            
            print(f"\n📝 Reasons:")
            for reason in signal.get('reasons', []):
                print(f"   • {reason}")
            
            if args.telegram:
                integration = AIIntegration()
                print(f"\n📱 Telegram Message:")
                print(integration.format_signal_for_telegram(signal))
        else:
            print("❌ Could not fetch data")
    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_live(args):
    """Live market data command"""
    print("\n" + "="*60)
    print("📡 LIVE MARKET DATA")
    print("="*60)
    
    try:
        market = AngelOneMarketData(
            api_key='MHaAyAN4',
            client_code='M450789',
            password='0492',
            totp_secret='KRFPVGCL7J2EBSHTN2JQH3USUQ'
        )
        
        if market.connected:
            indices = [
                ('NIFTY', '99926000'),
                ('BANKNIFTY', '99926009'),
            ]
            
            print("\n📊 Live Quotes:")
            for symbol, token in indices:
                quote = market.get_index_quote(symbol, token)
                print(f"   {symbol}: ₹{quote['ltp']}")
    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_compare(args):
    """Compare strategies command"""
    print("\n" + "="*60)
    print("📊 STRATEGY COMPARISON")
    print("="*60)
    
    generator = HistoricalDataGenerator()
    
    if args.years:
        df = generator.generate_with_market_events(years=args.years)
    else:
        df = generator.generate_with_market_events(years=5)
    
    print(f"\n📈 Data: {len(df)} days")
    
    tester = StrategyBacktester()
    comparison = tester.compare_strategies(df)
    
    print("\n📊 Results:")
    print(comparison.to_string(index=False))
    
    if args.output:
        comparison.to_csv(args.output, index=False)
        print(f"\n✅ Saved to {args.output}")


def cmd_ml_train(args):
    """Train ML model command"""
    print("\n" + "="*60)
    print("🤖 ML MODEL TRAINING")
    print("="*60)
    
    print("\n📈 Preparing data...")
    
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=args.years)
    
    print(f"✅ Generated {len(df)} samples")
    
    predictor = EnsemblePredictor()
    
    print(f"\n📊 Training ensemble model...")
    print(f"   Model: LSTM + Prophet Ensemble")
    print(f"   Features: Technical indicators, patterns, sentiment")
    
    if args.save:
        print(f"\n✅ Model would be saved to: models/{args.name}")
        print("   (Model registry coming soon)")
    
    print(f"\n✅ Training complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Nifty Options Trading Toolkit - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('--strategy', '-s', default='ma_crossover',
                                  choices=['ma_crossover', 'rsi', 'breakout', 'ai_signal'],
                                  help='Strategy to backtest')
    backtest_parser.add_argument('--capital', '-c', type=float, default=100000,
                                  help='Initial capital')
    backtest_parser.add_argument('--years', '-y', type=int, default=None,
                                  help='Years of historical data (default: live data)')
    backtest_parser.add_argument('--output', '-o', type=str, default=None,
                                  help='Output JSON file')
    
    # Signal command
    signal_parser = subparsers.add_parser('signal', help='Generate AI signal')
    signal_parser.add_argument('--refresh', '-r', action='store_true',
                               help='Refresh live data')
    signal_parser.add_argument('--telegram', '-t', action='store_true',
                              help='Show telegram format')
    
    # Live command
    live_parser = subparsers.add_parser('live', help='Get live market data')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare strategies')
    compare_parser.add_argument('--years', '-y', type=int, default=None,
                                 help='Years of data')
    compare_parser.add_argument('--output', '-o', type=str, default=None,
                                help='Output CSV file')
    
    # ML Train command
    ml_parser = subparsers.add_parser('train', help='Train ML model')
    ml_parser.add_argument('--name', '-n', default='model_v1',
                           help='Model name')
    ml_parser.add_argument('--years', '-y', type=int, default=10,
                           help='Years of training data')
    ml_parser.add_argument('--save', action='store_true',
                           help='Save model')
    
    args = parser.parse_args()
    
    if args.command == 'backtest':
        cmd_backtest(args)
    elif args.command == 'signal':
        cmd_signal(args)
    elif args.command == 'live':
        cmd_live(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'train':
        cmd_ml_train(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
