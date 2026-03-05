"""
Smart Strike Price Selector
=============================
Recommends optimal strike prices for Nifty options buying based on
moneyness, OI analysis, IV skew, spread, and support/resistance levels.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class StrikeSelector:
    """
    Smart strike selection for Nifty options buying.
    Ranks strikes by multiple criteria to find the best option to buy.
    """

    # NIFTY strike gap
    STRIKE_GAP = 50
    LOT_SIZE = 25

    def __init__(self, config: Dict = None):
        self.config = {
            "preferred_delta_min": 0.30,
            "preferred_delta_max": 0.55,
            "max_spread_pct": 3.0,          # Max bid-ask spread %
            "min_oi": 50000,                # Min OI filter
            "max_premium_pct": 1.5,          # Max premium as % of spot
            "strikes_to_analyze": 10,        # Number of strikes to analyze
        }
        if config:
            self.config.update(config)

    # ========================
    #  STRIKE GENERATION
    # ========================

    def get_strike_range(self, spot: float, option_type: str = "CE",
                         num_strikes: int = None) -> List[float]:
        """
        Generate a range of relevant strikes around the spot price.
        """
        if num_strikes is None:
            num_strikes = self.config["strikes_to_analyze"]

        atm_strike = round(spot / self.STRIKE_GAP) * self.STRIKE_GAP

        if option_type == "CE":
            # For calls: ATM + a few ITM + more OTM
            strikes = [atm_strike + (i * self.STRIKE_GAP) for i in range(-3, num_strikes - 3)]
        else:
            # For puts: ATM + a few ITM + more OTM
            strikes = [atm_strike + (i * self.STRIKE_GAP) for i in range(-(num_strikes - 3), 4)]

        return sorted(strikes)

    def classify_moneyness(self, spot: float, strike: float,
                           option_type: str = "CE") -> Dict:
        """Classify a strike as ITM, ATM, or OTM with details."""
        diff = spot - strike
        diff_pct = (diff / spot) * 100

        if option_type == "CE":
            if diff > self.STRIKE_GAP * 0.5:
                label = "ITM"
                distance = int(diff / self.STRIKE_GAP)
            elif diff < -self.STRIKE_GAP * 0.5:
                label = "OTM"
                distance = int(abs(diff) / self.STRIKE_GAP)
            else:
                label = "ATM"
                distance = 0
        else:  # PE
            if diff < -self.STRIKE_GAP * 0.5:
                label = "ITM"
                distance = int(abs(diff) / self.STRIKE_GAP)
            elif diff > self.STRIKE_GAP * 0.5:
                label = "OTM"
                distance = int(diff / self.STRIKE_GAP)
            else:
                label = "ATM"
                distance = 0

        return {
            "label": label,
            "distance_strikes": distance,
            "distance_points": abs(diff),
            "distance_pct": round(abs(diff_pct), 2)
        }

    # ========================
    #  STRIKE SCORING
    # ========================

    def score_strike(self, spot: float, strike: float, option_type: str,
                     premium: float = None, oi: float = None,
                     iv: float = None, bid: float = None, ask: float = None,
                     delta: float = None, oi_change: float = None) -> Dict:
        """
        Score a strike on multiple criteria (0-100).
        """
        scores = {}
        total_weight = 0
        weighted_sum = 0

        moneyness = self.classify_moneyness(spot, strike, option_type)

        # 1. Moneyness Score (weight: 25)
        weight = 25
        if moneyness["label"] == "ATM":
            score = 90
        elif moneyness["distance_strikes"] == 1:
            score = 80 if moneyness["label"] == "ITM" else 75
        elif moneyness["distance_strikes"] == 2:
            score = 60 if moneyness["label"] == "ITM" else 55
        else:
            score = max(20, 50 - moneyness["distance_strikes"] * 10)

        scores["moneyness"] = {"score": score, "weight": weight, "detail": moneyness["label"]}
        weighted_sum += score * weight
        total_weight += weight

        # 2. Delta Score (weight: 20) — Sweet spot 0.30-0.50
        if delta is not None:
            weight = 20
            abs_delta = abs(delta)
            if self.config["preferred_delta_min"] <= abs_delta <= self.config["preferred_delta_max"]:
                score = 95
            elif abs_delta > 0.55:
                score = 70  # Deep ITM, less leverage
            elif abs_delta > 0.25:
                score = 75
            elif abs_delta > 0.15:
                score = 50
            else:
                score = 30  # Very far OTM
            scores["delta"] = {"score": score, "weight": weight, "detail": f"Δ={delta:.3f}"}
            weighted_sum += score * weight
            total_weight += weight

        # 3. OI Score (weight: 15) — Higher OI = more liquid
        if oi is not None:
            weight = 15
            if oi >= 500000:
                score = 95
            elif oi >= 200000:
                score = 85
            elif oi >= self.config["min_oi"]:
                score = 70
            elif oi >= 20000:
                score = 50
            else:
                score = 20
            scores["oi"] = {"score": score, "weight": weight, "detail": f"OI={oi:,.0f}"}
            weighted_sum += score * weight
            total_weight += weight

        # 4. OI Buildup Score (weight: 10)
        if oi_change is not None and oi is not None and oi > 0:
            weight = 10
            oi_change_pct = (oi_change / oi) * 100
            if oi_change_pct > 10:
                score = 90  # Big OI buildup = institutional interest
            elif oi_change_pct > 5:
                score = 75
            elif oi_change_pct > 0:
                score = 60
            else:
                score = 40  # OI unwinding
            scores["oi_buildup"] = {"score": score, "weight": weight, "detail": f"ΔOI={oi_change_pct:.1f}%"}
            weighted_sum += score * weight
            total_weight += weight

        # 5. Spread Score (weight: 15) — Tighter spread = better
        if bid is not None and ask is not None and bid > 0:
            weight = 15
            spread_pct = ((ask - bid) / bid) * 100
            if spread_pct <= 1:
                score = 95
            elif spread_pct <= 2:
                score = 80
            elif spread_pct <= self.config["max_spread_pct"]:
                score = 60
            elif spread_pct <= 5:
                score = 40
            else:
                score = 15
            scores["spread"] = {"score": score, "weight": weight, "detail": f"Spread={spread_pct:.1f}%"}
            weighted_sum += score * weight
            total_weight += weight

        # 6. IV Score (weight: 10) — Lower IV = cheaper premium
        if iv is not None:
            weight = 10
            iv_pct = iv * 100 if iv < 1 else iv
            if iv_pct <= 12:
                score = 95  # Very cheap
            elif iv_pct <= 15:
                score = 85
            elif iv_pct <= 20:
                score = 70
            elif iv_pct <= 30:
                score = 50
            else:
                score = 25  # Expensive
            scores["iv"] = {"score": score, "weight": weight, "detail": f"IV={iv_pct:.1f}%"}
            weighted_sum += score * weight
            total_weight += weight

        # 7. Premium Affordability (weight: 5)
        if premium is not None:
            weight = 5
            premium_pct = (premium / spot) * 100
            lot_cost = premium * self.LOT_SIZE
            if premium_pct <= 0.5:
                score = 90
            elif premium_pct <= 1.0:
                score = 75
            elif premium_pct <= self.config["max_premium_pct"]:
                score = 55
            else:
                score = 30
            scores["affordability"] = {"score": score, "weight": weight, "detail": f"₹{lot_cost:,.0f}/lot"}
            weighted_sum += score * weight
            total_weight += weight

        # Overall score
        overall = round(weighted_sum / total_weight, 1) if total_weight > 0 else 50

        return {
            "strike": strike,
            "option_type": option_type,
            "overall_score": overall,
            "moneyness": moneyness,
            "scores": scores,
            "premium": premium,
            "lot_cost": round(premium * self.LOT_SIZE, 2) if premium else None,
            "recommendation": "BEST" if overall >= 80 else ("GOOD" if overall >= 65 else ("OK" if overall >= 50 else "AVOID"))
        }

    # ========================
    #  SMART RECOMMENDATION
    # ========================

    def recommend_strikes(self, spot: float, option_type: str,
                          strikes_data: List[Dict] = None,
                          support: float = None, resistance: float = None) -> Dict:
        """
        Recommend the best strikes to buy.

        Args:
            spot: Current NIFTY price
            option_type: "CE" or "PE"
            strikes_data: List of dicts with strike, premium, oi, iv, bid, ask, delta, oi_change
            support: Nearest support level
            resistance: Nearest resistance level

        Returns:
            Ranked list of strike recommendations
        """
        if strikes_data is None:
            # Generate synthetic data for demo
            strikes = self.get_strike_range(spot, option_type)
            strikes_data = []
            for strike in strikes:
                moneyness = self.classify_moneyness(spot, strike, option_type)
                base_premium = max(5, abs(spot - strike) * 0.4 + np.random.uniform(20, 100))
                if moneyness["label"] == "OTM":
                    base_premium *= 0.4
                strikes_data.append({
                    "strike": strike,
                    "premium": round(base_premium, 2),
                    "oi": int(np.random.uniform(30000, 800000)),
                    "iv": round(np.random.uniform(0.10, 0.30), 3),
                    "bid": round(base_premium * 0.98, 2),
                    "ask": round(base_premium * 1.02, 2),
                    "delta": round(np.random.uniform(0.15, 0.75) * (1 if option_type == "CE" else -1), 3),
                    "oi_change": int(np.random.uniform(-50000, 200000)),
                })

        # Score all strikes
        scored = []
        for sd in strikes_data:
            result = self.score_strike(
                spot=spot,
                strike=sd["strike"],
                option_type=option_type,
                premium=sd.get("premium"),
                oi=sd.get("oi"),
                iv=sd.get("iv"),
                bid=sd.get("bid"),
                ask=sd.get("ask"),
                delta=sd.get("delta"),
                oi_change=sd.get("oi_change"),
            )
            scored.append(result)

        # Sort by score (highest first)
        scored.sort(key=lambda x: x["overall_score"], reverse=True)

        # Support/Resistance based adjustment
        sr_suggestion = None
        if support and resistance:
            if option_type == "CE":
                sr_strike = round(support / self.STRIKE_GAP) * self.STRIKE_GAP
                sr_suggestion = f"Support at ₹{support:.0f} — consider {sr_strike} CE for bounce play"
            else:
                sr_strike = round(resistance / self.STRIKE_GAP) * self.STRIKE_GAP
                sr_suggestion = f"Resistance at ₹{resistance:.0f} — consider {sr_strike} PE for rejection play"

        return {
            "spot": spot,
            "option_type": option_type,
            "timestamp": datetime.now().isoformat(),
            "best_strike": scored[0] if scored else None,
            "top_3": scored[:3],
            "all_strikes": scored,
            "sr_suggestion": sr_suggestion,
            "total_analyzed": len(scored),
        }

    def get_optimal_entry(self, spot: float, direction: str,
                          strikes_data: List[Dict] = None) -> Dict:
        """
        Get single optimal entry recommendation.

        Args:
            spot: Current price
            direction: "BULLISH" or "BEARISH"
            strikes_data: Optional market data

        Returns:
            Complete trade setup recommendation
        """
        option_type = "CE" if direction == "BULLISH" else "PE"

        result = self.recommend_strikes(spot, option_type, strikes_data)
        best = result.get("best_strike")

        if not best:
            return {"recommendation": "NO_SUITABLE_STRIKE", "reason": "No strikes meet criteria"}

        premium = best.get("premium", 0)
        lot_cost = premium * self.LOT_SIZE if premium else 0

        return {
            "direction": direction,
            "option_type": option_type,
            "strike": best["strike"],
            "premium": premium,
            "lot_cost": lot_cost,
            "score": best["overall_score"],
            "moneyness": best["moneyness"]["label"],
            "recommendation": best["recommendation"],
            "scores_breakdown": best["scores"],

            # Trade setup
            "setup": {
                "entry": f"BUY {best['strike']} {option_type} @ ₹{premium:.0f}",
                "lots": 1,
                "capital_required": f"₹{lot_cost:,.0f}",
                "target": f"₹{premium * 1.4:.0f} (+40%)",
                "stoploss": f"₹{premium * 0.75:.0f} (-25%)",
                "risk_reward": "1:1.6",
            }
        }


# ========================
#  STANDALONE TEST
# ========================
if __name__ == "__main__":
    selector = StrikeSelector()
    spot = 24850

    print("=== CE Recommendations ===")
    ce_result = selector.recommend_strikes(spot, "CE")
    for i, strike in enumerate(ce_result["top_3"]):
        print(f"\n  #{i+1}: {strike['strike']} CE")
        print(f"     Score: {strike['overall_score']}")
        print(f"     Moneyness: {strike['moneyness']['label']}")
        print(f"     Recommendation: {strike['recommendation']}")

    print("\n=== Optimal Entry (BULLISH) ===")
    entry = selector.get_optimal_entry(spot, "BULLISH")
    print(f"  {entry['setup']['entry']}")
    print(f"  Capital: {entry['setup']['capital_required']}")
    print(f"  Target: {entry['setup']['target']}")
    print(f"  SL: {entry['setup']['stoploss']}")
