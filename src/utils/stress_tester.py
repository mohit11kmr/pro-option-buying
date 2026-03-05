"""
Phase 12: Stress Tester for Portfolio Risk Management
Tests portfolio against 5 extreme market scenarios.
Author: Nifty Options Toolkit
"""

import numpy as np
import pandas as pd
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StressScenario(Enum):
    """Realistic market stress scenarios."""
    MARKET_CRASH = 1        # 20-30% single day crash
    VOLATILITY_SPIKE = 2    # VIX spike to 40+
    SUSTAINED_DECLINE = 3   # 5-day 15% drop
    GAP_DOWN_OPEN = 4       # 10% gap down at open
    LIQUIDITY_CRUNCH = 5    # Wide spreads, slippage


@dataclass
class StressResult:
    """Result of stress test scenario."""
    scenario_name: str
    initial_portfolio_value: float
    final_portfolio_value: float
    max_loss: float
    max_loss_percent: float
    affected_positions: List[Dict]
    recovery_days: int
    tail_risk: float
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'scenario': self.scenario_name,
            'initial_value': self.initial_portfolio_value,
            'final_value': self.final_portfolio_value,
            'max_loss': self.max_loss,
            'max_loss_percent': self.max_loss_percent,
            'recovery_days': self.recovery_days,
            'tail_risk': self.tail_risk,
            'affected_positions': self.affected_positions
        }


