"""
Advanced Technical Indicators for Options Trading
===================================================
Professional-grade indicators for multi-confirmation entry:
SuperTrend, VWAP, EMA Ribbon, ADX, Stochastic RSI, OBV, Market Structure
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


class AdvancedIndicators:
    """
    Collection of advanced technical indicators optimized for
    intraday options trading on NIFTY.
    """

    # ========================
    #  SUPERTREND
    # ========================

    @staticmethod
    def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """
        SuperTrend indicator — trend direction + dynamic stop loss.

        Returns df with columns: supertrend, supertrend_direction (1=up, -1=down)
        """
        df = df.copy()
        hl2 = (df['high'] + df['low']) / 2

        # ATR
        tr = pd.DataFrame()
        tr['hl'] = df['high'] - df['low']
        tr['hc'] = abs(df['high'] - df['close'].shift(1))
        tr['lc'] = abs(df['low'] - df['close'].shift(1))
        tr['tr'] = tr[['hl', 'hc', 'lc']].max(axis=1)
        atr = tr['tr'].rolling(window=period).mean()

        upper = hl2 + (multiplier * atr)
        lower = hl2 - (multiplier * atr)

        st = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        st.iloc[0] = upper.iloc[0]
        direction.iloc[0] = 1

        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper.iloc[i - 1]:
                st.iloc[i] = lower.iloc[i]
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < lower.iloc[i - 1]:
                st.iloc[i] = upper.iloc[i]
                direction.iloc[i] = -1
            else:
                if direction.iloc[i - 1] == 1:
                    st.iloc[i] = max(lower.iloc[i], st.iloc[i - 1])
                    direction.iloc[i] = 1
                else:
                    st.iloc[i] = min(upper.iloc[i], st.iloc[i - 1])
                    direction.iloc[i] = -1

                if direction.iloc[i] == 1 and df['close'].iloc[i] < st.iloc[i]:
                    direction.iloc[i] = -1
                elif direction.iloc[i] == -1 and df['close'].iloc[i] > st.iloc[i]:
                    direction.iloc[i] = 1

        df['supertrend'] = st
        df['supertrend_direction'] = direction
        return df

    # ========================
    #  VWAP
    # ========================

    @staticmethod
    def vwap(df: pd.DataFrame, band_std: float = 1.5) -> pd.DataFrame:
        """
        VWAP with standard deviation bands.

        Returns df with columns: vwap, vwap_upper, vwap_lower
        """
        df = df.copy()
        tp = (df['high'] + df['low'] + df['close']) / 3
        cum_vol = df['volume'].cumsum()
        cum_tp_vol = (tp * df['volume']).cumsum()

        df['vwap'] = cum_tp_vol / cum_vol

        sq_diff = ((tp - df['vwap']) ** 2 * df['volume']).cumsum()
        vwap_std = np.sqrt(sq_diff / cum_vol)

        df['vwap_upper'] = df['vwap'] + band_std * vwap_std
        df['vwap_lower'] = df['vwap'] - band_std * vwap_std

        return df

    # ========================
    #  EMA RIBBON
    # ========================

    @staticmethod
    def ema_ribbon(df: pd.DataFrame, fast: int = 9, mid: int = 21, slow: int = 55) -> pd.DataFrame:
        """
        EMA Ribbon — multiple EMAs for trend strength visualization.

        Returns df with columns: ema_9, ema_21, ema_55, ema_ribbon_bullish, ema_ribbon_bearish
        """
        df = df.copy()
        df['ema_9'] = df['close'].ewm(span=fast, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=mid, adjust=False).mean()
        df['ema_55'] = df['close'].ewm(span=slow, adjust=False).mean()

        df['ema_ribbon_bullish'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_55'])
        df['ema_ribbon_bearish'] = (df['ema_9'] < df['ema_21']) & (df['ema_21'] < df['ema_55'])

        return df

    # ========================
    #  RSI
    # ========================

    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Standard RSI."""
        df = df.copy()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.inf)
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    # ========================
    #  STOCHASTIC RSI
    # ========================

    @staticmethod
    def stochastic_rsi(df: pd.DataFrame, period: int = 14,
                       smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """
        Stochastic RSI — momentum timing indicator.

        Returns df with columns: stoch_rsi_k, stoch_rsi_d
        """
        df = df.copy()
        if 'rsi' not in df.columns:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss.replace(0, np.inf)
            df['rsi'] = 100 - (100 / (1 + rs))

        rsi = df['rsi']
        rsi_min = rsi.rolling(window=period).min()
        rsi_max = rsi.rolling(window=period).max()

        stoch = ((rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.inf)) * 100
        df['stoch_rsi_k'] = stoch.rolling(window=smooth_k).mean()
        df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=smooth_d).mean()

        return df

    # ========================
    #  ADX
    # ========================

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        ADX — Average Directional Index for trend strength.

        Returns df with columns: adx, plus_di, minus_di
        """
        df = df.copy()
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

    # ========================
    #  OBV (On-Balance Volume)
    # ========================

    @staticmethod
    def obv(df: pd.DataFrame) -> pd.DataFrame:
        """On-Balance Volume — volume confirmation."""
        df = df.copy()
        obv_values = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv_values.append(obv_values[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv_values.append(obv_values[-1] - df['volume'].iloc[i])
            else:
                obv_values.append(obv_values[-1])

        df['obv'] = obv_values
        df['obv_ema'] = pd.Series(obv_values).ewm(span=20, adjust=False).mean().values
        return df

    # ========================
    #  BOLLINGER BANDS
    # ========================

    @staticmethod
    def bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """Bollinger Bands with squeeze detection."""
        df = df.copy()
        df['bb_mid'] = df['close'].rolling(window=period).mean()
        rolling_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_mid'] + std_dev * rolling_std
        df['bb_lower'] = df['bb_mid'] - std_dev * rolling_std

        # Bandwidth
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid'] * 100

        # Squeeze: bandwidth below 20-period low → volatility expansion coming
        df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(window=20).quantile(0.2)

        return df

    # ========================
    #  MACD
    # ========================

    @staticmethod
    def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD with histogram."""
        df = df.copy()
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        df['macd_line'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd_line'].ewm(span=signal, adjust=False).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']

        return df

    # ========================
    #  ATR (Average True Range)
    # ========================

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Average True Range."""
        df = df.copy()
        tr = pd.DataFrame()
        tr['hl'] = df['high'] - df['low']
        tr['hc'] = abs(df['high'] - df['close'].shift(1))
        tr['lc'] = abs(df['low'] - df['close'].shift(1))
        df['atr'] = tr[['hl', 'hc', 'lc']].max(axis=1).rolling(window=period).mean()
        return df

    # ========================
    #  MARKET STRUCTURE
    # ========================

    @staticmethod
    def market_structure(df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Detect Higher-Highs/Lower-Lows market structure.

        Returns dict with structure type and pivot points.
        """
        if len(df) < lookback:
            return {"structure": "INSUFFICIENT_DATA", "pivots": []}

        recent = df.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values

        # Find peaks and troughs
        peaks = []
        troughs = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append(highs[i])

            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append(lows[i])

        # Determine structure
        structure = "RANGING"
        if len(peaks) >= 2 and len(troughs) >= 2:
            higher_highs = peaks[-1] > peaks[-2]
            higher_lows = troughs[-1] > troughs[-2]
            lower_highs = peaks[-1] < peaks[-2]
            lower_lows = troughs[-1] < troughs[-2]

            if higher_highs and higher_lows:
                structure = "UPTREND"
            elif lower_highs and lower_lows:
                structure = "DOWNTREND"
            elif higher_highs and lower_lows:
                structure = "EXPANDING"
            elif lower_highs and higher_lows:
                structure = "CONTRACTING"

        return {
            "structure": structure,
            "peaks": peaks,
            "troughs": troughs,
            "latest_high": float(recent['high'].max()),
            "latest_low": float(recent['low'].min()),
        }

    # ========================
    #  SUPPORT / RESISTANCE
    # ========================

    @staticmethod
    def support_resistance(df: pd.DataFrame, num_levels: int = 3) -> Dict:
        """
        Calculate key support and resistance levels using price clustering.
        """
        prices = pd.concat([df['high'], df['low']]).values
        sorted_prices = np.sort(prices)

        # Use price frequency clustering
        hist, bin_edges = np.histogram(sorted_prices, bins=50)
        level_indices = np.argsort(hist)[::-1][:num_levels * 2]
        levels = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in level_indices]

        current = float(df['close'].iloc[-1])
        support = sorted([l for l in levels if l < current], reverse=True)[:num_levels]
        resistance = sorted([l for l in levels if l >= current])[:num_levels]

        return {
            "support": [round(s, 0) for s in support],
            "resistance": [round(r, 0) for r in resistance],
            "current_price": current,
        }

    # ========================
    #  PIVOT POINTS
    # ========================

    @staticmethod
    def pivot_points(df: pd.DataFrame) -> Dict:
        """Calculate Classic Pivot Points from previous session."""
        if len(df) < 2:
            return {}

        prev = df.iloc[-2]
        h = float(prev['high'])
        l = float(prev['low'])
        c = float(prev['close'])

        pp = (h + l + c) / 3
        r1 = 2 * pp - l
        s1 = 2 * pp - h
        r2 = pp + (h - l)
        s2 = pp - (h - l)
        r3 = h + 2 * (pp - l)
        s3 = l - 2 * (h - pp)

        return {
            "pivot": round(pp, 0),
            "r1": round(r1, 0), "r2": round(r2, 0), "r3": round(r3, 0),
            "s1": round(s1, 0), "s2": round(s2, 0), "s3": round(s3, 0),
        }

    # ========================
    #  COMBINED ALL-IN-ONE
    # ========================

    @classmethod
    def calculate_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all indicators to a DataFrame in one call.
        """
        df = cls.supertrend(df)
        df = cls.vwap(df)
        df = cls.ema_ribbon(df)
        df = cls.rsi(df)
        df = cls.stochastic_rsi(df)
        df = cls.adx(df)
        df = cls.obv(df)
        df = cls.bollinger_bands(df)
        df = cls.macd(df)
        df = cls.atr(df)
        return df

    @classmethod
    def get_summary(cls, df: pd.DataFrame) -> Dict:
        """
        Get a comprehensive indicator summary for the latest bar.
        """
        df = cls.calculate_all(df)
        latest = df.iloc[-1]
        structure = cls.market_structure(df)
        sr = cls.support_resistance(df)
        pivots = cls.pivot_points(df)

        # Aggregate signal
        bullish_count = 0
        bearish_count = 0

        if latest.get('supertrend_direction', 0) == 1:
            bullish_count += 1
        else:
            bearish_count += 1

        if latest['close'] > latest.get('vwap', latest['close']):
            bullish_count += 1
        else:
            bearish_count += 1

        if latest.get('ema_ribbon_bullish', False):
            bullish_count += 1
        elif latest.get('ema_ribbon_bearish', False):
            bearish_count += 1

        rsi_val = latest.get('rsi', 50)
        if rsi_val > 55:
            bullish_count += 1
        elif rsi_val < 45:
            bearish_count += 1

        if latest.get('macd_histogram', 0) > 0:
            bullish_count += 1
        else:
            bearish_count += 1

        if structure["structure"] == "UPTREND":
            bullish_count += 1
        elif structure["structure"] == "DOWNTREND":
            bearish_count += 1

        total = bullish_count + bearish_count
        bias = "BULLISH" if bullish_count > bearish_count else ("BEARISH" if bearish_count > bullish_count else "NEUTRAL")
        strength = round(max(bullish_count, bearish_count) / max(total, 1) * 100, 0)

        return {
            "bias": bias,
            "strength": strength,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "indicators": {
                "supertrend": int(latest.get('supertrend_direction', 0)),
                "vwap": round(float(latest.get('vwap', 0)), 2),
                "rsi": round(float(latest.get('rsi', 50)), 1),
                "adx": round(float(latest.get('adx', 0)), 1),
                "stoch_rsi_k": round(float(latest.get('stoch_rsi_k', 50)), 1),
                "stoch_rsi_d": round(float(latest.get('stoch_rsi_d', 50)), 1),
                "macd_histogram": round(float(latest.get('macd_histogram', 0)), 2),
                "ema_ribbon_bullish": bool(latest.get('ema_ribbon_bullish', False)),
                "ema_ribbon_bearish": bool(latest.get('ema_ribbon_bearish', False)),
                "bb_squeeze": bool(latest.get('bb_squeeze', False)),
                "atr": round(float(latest.get('atr', 0)), 2),
                "obv_trend": "UP" if latest.get('obv', 0) > latest.get('obv_ema', 0) else "DOWN",
            },
            "structure": structure,
            "support_resistance": sr,
            "pivots": pivots,
        }


# ========================
#  STANDALONE TEST
# ========================
if __name__ == "__main__":
    np.random.seed(42)

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

    summary = AdvancedIndicators.get_summary(df)

    import json
    print(json.dumps(summary, indent=2, default=str))
