"""
Walk-Forward Testing
====================
Advanced backtesting with walk-forward optimization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Any, Tuple
from datetime import datetime, timedelta


class WalkForwardBacktester:
    """
    Walk-forward testing with rolling optimization windows.
    
    Splits data into:
    - In-sample periods for parameter optimization
    - Out-of-sample periods for validation
    """
    
    def __init__(
        self,
        in_sample_months: int = 12,
        out_of_sample_months: int = 3,
        step_months: int = 1
    ):
        self.in_sample_months = in_sample_months
        self.out_of_sample_months = out_of_sample_months
        self.step_months = step_months
    
    def generate_windows(
        self,
        df: pd.DataFrame
    ) -> List[Dict[str, pd.DataFrame]]:
        """Generate walk-forward windows."""
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        df = df.sort_index()
        
        start_date = df.index[0]
        end_date = df.index[-1]
        
        current = start_date
        windows = []
        
        while True:
            is_start = current
            is_end = current + pd.DateOffset(months=self.in_sample_months)
            oos_start = is_end
            oos_end = oos_start + pd.DateOffset(months=self.out_of_sample_months)
            
            if is_end > end_date:
                break
            
            in_sample = df.loc[is_start:is_end]
            out_of_sample = df.loc[oos_start:oos_end] if oos_end <= end_date else None
            
            if out_of_sample is not None and len(out_of_sample) > 0:
                windows.append({
                    'in_sample': in_sample,
                    'out_of_sample': out_of_sample,
                    'is_period': (is_start, is_end),
                    'oos_period': (oos_start, oos_end)
                })
            
            current = current + pd.DateOffset(months=self.step_months)
            
            if current + pd.DateOffset(months=self.in_sample_months) > end_date:
                break
        
        return windows
    
    def optimize_parameters(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Find best parameters using grid search on in-sample data."""
        best_params = None
        best_score = float('-inf')
        
        from itertools import product
        param_combinations = list(product(*param_grid.values()))
        param_names = list(param_grid.keys())
        
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            
            try:
                score = self._evaluate_params(df, strategy_func, param_dict)
                
                if score > best_score:
                    best_score = score
                    best_params = param_dict
            except Exception:
                continue
        
        return best_params or {}
    
    def _evaluate_params(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        params: Dict
    ) -> float:
        """Evaluate strategy with given parameters."""
        from src.utils.backtester import Backtester
        
        bt = Backtester()
        result = bt.run_backtest(df, strategy_func, params)
        
        if 'error' in result:
            return float('-inf')
        
        return result.get('sharpe_ratio', 0)
    
    def run_walk_forward(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]]
    ) -> Dict:
        """Run complete walk-forward analysis."""
        windows = self.generate_windows(df)
        
        results = []
        
        for i, window in enumerate(windows):
            print(f"\n--- Window {i+1}/{len(windows)} ---")
            print(f"In-sample: {window['is_period']}")
            print(f"Out-of-sample: {window['oos_period']}")
            
            in_sample = window['in_sample']
            out_of_sample = window['out_of_sample']
            
            best_params = self.optimize_parameters(in_sample, strategy_func, param_grid)
            print(f"Best params: {best_params}")
            
            from src.utils.backtester import Backtester
            bt = Backtester()
            oos_result = bt.run_backtest(out_of_sample, strategy_func, best_params)
            
            window_result = {
                'window': i + 1,
                'in_sample_period': f"{window['is_period'][0]} to {window['is_period'][1]}",
                'out_of_sample_period': f"{window['oos_period'][0]} to {window['oos_period'][1]}",
                'optimized_params': best_params,
                'oos_returns': oos_result.get('returns_percent', 0),
                'oos_sharpe': oos_result.get('sharpe_ratio', 0),
                'oos_trades': oos_result.get('total_trades', 0),
                'oos_win_rate': oos_result.get('win_rate', 0)
            }
            
            results.append(window_result)
            print(f"OOS Returns: {window_result['oos_returns']:.2f}%")
        
        return self._aggregate_results(results)
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate walk-forward results."""
        returns = [r['oos_returns'] for r in results]
        sharpes = [r['oos_sharpe'] for r in results]
        
        return {
            'windows': results,
            'summary': {
                'total_windows': len(results),
                'avg_oos_returns': np.mean(returns),
                'avg_oos_sharpe': np.mean(sharpes),
                'max_oos_return': np.max(returns),
                'min_oos_return': np.min(returns),
                'consistency': len([r for r in returns if r > 0]) / len(returns) * 100 if returns else 0
            }
        }


class ParameterOptimizer:
    """Parameter optimization using various search methods."""
    
    @staticmethod
    def grid_search(
        df: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        metric: str = 'sharpe_ratio'
    ) -> Tuple[Dict, List[Dict]]:
        """Grid search optimization."""
        from itertools import product
        
        param_names = list(param_grid.keys())
        param_combinations = list(product(*param_grid.values()))
        
        results = []
        
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            
            from src.utils.backtester import Backtester
            bt = Backtester()
            result = bt.run_backtest(df, strategy_func, param_dict)
            
            if 'error' not in result:
                results.append({
                    'params': param_dict,
                    'returns': result.get('returns_percent', 0),
                    'sharpe': result.get('sharpe_ratio', 0),
                    'win_rate': result.get('win_rate', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'total_trades': result.get('total_trades', 0)
                })
        
        if not results:
            return {}, []
        
        best = max(results, key=lambda x: x.get(metric, 0))
        
        return best.get('params', {}), results
    
    @staticmethod
    def random_search(
        df: pd.DataFrame,
        strategy_func: Callable,
        param_distributions: Dict[str, Tuple[Any, Any]],
        n_iter: int = 50,
        metric: str = 'sharpe_ratio'
    ) -> Tuple[Dict, List[Dict]]:
        """Random search optimization."""
        import random
        
        results = []
        
        for _ in range(n_iter):
            params = {}
            for key, (low, high) in param_distributions.items():
                if isinstance(low, int) and isinstance(high, int):
                    params[key] = random.randint(low, high)
                else:
                    params[key] = random.uniform(low, high)
            
            from src.utils.backtester import Backtester
            bt = Backtester()
            result = bt.run_backtest(df, strategy_func, params)
            
            if 'error' not in result:
                results.append({
                    'params': params,
                    'returns': result.get('returns_percent', 0),
                    'sharpe': result.get('sharpe_ratio', 0),
                    'win_rate': result.get('win_rate', 0)
                })
        
        if not results:
            return {}, []
        
        best = max(results, key=lambda x: x.get(metric, 0))
        
        return best.get('params', {}), results


def demo_walk_forward():
    """Demonstrate walk-forward testing."""
    print("\n" + "="*60)
    print("WALK-FORWARD TESTING DEMO")
    print("="*60)
    
    from src.utils.backtester import HistoricalDataGenerator
    
    generator = HistoricalDataGenerator()
    df = generator.generate_with_market_events(years=5)
    
    print(f"Generated {len(df)} days of data")
    
    wf = WalkForwardBacktester(
        in_sample_months=12,
        out_of_sample_months=3,
        step_months=3
    )
    
    param_grid = {
        'short_ma': [10, 15, 20],
        'long_ma': [30, 40, 50]
    }
    
    def strategy_func(df, params):
        from src.utils.backtester import StrategyBacktester
        tester = StrategyBacktester()
        return tester.ma_crossover_strategy(df, params)
    
    results = wf.run_walk_forward(df, strategy_func, param_grid)
    
    print("\n" + "="*60)
    print("WALK-FORWARD SUMMARY")
    print("="*60)
    print(f"Total Windows: {results['summary']['total_windows']}")
    print(f"Avg OOS Returns: {results['summary']['avg_oos_returns']:.2f}%")
    print(f"Avg OOS Sharpe: {results['summary']['avg_oos_sharpe']:.2f}")
    print(f"Consistency: {results['summary']['consistency']:.1f}%")


if __name__ == "__main__":
    demo_walk_forward()