class StressTester:
    """
    Portfolio stress tester for extreme market scenarios.
    Tests against historical and hypothetical crises.
    """
    
    def __init__(self, initial_capital: float = 100000):
        """
        Initialize stress tester.
        
        Args:
            initial_capital: Starting portfolio capital
        """
        self.initial_capital = initial_capital
        self.portfolio_positions = {}
        self.test_results = {}
        
    def add_position(self, symbol: str, quantity: float, entry_price: float, 
                    position_type: str = 'long'):
        """
        Add position to portfolio for stress testing.
        
        Args:
            symbol: Asset symbol
            quantity: Number of units
            entry_price: Entry price
            position_type: 'long' or 'short'
        """
        self.portfolio_positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'type': position_type,
            'current_price': entry_price,
            'pnl': 0
        }
    
    def _apply_market_crash(self, price_change_pct: float = -25) -> Dict:
        """
        Scenario 1: Market Crash (20-30% single day drop)
        
        Example: US stocks crashed 20% on March 16, 2020
        """
        logger.info(f"Simulating market crash scenario ({price_change_pct}%)...")
        
        affected_positions = []
        total_loss = 0
        
        for symbol, position in self.portfolio_positions.items():
            # Price drops
            new_price = position['entry_price'] * (1 + price_change_pct / 100)
            
            # Calculate P&L
            if position['type'] == 'long':
                pnl = (new_price - position['entry_price']) * position['quantity']
            else:  # short
                pnl = (position['entry_price'] - new_price) * position['quantity']
            
            total_loss += pnl
            affected_positions.append({
                'symbol': symbol,
                'previous_price': position['entry_price'],
                'new_price': new_price,
                'pnl': pnl,
                'pnl_percent': (pnl / (position['entry_price'] * position['quantity'])) * 100
            })
        
        return {
            'scenario': StressScenario.MARKET_CRASH,
            'price_change': price_change_pct,
            'total_loss': total_loss,
            'affected_positions': affected_positions,
            'portfolio_impact': (total_loss / self.initial_capital) * 100
        }
    
    def _apply_volatility_spike(self, implied_vol_multiplier: float = 2.5) -> Dict:
        """
        Scenario 2: Volatility Spike (VIX 30+ → 60+)
        
        Affects options portfolio significantly via Vega exposure.
        Example: March 2020, VIX spiked to 82.69
        """
        logger.info(f"Simulating volatility spike scenario (Vol multiplier: {implied_vol_multiplier}x)...")
        
        affected_positions = []
        total_loss = 0
        
        # Simplified Vega impact
        # For each position, estimate vega impact
        for symbol, position in self.portfolio_positions.items():
            # Estimate vega (simplified: -10000 per 1% IV change for ATM options)
            estimated_vega = -10000
            vol_change_pct = (implied_vol_multiplier - 1) * 100
            
            # P&L impact from volatility
            pnl = estimated_vega * (vol_change_pct / 100)
            
            total_loss += pnl
            affected_positions.append({
                'symbol': symbol,
                'vega_exposure': estimated_vega,
                'vol_change_pct': vol_change_pct,
                'pnl': pnl
            })
        
        return {
            'scenario': StressScenario.VOLATILITY_SPIKE,
            'vol_multiplier': implied_vol_multiplier,
            'total_loss': total_loss,
            'affected_positions': affected_positions,
            'portfolio_impact': (total_loss / self.initial_capital) * 100
        }
    
    def _apply_sustained_decline(self, daily_decline_pct: float = -3, num_days: int = 5) -> Dict:
        """
        Scenario 3: Sustained Decline (5 days of 3% daily losses)
        
        Example: COVID crash March 9-13, 2020 (average -5% daily)
        """
        logger.info(f"Simulating sustained {num_days}-day decline ({daily_decline_pct}% daily)...")
        
        affected_positions = []
        total_loss = 0
        
        # Compound decline
        total_decline = (1 + daily_decline_pct/100) ** num_days - 1
        
        for symbol, position in self.portfolio_positions.items():
            new_price = position['entry_price'] * (1 + total_decline)
            
            if position['type'] == 'long':
                pnl = (new_price - position['entry_price']) * position['quantity']
            else:
                pnl = (position['entry_price'] - new_price) * position['quantity']
            
            total_loss += pnl
            affected_positions.append({
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': new_price,
                'cumulative_decline_pct': total_decline * 100,
                'pnl': pnl
            })
        
        return {
            'scenario': StressScenario.SUSTAINED_DECLINE,
            'daily_decline_pct': daily_decline_pct,
            'num_days': num_days,
            'total_decline_pct': total_decline * 100,
            'total_loss': total_loss,
            'affected_positions': affected_positions,
            'portfolio_impact': (total_loss / self.initial_capital) * 100
        }
    
    def _apply_gap_down_open(self, gap_down_pct: float = -10) -> Dict:
        """
        Scenario 4: Gap Down at Market Open (10%+ overnight gap)
        
        Example: INFY gapped down 10% on Oct 12, 2023 (Q2 miss)
        """
        logger.info(f"Simulating gap down opening ({gap_down_pct}%)...")
        
        affected_positions = []
        total_loss = 0
        
        for symbol, position in self.portfolio_positions.items():
            # Gap down at open - no opportunity to exit before taking loss
            new_price = position['entry_price'] * (1 + gap_down_pct / 100)
            
            if position['type'] == 'long':
                pnl = (new_price - position['entry_price']) * position['quantity']
            else:
                pnl = (position['entry_price'] - new_price) * position['quantity']
            
            total_loss += pnl
            affected_positions.append({
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'gap_down_price': new_price,
                'gap_pct': gap_down_pct,
                'pnl': pnl,
                'execution_risk': 'Cannot exit at open; slippage inevitable'
            })
        
        return {
            'scenario': StressScenario.GAP_DOWN_OPEN,
            'gap_down_pct': gap_down_pct,
            'total_loss': total_loss,
            'affected_positions': affected_positions,
            'portfolio_impact': (total_loss / self.initial_capital) * 100,
            'execution_risk': True
        }
    
    def _apply_liquidity_crunch(self, spread_widening_pct: float = 200, slippage_pct: float = 2) -> Dict:
        """
        Scenario 5: Liquidity Crisis (Spreads widen 200%, slippage 2%+)
        
        Example: March 2020, options spreads widened to 5-10% (normally 0.5-1%)
        """
        logger.info(f"Simulating liquidity crunch (spreads +{spread_widening_pct}%, slippage +{slippage_pct}%)...")
        
        affected_positions = []
        total_loss = 0
        
        for symbol, position in self.portfolio_positions.items():
            # Slippage cost on exit
            slippage_cost = position['entry_price'] * position['quantity'] * (slippage_pct / 100)
            
            # Wide spreads make it hard to exit at fair value
            execution_price = position['entry_price'] * (1 - slippage_pct / 100)
            
            pnl = (execution_price - position['entry_price']) * position['quantity'] - slippage_cost
            
            total_loss += pnl
            affected_positions.append({
                'symbol': symbol,
                'fair_price': position['entry_price'],
                'execution_price': execution_price,
                'bid_ask_spread_widening': spread_widening_pct,
                'slippage_pct': slippage_pct,
                'slippage_cost': slippage_cost,
                'pnl': pnl
            })
        
        return {
            'scenario': StressScenario.LIQUIDITY_CRUNCH,
            'spread_widening': spread_widening_pct,
            'slippage_pct': slippage_pct,
            'total_loss': total_loss,
            'affected_positions': affected_positions,
            'portfolio_impact': (total_loss / self.initial_capital) * 100
        }
    
    def run_all_stress_tests(self) -> Dict[str, StressResult]:
        """
        Run all 5 stress scenarios.
        
        Returns:
            Dictionary of stress test results
        """
        logger.info("\n" + "="*60)
        logger.info("Starting Comprehensive Stress Testing")
        logger.info("="*60)
        
        results = {}
        
        # Scenario 1: Market Crash
        crash_result = self._apply_market_crash(-25)
        results['market_crash'] = StressResult(
            scenario_name="Market Crash (-25%)",
            initial_portfolio_value=self.initial_capital,
            final_portfolio_value=self.initial_capital + crash_result['total_loss'],
            max_loss=crash_result['total_loss'],
            max_loss_percent=crash_result['portfolio_impact'],
            affected_positions=crash_result['affected_positions'],
            recovery_days=15,  # Historical: usually recovers in 2-3 weeks
            tail_risk=crash_result['portfolio_impact']
        )
        
        # Scenario 2: Volatility Spike
        vol_result = self._apply_volatility_spike(2.5)
        results['volatility_spike'] = StressResult(
            scenario_name="Volatility Spike (VIX 2.5x)",
            initial_portfolio_value=self.initial_capital,
            final_portfolio_value=self.initial_capital + vol_result['total_loss'],
            max_loss=vol_result['total_loss'],
            max_loss_percent=vol_result['portfolio_impact'],
            affected_positions=vol_result['affected_positions'],
            recovery_days=5,
            tail_risk=vol_result['portfolio_impact']
        )
        
        # Scenario 3: Sustained Decline
        sustained_result = self._apply_sustained_decline(-3, 5)
        results['sustained_decline'] = StressResult(
            scenario_name="5-Day Sustained Decline (-3% daily)",
            initial_portfolio_value=self.initial_capital,
            final_portfolio_value=self.initial_capital + sustained_result['total_loss'],
            max_loss=sustained_result['total_loss'],
            max_loss_percent=sustained_result['portfolio_impact'],
            affected_positions=sustained_result['affected_positions'],
            recovery_days=20,
            tail_risk=sustained_result['portfolio_impact']
        )
        
        # Scenario 4: Gap Down
        gap_result = self._apply_gap_down_open(-10)
        results['gap_down'] = StressResult(
            scenario_name="Gap Down at Open (-10%)",
            initial_portfolio_value=self.initial_capital,
            final_portfolio_value=self.initial_capital + gap_result['total_loss'],
            max_loss=gap_result['total_loss'],
            max_loss_percent=gap_result['portfolio_impact'],
            affected_positions=gap_result['affected_positions'],
            recovery_days=10,
            tail_risk=gap_result['portfolio_impact']
        )
        
        # Scenario 5: Liquidity Crunch
        liq_result = self._apply_liquidity_crunch(200, 2)
        results['liquidity_crunch'] = StressResult(
            scenario_name="Liquidity Crunch (+200% spreads, +2% slippage)",
            initial_portfolio_value=self.initial_capital,
            final_portfolio_value=self.initial_capital + liq_result['total_loss'],
            max_loss=liq_result['total_loss'],
            max_loss_percent=liq_result['portfolio_impact'],
            affected_positions=liq_result['affected_positions'],
            recovery_days=3,
            tail_risk=liq_result['portfolio_impact']
        )
        
        self.test_results = results
        
        logger.info("\n" + "="*60)
        logger.info("Stress Testing Complete")
        logger.info("="*60 + "\n")
        
        return results
    
    def get_worst_case_scenario(self) -> StressResult:
        """Get the worst-case outcome across all scenarios."""
        if not self.test_results:
            raise ValueError("Must run stress tests first")
        
        worst = max(
            self.test_results.values(),
            key=lambda x: abs(x.max_loss)
        )
        
        return worst
    
    def get_summary_report(self) -> Dict:
        """Get summary of all stress tests."""
        if not self.test_results:
            raise ValueError("Must run stress tests first")
        
        losses = [r.max_loss_percent for r in self.test_results.values()]
        
        return {
            'scenarios_tested': len(self.test_results),
            'worst_case_loss': max(losses),
            'average_loss': np.mean(losses),
            'best_case_loss': min(losses),
            'std_loss': np.std(losses),
            'results': {k: v.to_dict() for k, v in self.test_results.items()},
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate risk management recommendations based on stress test results."""
        if not self.test_results:
            return []
        
        worst_loss = max(r.max_loss_percent for r in self.test_results.values())
        
        recommendations = []
        
        if worst_loss < -5:
            recommendations.append("❌ Portfolio is under-hedged. Consider adding protective puts.")
        if worst_loss < -15:
            recommendations.append("⚠️ Portfolio has excessive tail risk. Reduce position sizes.")
        if worst_loss < -25:
            recommendations.append("🚨 Critical risk level. Implement circuit breakers or reduce leverage.")
        
        recommendations.append("✅ Consider diversifying across uncorrelated assets.")
        recommendations.append("📊 Review Greeks regularly; maintain delta neutrality where possible.")
        
        return recommendations


if __name__ == "__main__":
    print("\nPhase 12: Stress Testing System")
    print("=" * 60)
    
    # Create stress tester
    tester = StressTester(initial_capital=100000)
    
    # Add sample positions
    tester.add_position('NIFTY', 1, 24800, 'long')
    tester.add_position('BANKNIFTY', 1, 59800, 'long')
    
    # Run all tests
    results = tester.run_all_stress_tests()
    
    # Get summary
    summary = tester.get_summary_report()
    
    print(f"\n📊 Stress Test Summary:")
    print(f"   Worst Case Loss: {summary['worst_case_loss']:.2f}%")
    print(f"   Average Loss: {summary['average_loss']:.2f}%")
    print(f"   Best Case Loss: {summary['best_case_loss']:.2f}%")
    
    print(f"\n🎯 Recommendations:")
    for rec in summary['recommendations']:
        print(f"   {rec}")
