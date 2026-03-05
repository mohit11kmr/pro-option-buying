"""
Options Greeks Analyzer
========================
IV analysis, Delta/Gamma/Theta/Vega calculation for smart option selection.

Uses Black-Scholes model for Greeks computation.
Provides IV percentile, IV rank, and theta decay warnings.
"""

import numpy as np
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class GreeksAnalyzer:
    """
    Options Greeks calculator with IV analysis for smart option buying decisions.
    """

    # Risk-free rate (India — approximate RBI repo rate)
    RISK_FREE_RATE = 0.065

    # NIFTY lot size
    LOT_SIZE = 25

    def __init__(self):
        self.iv_history: List[float] = []

    # ========================
    #  BLACK-SCHOLES MODEL
    # ========================

    @staticmethod
    def _norm_cdf(x: float) -> float:
        """Standard normal CDF."""
        return stats.norm.cdf(x)

    @staticmethod
    def _norm_pdf(x: float) -> float:
        """Standard normal PDF."""
        return stats.norm.pdf(x)

    def _d1(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 in Black-Scholes formula."""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    def _d2(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 in Black-Scholes formula."""
        if T <= 0 or sigma <= 0:
            return 0.0
        return self._d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

    def bs_call_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes Call option price."""
        if T <= 0:
            return max(S - K, 0)
        d1 = self._d1(S, K, T, r, sigma)
        d2 = self._d2(S, K, T, r, sigma)
        return S * self._norm_cdf(d1) - K * math.exp(-r * T) * self._norm_cdf(d2)

    def bs_put_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes Put option price."""
        if T <= 0:
            return max(K - S, 0)
        d1 = self._d1(S, K, T, r, sigma)
        d2 = self._d2(S, K, T, r, sigma)
        return K * math.exp(-r * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)

    # ========================
    #  GREEKS CALCULATION
    # ========================

    def calculate_greeks(self, spot: float, strike: float, days_to_expiry: int,
                         iv: float, option_type: str = "CE",
                         r: float = None) -> Dict:
        """
        Calculate all Greeks for an option.

        Args:
            spot: Current underlying price
            strike: Strike price
            days_to_expiry: Days until expiry
            iv: Implied volatility (as decimal, e.g. 0.15 for 15%)
            option_type: "CE" for Call, "PE" for Put
            r: Risk-free rate (uses default if None)

        Returns:
            Dict with delta, gamma, theta, vega, rho, and prices
        """
        if r is None:
            r = self.RISK_FREE_RATE

        T = max(days_to_expiry / 365.0, 0.001)  # Time in years
        sigma = iv

        d1 = self._d1(spot, strike, T, r, sigma)
        d2 = self._d2(spot, strike, T, r, sigma)

        # --- Delta ---
        if option_type == "CE":
            delta = self._norm_cdf(d1)
        else:
            delta = self._norm_cdf(d1) - 1

        # --- Gamma (same for call/put) ---
        gamma = self._norm_pdf(d1) / (spot * sigma * math.sqrt(T))

        # --- Theta (per day) ---
        theta_common = -(spot * self._norm_pdf(d1) * sigma) / (2 * math.sqrt(T))
        if option_type == "CE":
            theta = (theta_common - r * strike * math.exp(-r * T) * self._norm_cdf(d2)) / 365
        else:
            theta = (theta_common + r * strike * math.exp(-r * T) * self._norm_cdf(-d2)) / 365

        # --- Vega (per 1% IV change) ---
        vega = spot * math.sqrt(T) * self._norm_pdf(d1) / 100

        # --- Rho (per 1% rate change) ---
        if option_type == "CE":
            rho = strike * T * math.exp(-r * T) * self._norm_cdf(d2) / 100
        else:
            rho = -strike * T * math.exp(-r * T) * self._norm_cdf(-d2) / 100

        # --- Option Price ---
        if option_type == "CE":
            price = self.bs_call_price(spot, strike, T, r, sigma)
        else:
            price = self.bs_put_price(spot, strike, T, r, sigma)

        # --- Intrinsic & Time Value ---
        if option_type == "CE":
            intrinsic = max(spot - strike, 0)
        else:
            intrinsic = max(strike - spot, 0)
        time_value = price - intrinsic

        # --- Moneyness ---
        moneyness = spot / strike
        if option_type == "CE":
            if moneyness > 1.02:
                money_label = "ITM"
            elif moneyness < 0.98:
                money_label = "OTM"
            else:
                money_label = "ATM"
        else:
            if moneyness < 0.98:
                money_label = "ITM"
            elif moneyness > 1.02:
                money_label = "OTM"
            else:
                money_label = "ATM"

        return {
            "spot": spot,
            "strike": strike,
            "option_type": option_type,
            "days_to_expiry": days_to_expiry,
            "iv": round(sigma * 100, 2),

            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 2),
            "vega": round(vega, 2),
            "rho": round(rho, 4),

            "theoretical_price": round(price, 2),
            "intrinsic_value": round(intrinsic, 2),
            "time_value": round(time_value, 2),

            "moneyness": money_label,
            "moneyness_ratio": round(moneyness, 4),

            "lot_size": self.LOT_SIZE,
            "lot_value": round(price * self.LOT_SIZE, 2),
        }

    def calculate_greeks_chain(self, spot: float, strikes: List[float],
                                days_to_expiry: int, ivs: Dict[float, float] = None,
                                default_iv: float = 0.15) -> Dict:
        """
        Calculate Greeks for multiple strikes (both CE and PE).

        Returns:
            Dict with 'calls' and 'puts' lists, each containing Greeks data.
        """
        calls = []
        puts = []

        for strike in sorted(strikes):
            iv = ivs.get(strike, default_iv) if ivs else default_iv

            ce_greeks = self.calculate_greeks(spot, strike, days_to_expiry, iv, "CE")
            pe_greeks = self.calculate_greeks(spot, strike, days_to_expiry, iv, "PE")

            calls.append(ce_greeks)
            puts.append(pe_greeks)

        return {
            "spot": spot,
            "days_to_expiry": days_to_expiry,
            "calls": calls,
            "puts": puts
        }

    # ========================
    #  IMPLIED VOLATILITY
    # ========================

    def calculate_iv(self, market_price: float, spot: float, strike: float,
                     days_to_expiry: int, option_type: str = "CE",
                     r: float = None, precision: float = 0.0001) -> float:
        """
        Calculate Implied Volatility using bisection method.
        """
        if r is None:
            r = self.RISK_FREE_RATE

        T = max(days_to_expiry / 365.0, 0.001)
        low_vol = 0.01
        high_vol = 5.0

        for _ in range(100):
            mid_vol = (low_vol + high_vol) / 2

            if option_type == "CE":
                price = self.bs_call_price(spot, strike, T, r, mid_vol)
            else:
                price = self.bs_put_price(spot, strike, T, r, mid_vol)

            if abs(price - market_price) < precision:
                return mid_vol

            if price > market_price:
                high_vol = mid_vol
            else:
                low_vol = mid_vol

        return (low_vol + high_vol) / 2

    # ========================
    #  IV ANALYSIS
    # ========================

    def analyze_iv(self, current_iv: float, historical_ivs: List[float] = None) -> Dict:
        """
        Comprehensive IV analysis — percentile, rank, and recommendations.
        """
        if historical_ivs is None:
            # Use stored history or generate default range
            historical_ivs = self.iv_history if self.iv_history else [
                0.10, 0.12, 0.14, 0.15, 0.16, 0.18, 0.20, 0.22,
                0.25, 0.28, 0.30, 0.35, 0.14, 0.13, 0.15, 0.17,
                0.19, 0.21, 0.23, 0.16
            ]

        sorted_ivs = sorted(historical_ivs)
        n = len(sorted_ivs)

        # IV Percentile: % of past IV values below current
        below_count = sum(1 for iv in sorted_ivs if iv < current_iv)
        iv_percentile = (below_count / n) * 100 if n > 0 else 50

        # IV Rank: (current - min) / (max - min)
        iv_min = min(sorted_ivs)
        iv_max = max(sorted_ivs)
        iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100 if iv_max > iv_min else 50

        # Mean IV
        iv_mean = np.mean(sorted_ivs)

        # Recommendation
        if iv_percentile < 20:
            iv_environment = "LOW"
            buying_advice = "✅ Low IV — Good for option buying (cheap premiums)"
        elif iv_percentile < 40:
            iv_environment = "BELOW_AVERAGE"
            buying_advice = "✅ Below-average IV — Favorable for buying"
        elif iv_percentile < 60:
            iv_environment = "NORMAL"
            buying_advice = "🟡 Normal IV — Acceptable for buying"
        elif iv_percentile < 80:
            iv_environment = "HIGH"
            buying_advice = "⚠️ High IV — Premiums expensive, risk of IV crush"
        else:
            iv_environment = "VERY_HIGH"
            buying_advice = "🔴 Very high IV — Avoid buying, consider selling strategies"

        return {
            "current_iv": round(current_iv * 100, 2),
            "iv_percentile": round(iv_percentile, 1),
            "iv_rank": round(iv_rank, 1),
            "iv_mean": round(iv_mean * 100, 2),
            "iv_min": round(iv_min * 100, 2),
            "iv_max": round(iv_max * 100, 2),
            "iv_environment": iv_environment,
            "buying_advice": buying_advice,
            "favorable_for_buying": iv_percentile < 60,
        }

    def detect_iv_crush_risk(self, days_to_expiry: int, events: List[Dict] = None) -> Dict:
        """
        Detect potential IV crush scenarios.

        Events like: expiry, RBI policy, budget, quarterly results
        """
        risks = []

        # Near-expiry crush
        if days_to_expiry <= 2:
            risks.append({
                "event": "Expiry",
                "days": days_to_expiry,
                "severity": "HIGH",
                "warning": "🔴 Expiry in {} day(s) — extreme theta decay + IV crush risk".format(days_to_expiry)
            })
        elif days_to_expiry <= 5:
            risks.append({
                "event": "Near Expiry",
                "days": days_to_expiry,
                "severity": "MEDIUM",
                "warning": "🟡 {} days to expiry — accelerating theta decay".format(days_to_expiry)
            })

        # Custom events
        if events:
            for event in events:
                event_days = event.get("days_away", 999)
                if event_days <= 1:
                    risks.append({
                        "event": event.get("name", "Unknown"),
                        "days": event_days,
                        "severity": "HIGH",
                        "warning": f"🔴 {event['name']} tomorrow — IV likely to drop post-event"
                    })

        has_risk = any(r["severity"] == "HIGH" for r in risks)

        return {
            "has_crush_risk": has_risk,
            "risks": risks,
            "recommendation": "AVOID BUYING" if has_risk else "OK TO BUY"
        }

    def recommend_expiry(self, trade_type: str = "INTRADAY") -> Dict:
        """
        Recommend optimal expiry based on trade type.
        """
        if trade_type == "INTRADAY":
            return {
                "recommended": "CURRENT_WEEK",
                "reason": "Weekly expiry for intraday — maximum gamma, fast premium movement",
                "min_days": 1,
                "max_days": 5,
                "ideal_days": 2
            }
        elif trade_type == "SWING":
            return {
                "recommended": "NEXT_WEEK",
                "reason": "Next week expiry for swing — balanced theta/gamma",
                "min_days": 5,
                "max_days": 14,
                "ideal_days": 8
            }
        else:  # POSITIONAL
            return {
                "recommended": "MONTHLY",
                "reason": "Monthly expiry for positional — lower theta decay per day",
                "min_days": 14,
                "max_days": 35,
                "ideal_days": 21
            }

    def theta_decay_warning(self, premium: float, theta: float) -> Dict:
        """
        Warn if daily theta decay is too high relative to premium.
        """
        if premium <= 0:
            return {"warning": False}

        daily_decay_pct = abs(theta / premium) * 100

        return {
            "daily_decay_pct": round(daily_decay_pct, 2),
            "premium": premium,
            "theta": theta,
            "warning": daily_decay_pct > 5,
            "severity": "HIGH" if daily_decay_pct > 10 else ("MEDIUM" if daily_decay_pct > 5 else "LOW"),
            "message": f"{'🔴' if daily_decay_pct > 10 else '🟡' if daily_decay_pct > 5 else '🟢'} Daily decay: {daily_decay_pct:.1f}% of premium"
        }

    def get_full_analysis(self, spot: float, strike: float, premium: float,
                          days_to_expiry: int, option_type: str = "CE",
                          historical_ivs: List[float] = None) -> Dict:
        """
        Comprehensive Greeks + IV analysis for a single option.
        """
        # Calculate IV from market premium
        iv = self.calculate_iv(premium, spot, strike, days_to_expiry, option_type)

        # Calculate Greeks
        greeks = self.calculate_greeks(spot, strike, days_to_expiry, iv, option_type)

        # IV Analysis
        iv_analysis = self.analyze_iv(iv, historical_ivs)

        # IV Crush risk
        crush_risk = self.detect_iv_crush_risk(days_to_expiry)

        # Theta warning
        theta_warn = self.theta_decay_warning(premium, greeks["theta"])

        # Buying suitability score (0-100)
        score = 50
        if iv_analysis["favorable_for_buying"]:
            score += 15
        if abs(greeks["delta"]) >= 0.3 and abs(greeks["delta"]) <= 0.5:
            score += 15  # Sweet spot delta
        if not crush_risk["has_crush_risk"]:
            score += 10
        if not theta_warn["warning"]:
            score += 10
        score = min(100, max(0, score))

        return {
            "greeks": greeks,
            "iv_analysis": iv_analysis,
            "crush_risk": crush_risk,
            "theta_warning": theta_warn,
            "buying_score": score,
            "recommendation": "BUY" if score >= 70 else ("WATCH" if score >= 50 else "AVOID"),
        }


# ========================
#  STANDALONE TEST
# ========================
if __name__ == "__main__":
    analyzer = GreeksAnalyzer()

    # Test: NIFTY 24800 CE, 3 days to expiry, IV 15%
    greeks = analyzer.calculate_greeks(
        spot=24800,
        strike=24800,
        days_to_expiry=3,
        iv=0.15,
        option_type="CE"
    )
    print("=== GREEKS ===")
    for k, v in greeks.items():
        print(f"  {k}: {v}")

    # Test: Full analysis
    analysis = analyzer.get_full_analysis(
        spot=24800,
        strike=24800,
        premium=120,
        days_to_expiry=3,
        option_type="CE"
    )
    print("\n=== FULL ANALYSIS ===")
    print(f"  Buying Score: {analysis['buying_score']}")
    print(f"  Recommendation: {analysis['recommendation']}")
    print(f"  IV: {analysis['iv_analysis']['current_iv']}%")
    print(f"  IV Percentile: {analysis['iv_analysis']['iv_percentile']}")
    print(f"  Delta: {analysis['greeks']['delta']}")
    print(f"  Theta: {analysis['greeks']['theta']}")
