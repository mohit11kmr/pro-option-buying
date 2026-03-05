"""
Nifty 50 Options Buying Strategy Engine
========================================
Professional multi-confirmation entry/exit system for NIFTY options buying.

Entry requires ALL conditions to align:
  - SuperTrend direction matches trade bias
  - VWAP crossover confirmation
  - RSI not in overbought/oversold extremes
  - EMA ribbon alignment (9, 21, 55)
  - Volume spike > 1.5x average
  - ADX > 20 (trending market)
  - AI signal confidence > 60%

Risk management:
  - Max 2% capital per trade
  - Max 3 open positions
  - No trades in last 30 min of market
  - Skip low-IV environment (IV < 12)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class SetupQuality(Enum):
    A_PLUS = "A+"      # All conditions perfect
    A = "A"            # 6/7 conditions met
    B = "B"            # 5/7 conditions met
    C = "C"            # Below threshold — skip
    NO_TRADE = "NO_TRADE"


class OptionsBuyingStrategy:
    """
    Professional Nifty 50 options buying strategy with multi-indicator
    confirmation, dynamic risk management, and trade journaling.
    """

    def __init__(self, config: Dict = None):
        # --- Default configuration ---
        self.config = {
            # Risk Management
            "max_risk_per_trade_pct": 2.0,       # Max 2% of capital per trade
            "max_open_positions": 3,
            "max_daily_loss_pct": 5.0,           # Stop trading after 5% daily loss
            "initial_capital": 200000,

            # Entry Thresholds
            "min_confidence": 60,                 # Minimum AI confidence to enter
            "min_adx": 20,                        # ADX > 20 = trending
            "volume_spike_multiplier": 1.5,       # Volume > 1.5x avg
            "rsi_overbought": 75,
            "rsi_oversold": 25,
            "min_iv_percentile": 12,              # Skip if IV < 12

            # Exit Rules
            "target_pct": 40,                     # Target: 40% premium gain
            "stoploss_pct": 25,                   # SL: 25% premium loss
            "trailing_stop_activation_pct": 20,   # Activate trailing after 20% gain
            "trailing_stop_pct": 10,              # Trail by 10% from peak
            "time_based_exit_mins": 45,           # Exit if no profit in 45 mins
            "no_trade_before_close_mins": 30,     # No new trades 30 min before close

            # SuperTrend
            "supertrend_period": 10,
            "supertrend_multiplier": 3.0,

            # EMA Ribbon
            "ema_fast": 9,
            "ema_mid": 21,
            "ema_slow": 55,

            # VWAP
            "vwap_band_std": 1.5,
        }
        if config:
            self.config.update(config)

        # State
        self.open_positions: List[Dict] = []
        self.trade_journal: List[Dict] = []
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0

    # ========================
    #  INDICATOR CALCULATIONS
    # ========================

    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate SuperTrend indicator."""
        period = self.config["supertrend_period"]
        multiplier = self.config["supertrend_multiplier"]

        hl2 = (df['high'] + df['low']) / 2

        # ATR calculation
        tr = pd.DataFrame()
        tr['hl'] = df['high'] - df['low']
        tr['hc'] = abs(df['high'] - df['close'].shift(1))
        tr['lc'] = abs(df['low'] - df['close'].shift(1))
        tr['tr'] = tr[['hl', 'hc', 'lc']].max(axis=1)
        atr = tr['tr'].rolling(window=period).mean()

        # Upper and lower bands
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        supertrend.iloc[0] = upper_band.iloc[0]
        direction.iloc[0] = 1  # 1 = uptrend, -1 = downtrend

        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i - 1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i - 1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                if direction.iloc[i - 1] == 1:
                    supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i - 1])
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i - 1])
                    direction.iloc[i] = -1

                if direction.iloc[i] == 1 and df['close'].iloc[i] < supertrend.iloc[i]:
                    direction.iloc[i] = -1
                elif direction.iloc[i] == -1 and df['close'].iloc[i] > supertrend.iloc[i]:
                    direction.iloc[i] = 1

        df['supertrend'] = supertrend
        df['supertrend_direction'] = direction
        return df

    def _calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP and bands."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cum_vol = df['volume'].cumsum()
        cum_tp_vol = (typical_price * df['volume']).cumsum()

        df['vwap'] = cum_tp_vol / cum_vol

        # VWAP bands
        squared_diff = ((typical_price - df['vwap']) ** 2 * df['volume']).cumsum()
        vwap_std = np.sqrt(squared_diff / cum_vol)
        band_mult = self.config["vwap_band_std"]
        df['vwap_upper'] = df['vwap'] + band_mult * vwap_std
        df['vwap_lower'] = df['vwap'] - band_mult * vwap_std

        return df

    def _calculate_ema_ribbon(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA ribbon (9, 21, 55)."""
        df['ema_fast'] = df['close'].ewm(span=self.config["ema_fast"], adjust=False).mean()
        df['ema_mid'] = df['close'].ewm(span=self.config["ema_mid"], adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config["ema_slow"], adjust=False).mean()
        return df

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI."""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.inf)
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate ADX (Average Directional Index)."""
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()

        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        tr = pd.DataFrame()
        tr['hl'] = df['high'] - df['low']
        tr['hc'] = abs(df['high'] - df['close'].shift(1))
        tr['lc'] = abs(df['low'] - df['close'].shift(1))
        atr = tr[['hl', 'hc', 'lc']].max(axis=1).rolling(window=period).mean()

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.inf)
        df['adx'] = dx.rolling(window=period).mean()
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        return df

    def _calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate On-Balance Volume."""
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv
        return df

    def _calculate_stochastic_rsi(self, df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """Calculate Stochastic RSI."""
        rsi = df['rsi'] if 'rsi' in df.columns else None
        if rsi is None:
            df = self._calculate_rsi(df, period)
            rsi = df['rsi']

        rsi_min = rsi.rolling(window=period).min()
        rsi_max = rsi.rolling(window=period).max()
        rsi_range = rsi_max - rsi_min

        stoch_rsi = ((rsi - rsi_min) / rsi_range.replace(0, np.inf)) * 100
        df['stoch_rsi_k'] = stoch_rsi.rolling(window=smooth_k).mean()
        df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=smooth_d).mean()
        return df

    def _calculate_volume_profile(self, df: pd.DataFrame) -> Dict:
        """Calculate volume profile — avg volume and spike detection."""
        avg_vol = df['volume'].rolling(window=20).mean()
        current_vol = df['volume'].iloc[-1]
        spike = current_vol / avg_vol.iloc[-1] if avg_vol.iloc[-1] > 0 else 1.0

        return {
            "current_volume": float(current_vol),
            "avg_volume": float(avg_vol.iloc[-1]),
            "volume_spike": float(spike),
            "is_volume_spike": spike > self.config["volume_spike_multiplier"]
        }

    # ========================
    #  CORE ANALYSIS
    # ========================

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all indicators to price data."""
        df = df.copy()
        df = self._calculate_supertrend(df)
        df = self._calculate_vwap(df)
        df = self._calculate_ema_ribbon(df)
        df = self._calculate_rsi(df)
        df = self._calculate_adx(df)
        df = self._calculate_obv(df)
        df = self._calculate_stochastic_rsi(df)
        return df

    def _check_entry_conditions(self, df: pd.DataFrame, ai_signal: Dict = None) -> Dict:
        """
        Check all 7 entry conditions and return detailed breakdown.
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        conditions = {}

        # 1. SuperTrend Direction
        st_dir = int(latest.get('supertrend_direction', 0))
        conditions["supertrend"] = {
            "met": st_dir != 0,
            "direction": "BULLISH" if st_dir == 1 else "BEARISH",
            "value": st_dir,
            "label": "SuperTrend ↑" if st_dir == 1 else "SuperTrend ↓"
        }

        # 2. VWAP Crossover
        price = latest['close']
        vwap = latest.get('vwap', price)
        vwap_cross_bull = price > vwap and prev['close'] <= prev.get('vwap', prev['close'])
        vwap_cross_bear = price < vwap and prev['close'] >= prev.get('vwap', prev['close'])
        vwap_above = price > vwap
        conditions["vwap"] = {
            "met": vwap_cross_bull or vwap_cross_bear or vwap_above,
            "above_vwap": vwap_above,
            "crossover_bullish": vwap_cross_bull,
            "crossover_bearish": vwap_cross_bear,
            "price": float(price),
            "vwap": float(vwap),
            "label": f"Price {'>' if vwap_above else '<'} VWAP ({vwap:.0f})"
        }

        # 3. RSI Zone
        rsi = float(latest.get('rsi', 50))
        rsi_ok = self.config["rsi_oversold"] < rsi < self.config["rsi_overbought"]
        conditions["rsi"] = {
            "met": rsi_ok,
            "value": rsi,
            "zone": "OVERBOUGHT" if rsi >= self.config["rsi_overbought"] else (
                "OVERSOLD" if rsi <= self.config["rsi_oversold"] else "NORMAL"
            ),
            "label": f"RSI {rsi:.1f}"
        }

        # 4. EMA Ribbon Alignment
        ema_f = float(latest.get('ema_fast', 0))
        ema_m = float(latest.get('ema_mid', 0))
        ema_s = float(latest.get('ema_slow', 0))
        bullish_ribbon = ema_f > ema_m > ema_s
        bearish_ribbon = ema_f < ema_m < ema_s
        conditions["ema_ribbon"] = {
            "met": bullish_ribbon or bearish_ribbon,
            "bullish": bullish_ribbon,
            "bearish": bearish_ribbon,
            "fast": ema_f,
            "mid": ema_m,
            "slow": ema_s,
            "label": "EMA Ribbon " + ("↑ Aligned" if bullish_ribbon else ("↓ Aligned" if bearish_ribbon else "Mixed"))
        }

        # 5. Volume Spike
        vol_profile = self._calculate_volume_profile(df)
        conditions["volume"] = {
            "met": vol_profile["is_volume_spike"],
            "spike": vol_profile["volume_spike"],
            "current": vol_profile["current_volume"],
            "average": vol_profile["avg_volume"],
            "label": f"Volume {vol_profile['volume_spike']:.1f}x avg"
        }

        # 6. ADX Trending
        adx = float(latest.get('adx', 0))
        conditions["adx"] = {
            "met": adx > self.config["min_adx"],
            "value": adx,
            "trending": adx > self.config["min_adx"],
            "label": f"ADX {adx:.1f}"
        }

        # 7. AI Signal Confidence
        confidence = 50
        ai_recommendation = "HOLD"
        if ai_signal:
            confidence = ai_signal.get("confidence", 50)
            ai_recommendation = ai_signal.get("recommendation", "HOLD")
        conditions["ai_signal"] = {
            "met": confidence >= self.config["min_confidence"],
            "confidence": confidence,
            "recommendation": ai_recommendation,
            "label": f"AI: {ai_recommendation} ({confidence}%)"
        }

        return conditions

    def _determine_direction(self, conditions: Dict) -> TradeDirection:
        """Determine overall trade direction from conditions."""
        bullish_signals = 0
        bearish_signals = 0

        if conditions["supertrend"]["direction"] == "BULLISH":
            bullish_signals += 2
        else:
            bearish_signals += 2

        if conditions["vwap"]["above_vwap"]:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if conditions["ema_ribbon"]["bullish"]:
            bullish_signals += 2
        elif conditions["ema_ribbon"]["bearish"]:
            bearish_signals += 2

        rsi = conditions["rsi"]["value"]
        if rsi > 55:
            bullish_signals += 1
        elif rsi < 45:
            bearish_signals += 1

        ai_rec = conditions["ai_signal"]["recommendation"]
        if "BUY" in ai_rec:
            bullish_signals += 2
        elif "SELL" in ai_rec:
            bearish_signals += 2

        if bullish_signals > bearish_signals + 2:
            return TradeDirection.BULLISH
        elif bearish_signals > bullish_signals + 2:
            return TradeDirection.BEARISH
        return TradeDirection.NEUTRAL

    def _grade_setup(self, conditions: Dict) -> SetupQuality:
        """Grade the setup quality based on how many conditions are met."""
        met_count = sum(1 for c in conditions.values() if c.get("met", False))
        total = len(conditions)

        if met_count == total:
            return SetupQuality.A_PLUS
        elif met_count >= total - 1:
            return SetupQuality.A
        elif met_count >= total - 2:
            return SetupQuality.B
        elif met_count >= total - 3:
            return SetupQuality.C
        return SetupQuality.NO_TRADE

    # ========================
    #  MAIN STRATEGY SIGNAL
    # ========================

    def generate_signal(self, df: pd.DataFrame, ai_signal: Dict = None,
                        iv_data: Dict = None, current_time: datetime = None) -> Dict:
        """
        Generate a complete options buying signal.

        Returns:
            Dict with recommendation, direction, setup quality, entry/exit levels,
            risk parameters, and full indicator breakdown.
        """
        if current_time is None:
            current_time = datetime.now()

        # Prepare data with all indicators
        df = self.prepare_data(df)

        # ---- Pre-checks ----
        # No trade in last 30 min
        market_close = current_time.replace(hour=15, minute=30, second=0)
        cutoff = market_close - timedelta(minutes=self.config["no_trade_before_close_mins"])
        if current_time.time() >= cutoff.time():
            return self._no_trade_signal("Market closing soon — no new entries", current_time)

        # Check max daily loss
        if abs(self.daily_pnl) >= (self.config["initial_capital"] * self.config["max_daily_loss_pct"] / 100):
            return self._no_trade_signal("Daily loss limit reached", current_time)

        # Check max open positions
        if len(self.open_positions) >= self.config["max_open_positions"]:
            return self._no_trade_signal("Max open positions reached", current_time)

        # Check IV
        if iv_data:
            iv_pct = iv_data.get("iv_percentile", 50)
            if iv_pct < self.config["min_iv_percentile"]:
                return self._no_trade_signal(f"IV too low ({iv_pct}%) — premiums not worth it", current_time)

        # ---- Check all entry conditions ----
        conditions = self._check_entry_conditions(df, ai_signal)
        direction = self._determine_direction(conditions)
        quality = self._grade_setup(conditions)

        # Build signal
        latest = df.iloc[-1]
        price = float(latest['close'])

        # Entry/Exit levels
        atr = float(latest.get('supertrend', price) - price) if latest.get('supertrend_direction', 0) == 1 else float(price - latest.get('supertrend', price))
        atr = max(abs(atr), 20)  # min ATR of 20 pts

        if direction == TradeDirection.BULLISH:
            option_type = "CE"
            entry_zone = (price - 10, price + 5)
            sl_nifty = price - atr
            target_nifty = price + atr * 1.5
        elif direction == TradeDirection.BEARISH:
            option_type = "PE"
            entry_zone = (price - 5, price + 10)
            sl_nifty = price + atr
            target_nifty = price - atr * 1.5
        else:
            option_type = "NONE"
            entry_zone = (price, price)
            sl_nifty = price
            target_nifty = price

        # Risk calculation
        capital = self.config["initial_capital"]
        risk_amount = capital * self.config["max_risk_per_trade_pct"] / 100
        lot_size = 25  # NIFTY lot size

        # Should we trade?
        tradeable = quality in (SetupQuality.A_PLUS, SetupQuality.A) and direction != TradeDirection.NEUTRAL
        recommendation = "WAIT"
        if tradeable:
            recommendation = f"BUY {option_type}"
        elif quality == SetupQuality.B:
            recommendation = f"WATCH {option_type}"

        signal = {
            "timestamp": current_time.isoformat(),
            "recommendation": recommendation,
            "direction": direction.value,
            "option_type": option_type,
            "setup_quality": quality.value,
            "nifty_price": price,

            # Entry/Exit
            "entry_zone": {
                "low": float(entry_zone[0]),
                "high": float(entry_zone[1])
            },
            "stoploss_nifty": float(sl_nifty),
            "target_nifty": float(target_nifty),
            "risk_reward_ratio": round(abs(target_nifty - price) / max(abs(price - sl_nifty), 1), 2),

            # Premium levels
            "premium_target_pct": self.config["target_pct"],
            "premium_sl_pct": self.config["stoploss_pct"],
            "trailing_stop": {
                "activation_pct": self.config["trailing_stop_activation_pct"],
                "trail_pct": self.config["trailing_stop_pct"]
            },

            # Risk
            "risk_per_trade": float(risk_amount),
            "lot_size": lot_size,
            "max_lots": max(1, int(risk_amount / (atr * lot_size))),

            # Indicator breakdown
            "conditions": conditions,
            "conditions_met": sum(1 for c in conditions.values() if c.get("met", False)),
            "conditions_total": len(conditions),

            # Indicator values
            "indicators": {
                "supertrend": float(latest.get('supertrend', 0)),
                "supertrend_direction": int(latest.get('supertrend_direction', 0)),
                "vwap": float(latest.get('vwap', 0)),
                "rsi": float(latest.get('rsi', 50)),
                "adx": float(latest.get('adx', 0)),
                "ema_fast": float(latest.get('ema_fast', 0)),
                "ema_mid": float(latest.get('ema_mid', 0)),
                "ema_slow": float(latest.get('ema_slow', 0)),
                "stoch_rsi_k": float(latest.get('stoch_rsi_k', 50)),
                "stoch_rsi_d": float(latest.get('stoch_rsi_d', 50)),
                "obv": float(latest.get('obv', 0)),
            },

            # Summary reasons
            "reasons": self._generate_reasons(conditions, direction, quality),
        }

        return signal

    def _no_trade_signal(self, reason: str, current_time: datetime) -> Dict:
        """Generate a NO_TRADE signal."""
        return {
            "timestamp": current_time.isoformat(),
            "recommendation": "NO_TRADE",
            "direction": TradeDirection.NEUTRAL.value,
            "option_type": "NONE",
            "setup_quality": SetupQuality.NO_TRADE.value,
            "reason": reason,
            "reasons": [reason],
            "conditions": {},
            "conditions_met": 0,
            "conditions_total": 7,
            "indicators": {},
        }

    def _generate_reasons(self, conditions: Dict, direction: TradeDirection, quality: SetupQuality) -> List[str]:
        """Generate human-readable reasons for the signal."""
        reasons = []

        if quality in (SetupQuality.A_PLUS, SetupQuality.A):
            reasons.append(f"🟢 Setup Quality: {quality.value} — Strong entry signal")
        elif quality == SetupQuality.B:
            reasons.append(f"🟡 Setup Quality: {quality.value} — Watch for confirmation")
        else:
            reasons.append(f"🔴 Setup Quality: {quality.value} — Not tradeable")

        reasons.append(f"📈 Direction: {direction.value}")

        for key, cond in conditions.items():
            icon = "✅" if cond.get("met") else "❌"
            reasons.append(f"{icon} {cond.get('label', key)}")

        return reasons

    # ========================
    #  POSITION MANAGEMENT
    # ========================

    def check_exit_conditions(self, position: Dict, current_premium: float,
                              current_time: datetime = None) -> Dict:
        """
        Check if an open position should be exited.

        Returns exit signal with reason.
        """
        if current_time is None:
            current_time = datetime.now()

        entry_premium = position.get("entry_premium", 0)
        if entry_premium <= 0:
            return {"should_exit": False}

        pnl_pct = ((current_premium - entry_premium) / entry_premium) * 100
        peak_premium = position.get("peak_premium", entry_premium)

        # Update peak
        if current_premium > peak_premium:
            position["peak_premium"] = current_premium
            peak_premium = current_premium

        # 1. Target hit
        if pnl_pct >= self.config["target_pct"]:
            return {
                "should_exit": True,
                "reason": f"🎯 Target hit! P&L: +{pnl_pct:.1f}%",
                "exit_type": "TARGET",
                "pnl_pct": pnl_pct
            }

        # 2. Stop loss hit
        if pnl_pct <= -self.config["stoploss_pct"]:
            return {
                "should_exit": True,
                "reason": f"🛑 Stop loss hit! P&L: {pnl_pct:.1f}%",
                "exit_type": "STOPLOSS",
                "pnl_pct": pnl_pct
            }

        # 3. Trailing stop
        if pnl_pct >= self.config["trailing_stop_activation_pct"]:
            drawdown_from_peak = ((peak_premium - current_premium) / peak_premium) * 100
            if drawdown_from_peak >= self.config["trailing_stop_pct"]:
                return {
                    "should_exit": True,
                    "reason": f"📉 Trailing stop triggered. Peak: {peak_premium:.0f}, Current: {current_premium:.0f}",
                    "exit_type": "TRAILING_STOP",
                    "pnl_pct": pnl_pct
                }

        # 4. Time-based exit
        entry_time = position.get("entry_time")
        if entry_time:
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time)
            elapsed = (current_time - entry_time).total_seconds() / 60
            if elapsed >= self.config["time_based_exit_mins"] and pnl_pct <= 0:
                return {
                    "should_exit": True,
                    "reason": f"⏰ Time exit: {elapsed:.0f} min elapsed, P&L: {pnl_pct:.1f}%",
                    "exit_type": "TIME_EXIT",
                    "pnl_pct": pnl_pct
                }

        # 5. Market close exit
        market_close = current_time.replace(hour=15, minute=25, second=0)
        if current_time.time() >= market_close.time():
            return {
                "should_exit": True,
                "reason": f"🔔 Market closing exit. P&L: {pnl_pct:.1f}%",
                "exit_type": "MARKET_CLOSE",
                "pnl_pct": pnl_pct
            }

        return {
            "should_exit": False,
            "pnl_pct": pnl_pct,
            "peak_premium": peak_premium
        }

    # ========================
    #  TRADE JOURNAL
    # ========================

    def record_trade(self, trade: Dict) -> None:
        """Record a trade in the journal."""
        trade["id"] = len(self.trade_journal) + 1
        trade["recorded_at"] = datetime.now().isoformat()
        self.trade_journal.append(trade)

        # Update stats
        self.total_trades += 1
        pnl = trade.get("pnl", 0)
        if pnl > 0:
            self.winning_trades += 1
        self.daily_pnl += pnl

    def get_journal(self, limit: int = 50) -> List[Dict]:
        """Get recent trade journal entries."""
        return self.trade_journal[-limit:]

    def get_stats(self) -> Dict:
        """Get strategy performance statistics."""
        if self.total_trades == 0:
            return {"total_trades": 0, "win_rate": 0, "daily_pnl": 0}

        pnls = [t.get("pnl", 0) for t in self.trade_journal]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": round(self.winning_trades / self.total_trades * 100, 1),
            "daily_pnl": round(self.daily_pnl, 2),
            "total_pnl": round(sum(pnls), 2),
            "avg_win": round(np.mean(wins), 2) if wins else 0,
            "avg_loss": round(np.mean(losses), 2) if losses else 0,
            "largest_win": round(max(wins), 2) if wins else 0,
            "largest_loss": round(min(losses), 2) if losses else 0,
            "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses else float('inf'),
        }

    def save_journal(self, filepath: str = "trade_journal.json") -> None:
        """Save journal to file."""
        with open(filepath, 'w') as f:
            json.dump({
                "trades": self.trade_journal,
                "stats": self.get_stats()
            }, f, indent=2)

    def load_journal(self, filepath: str = "trade_journal.json") -> None:
        """Load journal from file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    self.trade_journal = data.get("trades", [])
                    self.total_trades = len(self.trade_journal)
                    self.winning_trades = sum(1 for t in self.trade_journal if t.get("pnl", 0) > 0)
        except Exception as e:
            logger.error(f"Error loading journal: {e}")


# ========================
#  STANDALONE TEST
# ========================
if __name__ == "__main__":
    np.random.seed(42)

    # Generate sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    base = 24800
    closes = []
    for i in range(100):
        base += np.random.uniform(-15, 16)
        closes.append(base)

    df = pd.DataFrame({
        'open': [c + np.random.uniform(-10, 10) for c in closes],
        'high': [c + np.random.uniform(5, 30) for c in closes],
        'low': [c - np.random.uniform(5, 30) for c in closes],
        'close': closes,
        'volume': [np.random.uniform(500000, 3000000) for _ in range(100)]
    }, index=dates)

    strategy = OptionsBuyingStrategy()
    signal = strategy.generate_signal(df, ai_signal={
        "recommendation": "STRONG_BUY",
        "confidence": 75,
        "score": 82
    })

    print(json.dumps(signal, indent=2, default=str))
