import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class CandlestickPatternRecognizer:
    def __init__(self):
        self.patterns = {}
        
    def recognize_all_patterns(self, df: pd.DataFrame) -> Dict:
        if len(df) < 3:
            return {"error": "Insufficient data for pattern recognition"}
        
        patterns_found = []
        
        candlestick_patterns = self._detect_candlestick_patterns(df)
        if candlestick_patterns:
            patterns_found.extend(candlestick_patterns)
        
        chart_patterns = self._detect_chart_patterns(df)
        if chart_patterns:
            patterns_found.extend(chart_patterns)
        
        harmonic_patterns = self._detect_harmonic_patterns(df)
        if harmonic_patterns:
            patterns_found.extend(harmonic_patterns)
        
        return {
            "patterns": patterns_found,
            "signal": self._generate_signal(patterns_found),
            "strength": self._calculate_pattern_strength(patterns_found),
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = []
        
        if len(df) >= 3:
            three_candle = self._detect_three_candle_patterns(df)
            patterns.extend(three_candle)
        
        if len(df) >= 2:
            two_candle = self._detect_two_candle_patterns(df)
            patterns.extend(two_candle)
        
        single_candle = self._detect_single_candle_patterns(df.tail(1).iloc[0])
        if single_candle:
            patterns.append(single_candle)
        
        return patterns
    
    def _detect_single_candle_patterns(self, candle: pd.Series) -> Optional[Dict]:
        open_price = candle['open']
        close_price = candle['close']
        high = candle['high']
        low = candle['low']
        
        body = abs(close_price - open_price)
        upper_shadow = high - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low
        total_range = high - low
        
        if total_range == 0:
            return None
            
        body_ratio = body / total_range
        upper_shadow_ratio = upper_shadow / total_range
        lower_shadow_ratio = lower_shadow / total_range
        
        is_bullish = close_price > open_price
        
        if body_ratio < 0.1:
            if upper_shadow_ratio > 0.6 and lower_shadow_ratio < 0.2:
                return {
                    "type": "candlestick",
                    "pattern": "shooting_star",
                    "direction": "bearish",
                    "reliability": "high" if upper_shadow_ratio > 0.8 else "medium"
                }
            elif lower_shadow_ratio > 0.6 and upper_shadow_ratio < 0.2:
                return {
                    "type": "candlestick",
                    "pattern": "hammer",
                    "direction": "bullish",
                    "reliability": "high" if lower_shadow_ratio > 0.8 else "medium"
                }
            return {
                "type": "candlestick",
                "pattern": "doji",
                "direction": "neutral",
                "reliability": "medium"
            }
        
        if upper_shadow_ratio > 0.5 and lower_shadow_ratio < 0.1 and body_ratio > 0.5:
            return {
                "type": "candlestick",
                "pattern": "gravestone_doji",
                "direction": "bearish",
                "reliability": "high"
            }
        
        if lower_shadow_ratio > 0.5 and upper_shadow_ratio < 0.1 and body_ratio > 0.5:
            return {
                "type": "candlestick",
                "pattern": "dragonfly_doji",
                "direction": "bullish",
                "reliability": "high"
            }
        
        if body_ratio > 0.9 and upper_shadow_ratio < 0.05 and lower_shadow_ratio < 0.05:
            return {
                "type": "candlestick",
                "pattern": "marubozu",
                "direction": "bullish" if is_bullish else "bearish",
                "reliability": "high"
            }
        
        return None
    
    def _detect_two_candle_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = []
        last_two = df.tail(2)
        
        candle1 = last_two.iloc[0]
        candle2 = last_two.iloc[1]
        
        bullish_engulfing = self._check_bullish_engulfing(candle1, candle2)
        if bullish_engulfing:
            patterns.append(bullish_engulfing)
        
        bearish_engulfing = self._check_bearish_engulfing(candle1, candle2)
        if bearish_engulfing:
            patterns.append(bearish_engulfing)
        
        if len(df) >= 3:
            tweezer = self._check_tweezer_tops_bottoms(last_two.iloc[0], df.iloc[-3])
            if tweezer:
                patterns.append(tweezer)
        
        return patterns
    
    def _check_bullish_engulfing(self, candle1: pd.Series, candle2: pd.Series) -> Optional[Dict]:
        if candle1['close'] < candle1['open'] and candle2['close'] > candle2['open']:
            if candle2['open'] < candle1['close'] and candle2['close'] > candle1['open']:
                body1 = candle1['open'] - candle1['close']
                body2 = candle2['close'] - candle2['open']
                if body2 > body1 * 1.2:
                    return {
                        "type": "candlestick",
                        "pattern": "bullish_engulfing",
                        "direction": "bullish",
                        "reliability": "high"
                    }
        return None
    
    def _check_bearish_engulfing(self, candle1: pd.Series, candle2: pd.Series) -> Optional[Dict]:
        if candle1['close'] > candle1['open'] and candle2['close'] < candle2['open']:
            if candle2['open'] > candle1['close'] and candle2['close'] < candle1['open']:
                body1 = candle1['close'] - candle1['open']
                body2 = candle2['open'] - candle2['close']
                if body2 > body1 * 1.2:
                    return {
                        "type": "candlestick",
                        "pattern": "bearish_engulfing",
                        "direction": "bearish",
                        "reliability": "high"
                    }
        return None
    
    def _check_tweezer_tops_bottoms(self, candle1: pd.Series, candle2: pd.Series) -> Optional[Dict]:
        if abs(candle1['high'] - candle2['high']) < (candle1['high'] - candle1['low']) * 0.1:
            if candle1['close'] < candle1['open'] and candle2['close'] > candle2['open']:
                return {
                    "type": "candlestick",
                    "pattern": "tweezer_bottom",
                    "direction": "bullish",
                    "reliability": "medium"
                }
        elif abs(candle1['low'] - candle2['low']) < (candle1['high'] - candle1['low']) * 0.1:
            if candle1['close'] > candle1['open'] and candle2['close'] < candle2['open']:
                return {
                    "type": "candlestick",
                    "pattern": "tweezer_top",
                    "direction": "bearish",
                    "reliability": "medium"
                }
        return None
    
    def _detect_three_candle_patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = []
        last_three = df.tail(3)
        
        morning_star = self._check_morning_star(last_three.iloc[0], last_three.iloc[1], last_three.iloc[2])
        if morning_star:
            patterns.append(morning_star)
        
        evening_star = self._check_evening_star(last_three.iloc[0], last_three.iloc[1], last_three.iloc[2])
        if evening_star:
            patterns.append(evening_star)
        
        three_white_soldiers = self._check_three_white_soldiers(last_three)
        if three_white_soldiers:
            patterns.append(three_white_soldiers)
        
        three_black_crows = self._check_three_black_crows(last_three)
        if three_black_crows:
            patterns.append(three_black_crows)
        
        return patterns
    
    def _check_morning_star(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[Dict]:
        if candle1['close'] < candle1['open']:
            if abs(candle2['close'] - candle2['open']) < abs(candle1['open'] - candle1['close']) * 0.3:
                if candle3['close'] > candle3['open'] and candle3['close'] > (candle1['open'] + candle1['close']) / 2:
                    return {
                        "type": "candlestick",
                        "pattern": "morning_star",
                        "direction": "bullish",
                        "reliability": "high"
                    }
        return None
    
    def _check_evening_star(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[Dict]:
        if candle1['close'] > candle1['open']:
            if abs(candle2['close'] - candle2['open']) < abs(candle1['close'] - candle1['open']) * 0.3:
                if candle3['close'] < candle3['open'] and candle3['close'] < (candle1['open'] + candle1['close']) / 2:
                    return {
                        "type": "candlestick",
                        "pattern": "evening_star",
                        "direction": "bearish",
                        "reliability": "high"
                    }
        return None
    
    def _check_three_white_soldiers(self, candles: pd.DataFrame) -> Optional[Dict]:
        c1, c2, c3 = candles.iloc[0], candles.iloc[1], candles.iloc[2]
        
        if (c1['close'] > c1['open'] and c2['close'] > c2['open'] and c3['close'] > c3['open']):
            if (c2['close'] > c1['close'] and c3['close'] > c2['close']):
                body1 = c1['close'] - c1['open']
                body2 = c2['close'] - c2['open']
                body3 = c3['close'] - c3['open']
                
                if (c2['open'] > c1['open'] and c3['open'] > c2['open']):
                    if min(body1, body2, body3) > 0.5 * max(body1, body2, body3):
                        return {
                            "type": "candlestick",
                            "pattern": "three_white_soldiers",
                            "direction": "bullish",
                            "reliability": "high"
                        }
        return None
    
    def _check_three_black_crows(self, candles: pd.DataFrame) -> Optional[Dict]:
        c1, c2, c3 = candles.iloc[0], candles.iloc[1], candles.iloc[2]
        
        if (c1['close'] < c1['open'] and c2['close'] < c2['open'] and c3['close'] < c3['open']):
            if (c2['close'] < c1['close'] and c3['close'] < c2['close']):
                body1 = c1['open'] - c1['close']
                body2 = c2['open'] - c2['close']
                body3 = c3['open'] - c3['close']
                
                if (c2['open'] < c1['open'] and c3['open'] < c2['open']):
                    if min(body1, body2, body3) > 0.5 * max(body1, body2, body3):
                        return {
                            "type": "candlestick",
                            "pattern": "three_black_crows",
                            "direction": "bearish",
                            "reliability": "high"
                        }
        return None
    
    def _detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        if len(df) < 20:
            return []
        
        patterns = []
        
        head_shoulders = self._detect_head_and_shoulders(df)
        if head_shoulders:
            patterns.append(head_shoulders)
        
        double_top = self._detect_double_top(df)
        if double_top:
            patterns.append(double_top)
        
        double_bottom = self._detect_double_bottom(df)
        if double_bottom:
            patterns.append(double_bottom)
        
        wedge = self._detect_wedge(df)
        if wedge:
            patterns.append(wedge)
        
        return patterns
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> Optional[Dict]:
        highs = df['high'].values
        
        local_maxima = []
        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                local_maxima.append((i, highs[i]))
        
        if len(local_maxima) >= 3:
            left_shoulder = local_maxima[0]
            head = max(local_maxima, key=lambda x: x[1])
            right_shoulder = local_maxima[-1]
            
            if (abs(head[1] - left_shoulder[1]) < head[1] * 0.03 and 
                abs(head[1] - right_shoulder[1]) < head[1] * 0.03 and
                left_shoulder[0] < head[0] < right_shoulder[0]):
                
                return {
                    "type": "chart",
                    "pattern": "head_and_shoulders",
                    "direction": "bearish",
                    "reliability": "high"
                }
            
            if (abs(left_shoulder[1] - right_shoulder[1]) < head[1] * 0.02 and
                left_shoulder[0] < head[0]):
                
                return {
                    "type": "chart",
                    "pattern": "inverse_head_and_shoulders",
                    "direction": "bullish",
                    "reliability": "high"
                }
        
        return None
    
    def _detect_double_top(self, df: pd.DataFrame) -> Optional[Dict]:
        highs = df['high'].values
        
        local_maxima = []
        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                local_maxima.append(highs[i])
        
        if len(local_maxima) >= 2:
            top1 = max(local_maxima[:-1])
            top2 = max(local_maxima[1:])
            
            if abs(top1 - top2) < top1 * 0.02:
                return {
                    "type": "chart",
                    "pattern": "double_top",
                    "direction": "bearish",
                    "reliability": "medium"
                }
        
        return None
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> Optional[Dict]:
        lows = df['low'].values
        
        local_minima = []
        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                local_minima.append(lows[i])
        
        if len(local_minima) >= 2:
            bottom1 = min(local_minima[:-1])
            bottom2 = min(local_minima[1:])
            
            if abs(bottom1 - bottom2) < bottom1 * 0.02:
                return {
                    "type": "chart",
                    "pattern": "double_bottom",
                    "direction": "bullish",
                    "reliability": "medium"
                }
        
        return None
    
    def _detect_wedge(self, df: pd.DataFrame) -> Optional[Dict]:
        if len(df) < 20:
            return None
        
        recent = df.tail(20)
        highs = recent['high'].values
        lows = recent['low'].values
        
        high_slope = (highs[-1] - highs[0]) / len(highs)
        low_slope = (lows[-1] - lows[0]) / len(lows)
        
        if high_slope < 0 and low_slope < 0:
            if abs(high_slope - low_slope) < abs(high_slope) * 0.3:
                return {
                    "type": "chart",
                    "pattern": "falling_wedge",
                    "direction": "bullish",
                    "reliability": "medium"
                }
        
        if high_slope > 0 and low_slope > 0:
            if abs(high_slope - low_slope) < abs(high_slope) * 0.3:
                return {
                    "type": "chart",
                    "pattern": "rising_wedge",
                    "direction": "bearish",
                    "reliability": "medium"
                }
        
        return None
    
    def _detect_harmonic_patterns(self, df: pd.DataFrame) -> List[Dict]:
        return []
    
    def _generate_signal(self, patterns: List[Dict]) -> str:
        if not patterns:
            return "NEUTRAL"
        
        bullish_count = sum(1 for p in patterns if p.get('direction') == 'bullish')
        bearish_count = sum(1 for p in patterns if p.get('direction') == 'bearish')
        
        high_reliability_bullish = sum(1 for p in patterns 
                                       if p.get('direction') == 'bullish' and p.get('reliability') == 'high')
        high_reliability_bearish = sum(1 for p in patterns 
                                        if p.get('direction') == 'bearish' and p.get('reliability') == 'high')
        
        if high_reliability_bullish > high_reliability_bearish:
            return "STRONG_BUY"
        elif high_reliability_bearish > high_reliability_bullish:
            return "STRONG_SELL"
        elif bullish_count > bearish_count:
            return "BUY"
        elif bearish_count > bullish_count:
            return "SELL"
        else:
            return "NEUTRAL"
    
    def _calculate_pattern_strength(self, patterns: List[Dict]) -> float:
        if not patterns:
            return 0.0
        
        reliability_weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        
        total_strength = 0
        for pattern in patterns:
            reliability = pattern.get('reliability', 'low')
            total_strength += reliability_weights.get(reliability, 0.3)
        
        avg_strength = total_strength / len(patterns)
        
        direction_weight = 1.0
        directions = [p.get('direction') for p in patterns]
        if directions.count('bullish') == len(directions) or directions.count('bearish') == len(directions):
            direction_weight = 1.2
        
        return min(round(avg_strength * direction_weight * 20, 1), 100)


class WaveAnalyzer:
    def __init__(self):
        pass
    
    def analyze_waves(self, df: pd.DataFrame) -> Dict:
        if len(df) < 50:
            return {"error": "Insufficient data for wave analysis"}
        
        closes = df['close'].values
        
        peaks, troughs = self._find_peaks_and_troughs(closes)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {
                "wave_pattern": "unclear",
                "interpretation": "Not enough data to determine wave pattern"
            }
        
        return {
            "peaks": peaks,
            "troughs": troughs,
            "wave_pattern": self._classify_waves(peaks, troughs),
            "timestamp": datetime.now().isoformat()
        }
    
    def _find_peaks_and_troughs(self, prices: np.ndarray, threshold: float = 0.02):
        peaks = []
        troughs = []
        
        window = 5
        for i in range(window, len(prices) - window):
            if all(prices[i] > prices[i-j] for j in range(1, window+1)) and \
               all(prices[i] > prices[i+j] for j in range(1, window+1)):
                peaks.append(prices[i])
            
            if all(prices[i] < prices[i-j] for j in range(1, window+1)) and \
               all(prices[i] < prices[i+j] for j in range(1, window+1)):
                troughs.append(prices[i])
        
        return peaks, troughs
    
    def _classify_waves(self, peaks: List[float], troughs: List[float]) -> str:
        if len(peaks) >= 3 and len(troughs) >= 2:
            last_peak = peaks[-1]
            last_trough = troughs[-1]
            
            if last_peak > last_trough:
                return "impulse_wave_up"
            else:
                return "impulse_wave_down"
        
        return "corrective_wave"


if __name__ == "__main__":
    recognizer = CandlestickPatternRecognizer()
    
    import random
    np.random.seed(42)
    random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=30)
    base_price = 25000
    
    closes = []
    for i in range(30):
        closes.append(base_price + np.random.uniform(-200, 200))
        base_price += np.random.uniform(-100, 100)
    
    df = pd.DataFrame({
        'open': [c + np.random.uniform(-50, 50) for c in closes],
        'high': [c + np.random.uniform(0, 100) for c in closes],
        'low': [c - np.random.uniform(0, 100) for c in closes],
        'close': closes,
        'volume': [np.random.uniform(1000000, 5000000) for _ in range(30)]
    }, index=dates)
    
    result = recognizer.recognize_all_patterns(df)
    print(json.dumps(result, indent=2))
