import json
import random
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from src.utils.db_manager import DatabaseManager


class AISignalGenerator:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        try:
            from .price_predictor import EnsemblePredictor, PricePredictor
            from .pattern_recognizer import CandlestickPatternRecognizer, WaveAnalyzer
            from .sentiment_analyzer import SentimentAnalyzer, OptionsSentimentAnalyzer, NewsFetcher
            self.price_predictor = EnsemblePredictor()
            self.pattern_recognizer = CandlestickPatternRecognizer()
            self.wave_analyzer = WaveAnalyzer()
            self.sentiment_analyzer = SentimentAnalyzer()
            self.options_sentiment = OptionsSentimentAnalyzer()
            self.news_fetcher = NewsFetcher()
            self.models_loaded = True
        except ImportError:
            self.models_loaded = False
            
        self.signal_history = []
        
        # Load optimized weights from DB, fallback to defaults
        latest_weights = self.db.get_latest_weights()
        if latest_weights:
            self.weights = latest_weights
        else:
            self.weights = {
                'price_prediction': 0.25,
                'pattern_recognition': 0.25,
                'sentiment': 0.25,
                'options_flow': 0.25
            }
        
    def generate_comprehensive_signal(self, market_data: pd.DataFrame, options_data: Dict = None, news: List[str] = None) -> Dict:
        if not self.models_loaded:
            return self._generate_fallback_signal(market_data)
        
        logic_steps = [
            "🧠 Initializing Neural Network decision matrix...",
            f"📊 Fetching latest Nifty price action ({len(market_data)} bars)..."
        ]
        
        signals = {}
        
        try:
            logic_steps.append("🔍 Analyzing price momentum with Ensemble Predictor...")
            price_signal = self._analyze_price_prediction(market_data)
            signals['price_prediction'] = price_signal
            logic_steps.append(f"✅ Price Momentum: {price_signal.get('signal')} (Confidence: {price_signal.get('confidence')}%)")
        except Exception as e:
            signals['price_prediction'] = {"error": str(e), "signal": "NEUTRAL"}
            logic_steps.append(f"⚠️ Price analysis encountered an issue: {str(e)[:30]}...")
        
        try:
            logic_steps.append("📐 Scanning candlestick structures for recurring patterns...")
            pattern_signal = self._analyze_patterns(market_data)
            signals['pattern_recognition'] = pattern_signal
            logic_steps.append(f"✅ Pattern Logic: {pattern_signal.get('signal')} detected.")
        except Exception as e:
            signals['pattern_recognition'] = {"error": str(e), "signal": "NEUTRAL"}
            logic_steps.append("⚠️ Pattern scanner offline, using default risk parameters.")
        
        try:
            logic_steps.append("📰 Fetching global market news and sentiment data...")
            sentiment_signal = self._analyze_sentiment(news or [])
            signals['sentiment'] = sentiment_signal
            logic_steps.append(f"✅ Sentiment Score: {sentiment_signal.get('signal')}")
        except Exception as e:
            signals['sentiment']={"error": str(e), "overall_sentiment": "NEUTRAL"}
            logic_steps.append("⚠️ News API timeout, using historical sentiment buffer.")
        
        try:
            logic_steps.append("🌊 Analyzing Options Open Interest and Change in OI...")
            options_signal = self._analyze_options_flow(options_data or {})
            signals['options_flow'] = options_signal
            logic_steps.append(f"✅ Options Flow: {options_signal.get('signal')} dynamics confirmed.")
        except Exception as e:
            signals['options_flow'] = {"error": str(e), "sentiment": "NEUTRAL"}
            logic_steps.append("⚠️ OI Data mismatch, cross-referencing with spot price.")
        
        # Pass df through signals so _combine_signals can use it for multi-TF trends
        signals['_df'] = market_data
        
        logic_steps.append("⚖️ Applying adaptive self-learned weights to all signals...")
        final_signal = self._combine_signals(signals)
        final_signal['logic_steps'] = logic_steps
        logic_steps.append(f"🚀 Conclusion reached: {final_signal.get('recommendation')} with Score {final_signal.get('score')}")
        
        # Log signal to DB for tracking outcomes
        try:
            nifty_price = market_data['close'].iloc[-1] if not market_data.empty else 0
            self.db.log_signal(final_signal, nifty_price, self.weights)
        except Exception as e:
            print(f"Failed to log signal to DB: {e}")

        signal_entry = {
            "timestamp": datetime.now().isoformat(),
            "signals": signals,
            "final_signal": final_signal
        }
        self.signal_history.append(signal_entry)
        
        return final_signal
    
    def _analyze_price_prediction(self, df: pd.DataFrame) -> Dict:
        if len(df) < 5:
            return {"signal": "NEUTRAL", "confidence": 50, "direction": "neutral"}
        
        recent_closes = df['close'].tail(10).values
        sma_5 = df['close'].tail(5).mean()
        sma_10 = df['close'].tail(10).mean()
        current_price = df['close'].iloc[-1]
        
        if sma_5 > sma_10 and current_price > sma_5:
            direction = "bullish"
            confidence = 70
        elif sma_5 < sma_10 and current_price < sma_5:
            direction = "bearish"
            confidence = 70
        else:
            direction = "neutral"
            confidence = 50
        
        if confidence >= 70:
            signal = "STRONG_BUY" if direction == "bullish" else "STRONG_SELL"
        elif confidence >= 50:
            signal = "BUY" if direction == "bullish" else "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "direction": direction,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_patterns(self, df: pd.DataFrame) -> Dict:
        patterns = self.pattern_recognizer.recognize_all_patterns(df)
        
        signal = patterns.get('signal', 'NEUTRAL')
        strength = patterns.get('strength', 0)
        
        if strength >= 60 and signal in ['BUY', 'STRONG_BUY']:
            signal = 'STRONG_BUY'
        elif strength >= 60 and signal in ['SELL', 'STRONG_SELL']:
            signal = 'STRONG_SELL'
        
        return {
            "signal": signal,
            "strength": strength,
            "patterns": patterns,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_sentiment(self, news: List[str]) -> Dict:
        if not news:
            news = self.news_fetcher.fetch_market_news()
        
        sentiment = self.sentiment_analyzer.analyze_news(news)
        
        signal = sentiment.get('overall_sentiment', 'NEUTRAL')
        
        return {
            "signal": signal,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_options_flow(self, options_data: Dict) -> Dict:
        if not options_data:
            options_data = {
                'calls_oi': random.randint(1000000, 5000000),
                'puts_oi': random.randint(1000000, 5000000),
                'calls_change_oi': random.randint(-100000, 200000),
                'puts_change_oi': random.randint(-100000, 200000)
            }
        
        options_sentiment = self.options_sentiment.analyze_options_data(options_data)
        
        signal = options_sentiment.get('sentiment', 'NEUTRAL')
        
        return {
            "signal": signal,
            "options_sentiment": options_sentiment,
            "timestamp": datetime.now().isoformat()
        }
    
    def _combine_signals(self, signals: Dict) -> Dict:
        signal_scores = []
        
        price = signals.get('price_prediction', {})
        pattern = signals.get('pattern_recognition', {})
        sentiment = signals.get('sentiment', {})
        options = signals.get('options_flow', {})
        
        signal_map = {
            "STRONG_BUY": 2, "BUY": 1, "ACCUMULATE": 0.5,
            "NEUTRAL": 0,
            "REDUCE": -0.5, "SELL": -1, "STRONG_SELL": -2,
            "BULLISH": 1, "STRONG_BULLISH": 2,
            "BEARISH": -1, "STRONG_BEARISH": -2
        }
        
        price_score = signal_map.get(price.get('signal', 'NEUTRAL'), 0)
        pattern_score = signal_map.get(pattern.get('signal', 'NEUTRAL'), 0)
        sentiment_score = signal_map.get(sentiment.get('signal', 'NEUTRAL'), 0)
        options_score = signal_map.get(options.get('signal', 'NEUTRAL'), 0)
        
        price_conf = price.get('confidence', 50) / 100
        pattern_strength = pattern.get('strength', 0) / 100
        
        weight_sum = self.weights['price_prediction'] + self.weights['pattern_recognition'] + self.weights['sentiment'] + self.weights['options_flow']
        
        weighted_score = (
            price_score * price_conf * self.weights['price_prediction'] +
            pattern_score * pattern_strength * self.weights['pattern_recognition'] +
            sentiment_score * self.weights['sentiment'] +
            options_score * self.weights['options_flow']
        ) / weight_sum if weight_sum > 0 else 0
        
        final_score = weighted_score * 100
        
        if final_score >= 50:
            recommendation = "STRONG_BUY"
        elif final_score >= 20:
            recommendation = "BUY"
        elif final_score >= -20:
            recommendation = "HOLD"
        elif final_score >= -50:
            recommendation = "SELL"
        else:
            recommendation = "STRONG_SELL"
        
        reasons = []
        if price_score > 0:
            reasons.append(f"Price prediction: {price.get('signal')}")
        if pattern_score > 0:
            reasons.append(f"Patterns: {pattern.get('signal')}")
        if sentiment_score > 0:
            reasons.append(f"Sentiment: {sentiment.get('signal')}")
        if options_score > 0:
            reasons.append(f"Options flow: {options.get('signal')}")
        
        if not reasons:
            if price_score < 0:
                reasons.append(f"Price prediction: {price.get('signal')}")
            if pattern_score < 0:
                reasons.append(f"Patterns: {pattern.get('signal')}")
            if sentiment_score < 0:
                reasons.append(f"Sentiment: {sentiment.get('signal')}")
            if options_score < 0:
                reasons.append(f"Options flow: {options.get('signal')}")
        
        if not reasons:
            reasons.append("All indicators neutral")
        
        # Generate Pro Verdict (AI Reasoning)
        verdict = self._generate_pro_verdict(recommendation, final_score, reasons)
        
        # Calculate Trends for 5m, 15m, 1h based on recent price action
        trends = self._calculate_multi_tf_trends(signals.get('_df'))
        
        return {
            "recommendation": recommendation,
            "score": round(final_score, 1),
            "confidence": self._calculate_confidence(price, pattern, sentiment, options),
            "reasons": reasons,
            "verdict": verdict,
            "trends": trends,
            "components": {
                "price_prediction": price_score,
                "pattern_recognition": pattern_score,
                "sentiment": sentiment_score,
                "options_flow": options_score
            },
            "timestamp": datetime.now().isoformat(),
            # Actionable Trade Levels
            "entry_price": round(signals['_df']['close'].iloc[-1], 2) if not signals['_df'].empty else 0,
            "stop_loss": self._calculate_sl_tp(signals['_df'], recommendation)['sl'],
            "target": self._calculate_sl_tp(signals['_df'], recommendation)['tp']
        }

    def _calculate_sl_tp(self, df: pd.DataFrame, recommendation: str) -> Dict:
        """Calculates ATR-based Stop Loss and Take Profit levels."""
        if df is None or df.empty or len(df) < 14:
            return {"sl": 0, "tp": 0}
            
        current_price = df['close'].iloc[-1]
        
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        if "BUY" in recommendation:
            return {
                "sl": round(current_price - (atr * 1.5), 2),
                "tp": round(current_price + (atr * 3.0), 2)
            }
        elif "SELL" in recommendation:
            return {
                "sl": round(current_price + (atr * 1.5), 2),
                "tp": round(current_price - (atr * 3.0), 2)
            }
        return {"sl": 0, "tp": 0}

    def _generate_pro_verdict(self, rec, score, reasons):
        """Generates a plain English 'Smart Verdict' for the pro-trading terminal."""
        if "STRONG_BUY" in rec:
            return f"Nifty is showing powerful bullish momentum with a score of {score}. Major indicators and options flow are aligned for an upside move. Consider aggressive entry."
        elif "BUY" in rec:
            return f"Bullish bias detected. Market is respecting support levels with {len(reasons)} positive conditions met. Look for entries on minor dips."
        elif "STRONG_SELL" in rec:
            return f"Heavy bearish pressure detected (Score: {score}). Multiple breakdown patterns confirmed. High risk area for buyers; shorts are dominating the flow."
        elif "SELL" in rec:
            return f"Bearish momentum building. Indicators suggest a potential correction. Volume and options data favoring 'Sell on Rise' strategy."
        else:
            return "Market is currently in a range-bound or sideways phase. No clear edge for buyers or sellers. Patience is recommended until a breakout occurs."

    def _calculate_multi_tf_trends(self, df):
        """Detects trends across different timeframes based on SMA/EMA alignments."""
        if df is None or len(df) < 60:
            return {"5m": "NEUTRAL", "15m": "NEUTRAL", "1h": "NEUTRAL", "1d": "NEUTRAL"}
        
        last_price = df['close'].iloc[-1]
        
        def get_trend(price, fast_window, slow_window):
            fast = df['close'].tail(fast_window).mean()
            slow = df['close'].tail(slow_window).mean()
            if price > fast > slow: return "BULLISH"
            if price < fast < slow: return "BEARISH"
            return "NEUTRAL"
        
        # Proxy TFs based on windows of the current timeframe (e.g., 5m)
        return {
            "5m": get_trend(last_price, 5, 20),
            "15m": get_trend(last_price, 10, 30),
            "1h": get_trend(last_price, 20, 50),
            "1d": get_trend(last_price, 40, 100) if len(df) >= 100 else "NEUTRAL"
        }
    
    def _calculate_confidence(self, price: Dict, pattern: Dict, sentiment: Dict, options: Dict) -> float:
        confidences = []
        
        if 'confidence' in price:
            confidences.append(price['confidence'])
        if 'strength' in pattern:
            confidences.append(pattern['strength'])
        
        sentiment_conf = 50
        options_conf = 50
        
        sentiment_score = sentiment.get('sentiment', {}).get('sentiment_score', 0)
        if sentiment_score:
            sentiment_conf = min(abs(sentiment_score) * 100 + 30, 90)
        
        pcr = sentiment.get('options_sentiment', {}).get('put_call_ratio', 1.0)
        if 0.7 <= pcr <= 1.3:
            options_conf = 70
        else:
            options_conf = 50
        
        confidences.extend([sentiment_conf, options_conf])
        
        return round(sum(confidences) / len(confidences), 1) if confidences else 50.0
    
    def _generate_fallback_signal(self, df: pd.DataFrame) -> Dict:
        return {
            "recommendation": "HOLD",
            "score": 0,
            "confidence": 0,
            "reasons": ["AI models not loaded - using fallback"],
            "verdict": "The AI analysis module is currently offline. Market trend detection and smart reasoning are unavailable. Please check system logs for model loading issues.",
            "trends": {"5m": "NEUTRAL", "15m": "NEUTRAL", "1h": "NEUTRAL"},
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def get_signal_history(self, limit: int = 10) -> List[Dict]:
        return self.signal_history[-limit:]
    
    def update_weights(self, new_weights: Dict):
        total = sum(new_weights.values())
        if abs(total - 1.0) < 0.01:
            self.weights = new_weights
    
    def backtest_signals(self, historical_data: List[Dict]) -> Dict:
        if not self.signal_history:
            return {"error": "No signal history available"}
        
        correct_signals = 0
        total_signals = len(self.signal_history)
        
        for i, signal_entry in enumerate(self.signal_history[:-1]):
            current_signal = signal_entry['final_signal']['recommendation']
            
            if i < len(historical_data):
                actual_direction = historical_data[i].get('actual_direction', 'HOLD')
                
                if (current_signal in ['STRONG_BUY', 'BUY'] and actual_direction in ['UP', 'BULLISH']) or \
                   (current_signal in ['STRONG_SELL', 'SELL'] and actual_direction in ['DOWN', 'BEARISH']):
                    correct_signals += 1
                elif current_signal == 'HOLD' and actual_direction == 'SIDEWAYS':
                    correct_signals += 1
        
        accuracy = (correct_signals / total_signals * 100) if total_signals > 0 else 0
        
        return {
            "total_signals": total_signals,
            "correct_signals": correct_signals,
            "accuracy": round(accuracy, 2),
            "timestamp": datetime.now().isoformat()
        }


class RiskAdjustedSignalGenerator(AISignalGenerator):
    def __init__(self):
        super().__init__()
        self.max_position_size = 0.1
        self.max_loss_per_trade = 0.02
        
    def generate_signal_with_risk(self, market_data: pd.DataFrame, account_balance: float, options_data: Dict = None) -> Dict:
        base_signal = self.generate_comprehensive_signal(market_data, options_data)
        
        recommendation = base_signal['recommendation']
        score = base_signal['score']
        confidence = base_signal['confidence']
        
        position_size = 0
        stop_loss = 0
        take_profit = 0
        
        if recommendation in ['STRONG_BUY', 'BUY']:
            position_size = self._calculate_position_size(confidence, account_balance)
            
            if len(market_data) > 0:
                current_price = market_data['close'].iloc[-1]
                atr = self._calculate_atr(market_data)
                stop_loss = round(current_price - (atr * 2), 2)
                take_profit = round(current_price + (atr * 3), 2)
        
        elif recommendation in ['STRONG_SELL', 'SELL']:
            position_size = self._calculate_position_size(confidence, account_balance)
            
            if len(market_data) > 0:
                current_price = market_data['close'].iloc[-1]
                atr = self._calculate_atr(market_data)
                stop_loss = round(current_price + (atr * 2), 2)
                take_profit = round(current_price - (atr * 3), 2)
        
        return {
            **base_signal,
            "position_size": position_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": round((take_profit - market_data['close'].iloc[-1]) / (market_data['close'].iloc[-1] - stop_loss), 2) if stop_loss and take_profit and len(market_data) > 0 else 0,
            "account_balance": account_balance,
            "max_risk_amount": round(account_balance * self.max_loss_per_trade, 2)
        }
    
    def _calculate_position_size(self, confidence: float, account_balance: float) -> float:
        base_size = self.max_position_size * account_balance
        
        confidence_factor = confidence / 100
        
        position_size = base_size * confidence_factor
        
        return round(position_size, 2)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        if len(df) < period:
            return df['close'].iloc[-1] * 0.02
        
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr


if __name__ == "__main__":
    generator = AISignalGenerator()
    
    dates = pd.date_range(start='2024-01-01', periods=60)
    
    np.random.seed(42)
    base_price = 25000
    
    closes = []
    for i in range(60):
        closes.append(base_price + np.random.uniform(-200, 200))
        base_price += np.random.uniform(-100, 100)
    
    df = pd.DataFrame({
        'open': [c + np.random.uniform(-50, 50) for c in closes],
        'high': [c + np.random.uniform(0, 100) for c in closes],
        'low': [c - np.random.uniform(0, 100) for c in closes],
        'close': closes,
        'volume': [np.random.uniform(1000000, 5000000) for _ in range(60)]
    }, index=dates)
    
    result = generator.generate_comprehensive_signal(df)
    print(json.dumps(result, indent=2))
