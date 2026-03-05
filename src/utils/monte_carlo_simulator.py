"""
Phase 12: Monte Carlo Simulator for Risk Analysis
10,000 path simulations for portfolio VAR and CVAR analysis.
Author: Nifty Options Toolkit
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """
    Monte Carlo simulator for portfolio risk analysis.
    Generates 10,000+ simulated price paths and analyzes portfolio outcomes.
    """
    
    def __init__(self, num_simulations=10000, num_days=30):
        """
        Initialize simulator.
        
        Args:
            num_simulations: Number of Monte Carlo paths (default 10,000)
            num_days: Forecast period in days
        """
        self.num_simulations = num_simulations
        self.num_days = num_days
        self.simulated_paths = None
        self.portfolio_outcomes = None
        
    def _calculate_statistics(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate mean return and volatility from historical data.
        
        Returns:
            (mean_return, volatility)
        """
        returns = df['close'].pct_change().dropna()
        mean_return = returns.mean()
        volatility = returns.std()
        
        return mean_return, volatility
    
    def generate_paths(self, df: pd.DataFrame, drift=None, volatility=None) -> np.ndarray:
        """
        Generate Monte Carlo price paths using Geometric Brownian Motion.
        
        GBM Formula: dS = μS*dt + σS*dW
        
        Args:
            df: Historical OHLC data
            drift: Expected drift (if None, calculated from data)
            volatility: Price volatility (if None, calculated from data)
        
        Returns:
            Array of shape (num_simulations, num_days)
        """
        S0 = df['close'].iloc[-1]
        
        # Calculate statistics if not provided
        if drift is None or volatility is None:
            mean_return, vol = self._calculate_statistics(df)
            if drift is None:
                drift = mean_return
            if volatility is None:
                volatility = vol
        
        dt = 1.0 / 252  # Trading day
        
        # Generate random normal increments
        dW = np.random.normal(0, np.sqrt(dt), (self.num_simulations, self.num_days))
        
        # Initialize paths
        paths = np.zeros((self.num_simulations, self.num_days + 1))
        paths[:, 0] = S0
        
        # Generate paths
        for t in range(1, self.num_days + 1):
            paths[:, t] = paths[:, t-1] * np.exp(
                (drift - 0.5 * volatility ** 2) * dt + volatility * dW[:, t-1]
            )
        
        self.simulated_paths = paths
        return paths
    
    def calculate_var_cvar(self, confidence_level=0.95) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) and Conditional Value at Risk (CVaR).
        
        VaR: Maximum expected loss with given confidence
        CVaR: Expected loss exceeding VaR (also called Expected Shortfall)
        
        Args:
            confidence_level: Confidence level (0.95 = 95%)
        
        Returns:
            Dict with VaR, CVaR metrics
        """
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        final_prices = self.simulated_paths[:, -1]
        initial_price = self.simulated_paths[0, 0]
        
        # Calculate returns
        returns = (final_prices - initial_price) / initial_price
        
        # VaR calculation
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(returns, var_percentile)
        
        # CVaR calculation
        losses_exceeding_var = returns[returns <= var]
        cvar = losses_exceeding_var.mean() if len(losses_exceeding_var) > 0 else var
        
        return {
            'var': float(var),
            'cvar': float(cvar),
            'confidence_level': confidence_level,
            'var_percentage': float(var * 100),
            'cvar_percentage': float(cvar * 100)
        }
    
    def calculate_quantiles(self, quantiles=[0.05, 0.25, 0.5, 0.75, 0.95]) -> Dict[str, float]:
        """
        Calculate distribution quantiles for final prices.
        
        Returns:
            Dict with quantile values
        """
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        final_prices = self.simulated_paths[:, -1]
        
        result = {}
        for q in quantiles:
            result[f'q{int(q*100)}'] = float(np.percentile(final_prices, q * 100))
        
        return result
    
    def calculate_drawdown_analysis(self) -> Dict:
        """
        Analyze maximum drawdown across all simulated paths.
        
        Returns:
            Drawdown statistics
        """
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        max_drawdowns = []
        
        for path in self.simulated_paths:
            running_max = np.maximum.accumulate(path)
            drawdown = (path - running_max) / running_max
            max_drawdowns.append(np.min(drawdown))
        
        max_drawdowns = np.array(max_drawdowns)
        
        return {
            'mean_max_drawdown': float(np.mean(max_drawdowns)),
            'worst_max_drawdown': float(np.min(max_drawdowns)),
            'best_max_drawdown': float(np.max(max_drawdowns)),
            'std_max_drawdown': float(np.std(max_drawdowns)),
            'percentile_95_drawdown': float(np.percentile(max_drawdowns, 95))
        }
    
    def calculate_probability_metrics(self, target_price: float, initial_price: float) -> Dict:
        """
        Calculate probability of reaching target price.
        
        Args:
            target_price: Target price level
            initial_price: Starting price
        
        Returns:
            Probability metrics
        """
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        final_prices = self.simulated_paths[:, -1]
        
        # Probability of gaining X%
        gain_pct = (target_price - initial_price) / initial_price
        prob_target = (final_prices >= target_price).sum() / self.num_simulations
        
        # Expected return
        returns = (final_prices - initial_price) / initial_price
        expected_return = np.mean(returns)
        
        # Probability of loss
        prob_loss = (returns < 0).sum() / self.num_simulations
        
        return {
            'probability_reach_target': float(prob_target),
            'target_price': float(target_price),
            'gain_percentage': float(gain_pct * 100),
            'expected_return': float(expected_return * 100),
            'probability_loss': float(prob_loss),
            'mean_final_price': float(np.mean(final_prices)),
            'median_final_price': float(np.median(final_prices)),
            'std_final_price': float(np.std(final_prices))
        }
    
    def get_distribution_stats(self) -> Dict:
        """Get distribution statistics of final prices."""
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        final_prices = self.simulated_paths[:, -1]
        
        return {
            'mean': float(np.mean(final_prices)),
            'median': float(np.median(final_prices)),
            'std': float(np.std(final_prices)),
            'min': float(np.min(final_prices)),
            'max': float(np.max(final_prices)),
            'skewness': float(stats.skew(final_prices)),
            'kurtosis': float(stats.kurtosis(final_prices))
        }
    
    def get_full_report(self, initial_price: float, target_price: float, 
                       confidence_level: float = 0.95) -> Dict:
        """
        Generate comprehensive risk report.
        
        Returns:
            Complete analysis dictionary
        """
        if self.simulated_paths is None:
            raise ValueError("Must generate paths first")
        
        return {
            'simulation_info': {
                'num_simulations': self.num_simulations,
                'forecast_days': self.num_days
            },
            'initial_price': initial_price,
            'target_price': target_price,
            'var_analysis': self.calculate_var_cvar(confidence_level),
            'quantiles': self.calculate_quantiles(),
            'drawdown_analysis': self.calculate_drawdown_analysis(),
            'probability_metrics': self.calculate_probability_metrics(target_price, initial_price),
            'distribution_stats': self.get_distribution_stats()
        }


class CorrelationAnalyzer:
    """Analyze correlations between multiple assets."""
    
    def __init__(self):
        """Initialize correlation analyzer."""
        self.correlation_matrix = None
    
    def analyze_assets(self, data_dict: Dict[str, pd.DataFrame]) -> np.ndarray:
        """
        Analyze correlation between multiple assets.
        
        Args:
            data_dict: Dict mapping asset names to DataFrames
        
        Returns:
            Correlation matrix
        """
        returns_dict = {}
        
        for name, df in data_dict.items():
            returns_dict[name] = df['close'].pct_change().dropna()
        
        # Create DataFrame and calculate correlation
        returns_df = pd.DataFrame(returns_dict)
        self.correlation_matrix = returns_df.corr()
        
        return self.correlation_matrix
    
    def get_correlation_dict(self) -> Dict:
        """Get correlation as nested dictionary."""
        if self.correlation_matrix is None:
            raise ValueError("Must analyze assets first")
        
        return self.correlation_matrix.to_dict()


class SensitivityAnalyzer:
    """Parameter sensitivity analysis."""
    
    @staticmethod
    def analyze_volatility_sensitivity(df: pd.DataFrame, volatility_range: List[float]) -> Dict:
        """
        Analyze portfolio sensitivity to volatility changes.
        
        Args:
            df: Historical data
            volatility_range: List of volatility values to test
        
        Returns:
            Sensitivity results
        """
        results = {}
        base_return, _ = MonteCarloSimulator()._calculate_statistics(df)
        
        for vol in volatility_range:
            sim = MonteCarloSimulator(num_simulations=1000, num_days=30)
            sim.generate_paths(df, volatility=vol)
            var_cvar = sim.calculate_var_cvar()
            results[f'vol_{vol:.2f}'] = var_cvar
        
        return results
    
    @staticmethod
    def analyze_drift_sensitivity(df: pd.DataFrame, drift_range: List[float]) -> Dict:
        """
        Analyze portfolio sensitivity to drift changes.
        
        Args:
            df: Historical data
            drift_range: List of drift values to test
        
        Returns:
            Sensitivity results
        """
        results = {}
        _, base_vol = MonteCarloSimulator()._calculate_statistics(df)
        
        for drift in drift_range:
            sim = MonteCarloSimulator(num_simulations=1000, num_days=30)
            sim.generate_paths(df, drift=drift, volatility=base_vol)
            var_cvar = sim.calculate_var_cvar()
            results[f'drift_{drift:.4f}'] = var_cvar
        
        return results


if __name__ == "__main__":
    print("\nPhase 12: Monte Carlo Simulator")
    print("=" * 50)
    
    from utils.backtester import HistoricalDataGenerator
    gen = HistoricalDataGenerator()
    df = gen.generate_with_market_events(years=1).tail(500)
    
    # Run Monte Carlo simulation
    simulator = MonteCarloSimulator(num_simulations=10000, num_days=30)
    simulator.generate_paths(df)
    
    # Get comprehensive report
    report = simulator.get_full_report(
        initial_price=df['close'].iloc[-1],
        target_price=df['close'].iloc[-1] * 1.10,
        confidence_level=0.95
    )
    
    print(f"\n💰 Monte Carlo Simulation Report")
    print(f"Simulations: {report['simulation_info']['num_simulations']:,}")
    print(f"Forecast Period: {report['simulation_info']['forecast_days']} days\n")
    
    print(f"📊 VaR Analysis (95% confidence):")
    print(f"   VaR: {report['var_analysis']['var_percentage']:.2f}%")
    print(f"   CVaR: {report['var_analysis']['cvar_percentage']:.2f}%\n")
    
    print(f"📈 Probability Metrics:")
    print(f"   Target Probability: {report['probability_metrics']['probability_reach_target']:.2%}")
    print(f"   Expected Return: {report['probability_metrics']['expected_return']:.2f}%")
    print(f"   Loss Probability: {report['probability_metrics']['probability_loss']:.2%}")
