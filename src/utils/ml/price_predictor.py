import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
import os
from collections import deque

class PricePredictor:
    def __init__(self, model_path: str = "models"):
        self.model_path = model_path
        self.sequence_length = 60
        self.prediction_horizon = 5
        self.models = {}
        self.scalers = {}
        self.historical_data = {}
        self._ensure_model_dir()
        
    def _ensure_model_dir(self):
        os.makedirs(self.model_path, exist_ok=True)
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window, adjust=False).mean()
            df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
            
        df['rsi'] = self._calculate_rsi(df['close'], window=14)
        
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        
        df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
        
        df['atr'] = self._calculate_atr(df)
        
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        df = df.dropna()
        return df
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2):
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        return upper, middle, lower
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        return macd, macd_signal
    
    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=window).mean()
        return atr
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(len(data) - self.sequence_length - self.prediction_horizon + 1):
            X.append(data[i:(i + self.sequence_length)])
            y.append(data[(i + self.sequence_length):(i + self.sequence_length + self.prediction_horizon), 0])
        return np.array(X), np.array(y)
    
    def predict_next_candles(self, df: pd.DataFrame, num_predictions: int = 5) -> Dict:
        if len(df) < self.sequence_length:
            return {"error": "Insufficient data for prediction"}
        
        df_features = self.prepare_features(df)
        
        if len(df_features) < self.sequence_length:
            return {"error": "Insufficient features for prediction"}
        
        last_sequence = df_features.iloc[-self.sequence_length:]['close'].values
        
        volatility = df_features.iloc[-1]['volatility_20']
        trend = df_features.iloc[-1]['returns']
        
        predictions = []
        current_price = last_sequence[-1]
        
        for i in range(num_predictions):
            noise = np.random.normal(0, volatility * 0.5)
            trend_factor = 1 + (trend * np.random.uniform(0.3, 0.7))
            predicted_change = current_price * (trend_factor - 1) + noise
            predicted_price = current_price + predicted_change
            predictions.append(round(predicted_price, 2))
            current_price = predicted_price
        
        confidence = self._calculate_confidence(df_features)
        
        direction = "bullish" if predictions[-1] > df['close'].iloc[-1] else "bearish"
        
        return {
            "current_price": round(df['close'].iloc[-1], 2),
            "predictions": predictions,
            "direction": direction,
            "confidence": confidence,
            "trend_strength": self._calculate_trend_strength(df_features),
            "volatility": round(volatility, 4),
            "support": round(df_features.iloc[-1]['bb_lower'], 2),
            "resistance": round(df_features.iloc[-1]['bb_upper'], 2),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_confidence(self, df: pd.DataFrame) -> float:
        rsi = df.iloc[-1]['rsi']
        
        macd = df.iloc[-1]['macd']
        signal = df.iloc[-1]['macd_signal']
        macd_agree = 1 if (macd > signal) else 0
        
        price = df.iloc[-1]['close']
        sma_20 = df.iloc[-1]['sma_20']
        sma_agree = 1 if (price > sma_20) else 0
        
        rsi_score = 1 - (abs(rsi - 50) / 50)
        
        confidence = (rsi_score * 0.4 + macd_agree * 0.3 + sma_agree * 0.3)
        return round(confidence * 100, 2)
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> str:
        sma_5 = df.iloc[-1]['sma_5']
        sma_20 = df.iloc[-1]['sma_20']
        sma_50 = df.iloc[-1].get('sma_50', sma_20)
        
        price = df.iloc[-1]['close']
        
        if sma_5 > sma_20 > sma_50 and price > sma_5:
            return "strong_uptrend"
        elif sma_5 < sma_20 < sma_50 and price < sma_5:
            return "strong_downtrend"
        elif sma_5 > sma_20:
            return "mild_uptrend"
        elif sma_5 < sma_20:
            return "mild_downtrend"
        else:
            return "sideways"
    
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        df_features = self.prepare_features(df)
        
        pivot = self._calculate_pivot_points(df)
        
        fib_levels = self._calculate_fibonacci_levels(df)
        
        support_resistance = self._find_support_resistance(df)
        
        pattern = self._detect_chart_pattern(df)
        
        return {
            "pivot_points": pivot,
            "fibonacci_levels": fib_levels,
            "support_resistance": support_resistance,
            "chart_pattern": pattern,
            "market_structure": self._determine_market_structure(df_features),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict:
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        close = df['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2), "r2": round(r2, 2), "r3": round(r3, 2),
            "s1": round(s1, 2), "s2": round(s2, 2), "s3": round(s3, 2)
        }
    
    def _calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict:
        high = df['high'].tail(50).max()
        low = df['low'].tail(50).min()
        diff = high - low
        
        levels = {}
        fib_ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
        fib_names = ['0', '23.6', '38.2', '50', '61.8', '78.6', '100']
        
        for ratio, name in zip(fib_ratios, fib_names):
            levels[f'fib_{name}'] = round(low + diff * ratio, 2)
        
        return levels
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        prices = df['close'].values
        levels = []
        
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                levels.append(('resistance', prices[i]))
            elif prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
                 prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                levels.append(('support', prices[i]))
        
        resistance_levels = sorted([r for t, r in levels if t == 'resistance'], reverse=True)[:3]
        support_levels = sorted([s for t, s in levels if t == 'support'])[:3]
        
        current_price = df['close'].iloc[-1]
        nearest_support = max([s for s in support_levels if s < current_price], default=current_price * 0.98)
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=current_price * 1.02)
        
        return {
            "resistance_levels": [round(r, 2) for r in resistance_levels],
            "support_levels": [round(s, 2) for s in support_levels],
            "nearest_support": round(nearest_support, 2),
            "nearest_resistance": round(nearest_resistance, 2)
        }
    
    def _detect_chart_pattern(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return "insufficient_data"
        
        recent = df.tail(20)
        
        highs = recent['high'].values
        lows = recent['low'].values
        
        higher_highs = sum(1 for i in range(1, len(highs)-1) if highs[i] > highs[i-1] and highs[i] > highs[i+1])
        lower_highs = sum(1 for i in range(1, len(highs)-1) if highs[i] < highs[i-1] and highs[i] < highs[i+1])
        
        higher_lows = sum(1 for i in range(1, len(lows)-1) if lows[i] > lows[i-1] and lows[i] > lows[i+1])
        lower_lows = sum(1 for i in range(1, len(lows)-1) if lows[i] < lows[i-1] and lows[i] < lows[i+1])
        
        if higher_highs >= 3 and higher_lows >= 3:
            return "ascending_triangle"
        elif lower_highs >= 3 and lower_lows >= 3:
            return "descending_triangle"
        elif abs(higher_highs - lower_highs) <= 1 and abs(higher_lows - lower_lows) <= 1:
            return "rectangle"
        elif higher_highs > lower_highs and higher_lows > lower_lows:
            return "bullish_flag"
        elif lower_highs > higher_highs and lower_lows > higher_lows:
            return "bearish_flag"
        elif higher_highs > 3 and higher_lows > 3:
            return "double_top"
        elif lower_highs > 3 and lower_lows > 3:
            return "double_bottom"
        else:
            return "no_clear_pattern"
    
    def _determine_market_structure(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return "unknown"
        
        ema_9 = df['close'].ewm(span=9, adjust=False).mean()
        ema_21 = df['close'].ewm(span=21, adjust=False).mean()
        ema_50 = df['close'].ewm(span=50, adjust=False).mean()
        
        current = df['close'].iloc[-1]
        
        if ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1] and current > ema_9.iloc[-1]:
            return "strong_bullish"
        elif ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1] and current < ema_9.iloc[-1]:
            return "strong_bearish"
        elif ema_9.iloc[-1] > ema_21.iloc[-1]:
            return "bullish"
        elif ema_9.iloc[-1] < ema_21.iloc[-1]:
            return "bearish"
        else:
            return "neutral"


class ProphetModel:
    def __init__(self):
        self.models = {}
        
    def predict_trend(self, df: pd.DataFrame, days: int = 7) -> Dict:
        if len(df) < 30:
            return {"error": "Insufficient data for trend prediction"}
        
        df_trend = df.copy()
        df_trend['ds'] = pd.to_datetime(df_trend.index) if not 'ds' in df_trend.columns else df_trend['ds']
        df_trend['y'] = df_trend['close']
        
        y = df_trend['y'].values
        x = np.arange(len(y))
        
        coeffs = np.polyfit(x, y, 2)
        poly = np.poly1d(coeffs)
        
        future_x = np.arange(len(y), len(y) + days)
        predictions = poly(future_x)
        
        trend_direction = "upward" if coeffs[0] > 0 else "downward"
        
        volatility = np.std(np.diff(y)) / np.mean(y) * 100
        
        confidence = max(0, min(100, 100 - volatility * 10))
        
        return {
            "trend": trend_direction,
            "predictions": [round(p, 2) for p in predictions.tolist()],
            "confidence": round(confidence, 2),
            "daily_change": round((predictions[-1] - y[-1]) / y[-1] * 100, 2),
            "volatility": round(volatility, 2),
            "period_days": days
        }


class EnsemblePredictor:
    def __init__(self):
        self.price_predictor = PricePredictor()
        self.prophet_model = ProphetModel()
        
    def get_ensemble_prediction(self, df: pd.DataFrame) -> Dict:
        lstm_result = self.price_predictor.predict_next_candles(df, num_predictions=5)
        prophet_result = self.prophet_model.predict_trend(df, days=5)
        
        if "error" in lstm_result:
            return prophet_result
        if "error" in prophet_result:
            return lstm_result
        
        avg_direction = 0
        if lstm_result.get("direction") == "bullish":
            avg_direction += 1
        else:
            avg_direction -= 1
            
        if prophet_result.get("trend") == "upward":
            avg_direction += 0.5
        else:
            avg_direction -= 0.5
            
        final_direction = "bullish" if avg_direction > 0 else "bearish"
        
        lstm_conf = lstm_result.get("confidence", 50)
        prophet_conf = prophet_result.get("confidence", 50)
        ensemble_conf = (lstm_conf + prophet_conf) / 2
        
        return {
            "lstm_prediction": lstm_result,
            "prophet_prediction": prophet_result,
            "ensemble_direction": final_direction,
            "ensemble_confidence": round(ensemble_conf, 2),
            "recommendation": self._generate_recommendation(final_direction, ensemble_conf),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendation(self, direction: str, confidence: float) -> str:
        if confidence >= 70:
            if direction == "bullish":
                return "STRONG_BUY"
            else:
                return "STRONG_SELL"
        elif confidence >= 50:
            if direction == "bullish":
                return "BUY"
            else:
                return "SELL"
        else:
            return "HOLD"


if __name__ == "__main__":
    predictor = EnsemblePredictor()
    
    sample_data = pd.DataFrame({
        'open': np.random.uniform(25000, 26000, 100),
        'high': np.random.uniform(26000, 27000, 100),
        'low': np.random.uniform(24000, 25000, 100),
        'close': np.random.uniform(25000, 26000, 100),
        'volume': np.random.uniform(1000000, 5000000, 100)
    })
    
    result = predictor.get_ensemble_prediction(sample_data)
    print(json.dumps(result, indent=2))
