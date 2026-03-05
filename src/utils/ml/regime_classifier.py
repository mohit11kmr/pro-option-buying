"""
Phase 10: Market Regime Classification
Detects Bull/Bear/Sideways markets using Machine Learning ensemble.
Author: Nifty Options Toolkit
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegimeClassifier:
    """
    Multi-model ensemble for market regime classification.
    
    Regimes:
    - 0: BEARISH (downtrend)
    - 1: SIDEWAYS (range-bound)
    - 2: BULLISH (uptrend)
    """
    
    def __init__(self, window=20, lookback=252):
        """
        Initialize regime classifier.
        
        Args:
            window: Period for feature calculation
            lookback: Historical data lookback window
        """
        self.window = window
        self.lookback = lookback
        self.scaler = StandardScaler()
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.models = {'rf': self.rf_model, 'gb': self.gb_model}
        self.is_trained = False
        
    def _calculate_features(self, df):
        """
        Calculate technical features for regime classification.
        
        Returns:
            DataFrame with 20+ features
        """
        features = pd.DataFrame(index=df.index)
        
        # Trend features
        features['sma20_above_sma50'] = (
            df['close'].rolling(20).mean() > df['close'].rolling(50).mean()
        ).astype(int)
        
        features['sma50_above_sma200'] = (
            df['close'].rolling(50).mean() > df['close'].rolling(200).mean()
        ).astype(int)
        
        # Volatility features
        features['volatility'] = df['close'].pct_change().rolling(self.window).std()
        features['atr'] = self._calculate_atr(df)
        features['atr_ratio'] = features['atr'] / df['close']
        
        # Momentum features
        features['rsi'] = self._calculate_rsi(df['close'])
        features['macd'] = self._calculate_macd(df['close'])[0]
        features['macd_signal'] = self._calculate_macd(df['close'])[1]
        features['momentum'] = df['close'].diff(self.window)
        
        # Trend strength
        features['adx'] = self._calculate_adx(df)
        features['cci'] = self._calculate_cci(df)
        
        # Volume features
        if 'volume' in df.columns:
            features['volume_sma'] = df['volume'].rolling(self.window).mean()
            features['volume_ratio'] = df['volume'] / features['volume_sma']
        else:
            features['volume_ratio'] = 1.0
        
        # Price action features
        features['close_position'] = (
            (df['close'] - df['close'].rolling(self.window).min()) /
            (df['close'].rolling(self.window).max() - df['close'].rolling(self.window).min())
        )
        
        # Returns features
        features['returns'] = df['close'].pct_change()
        features['returns_mean'] = features['returns'].rolling(self.window).mean()
        features['returns_std'] = features['returns'].rolling(self.window).std()
        
        # Volatility regime
        features['high_volatility'] = (
            features['volatility'] > features['volatility'].rolling(50).quantile(0.75)
        ).astype(int)
        
        return features.fillna(0)
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        
        return macd, macd_signal
    
    def _calculate_adx(self, df, period=14):
        """Calculate Average Directional Index (simplified)."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where(plus_dm > 0, 0)
        minus_dm = minus_dm.where(minus_dm > 0, 0)
        
        tr = self._calculate_atr(df, period)
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def _calculate_cci(self, df, period=20):
        """Calculate Commodity Channel Index."""
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        
        cci = (tp - sma) / (0.015 * mad)
        
        return cci
    
    def _create_labels(self, df):
        """
        Create regime labels based on price action.
        
        Returns:
            0: BEARISH, 1: SIDEWAYS, 2: BULLISH
        """
        # Calculate 21-day returns
        returns_21 = df['close'].pct_change(21)
        
        # Calculate 21-day volatility
        volatility = df['close'].pct_change().rolling(21).std()
        
        labels = []
        for i in range(len(df)):
            if i < 21:
                labels.append(np.nan)
            else:
                ret = returns_21.iloc[i]
                vol = volatility.iloc[i]
                
                # Determine regime
                if vol < volatility.rolling(252).quantile(0.33).iloc[i]:
                    # Low volatility
                    if abs(ret) < 0.01:
                        labels.append(1)  # SIDEWAYS
                    elif ret > 0:
                        labels.append(2)  # BULLISH
                    else:
                        labels.append(0)  # BEARISH
                elif vol > volatility.rolling(252).quantile(0.66).iloc[i]:
                    # High volatility
                    labels.append(0 if ret < 0 else 2)
                else:
                    # Medium volatility
                    if ret > 0.02:
                        labels.append(2)  # BULLISH
                    elif ret < -0.02:
                        labels.append(0)  # BEARISH
                    else:
                        labels.append(1)  # SIDEWAYS
        
        return np.array(labels)
    
    def fit(self, df):
        """
        Train regime classification models.
        
        Args:
            df: DataFrame with OHLC data
        """
        logger.info("Training regime classifier...")
        
        # Calculate features
        X = self._calculate_features(df)
        y = self._create_labels(df)
        
        # Remove NaN values
        valid_idx = ~np.isnan(y)
        X = X[valid_idx]
        y = y[valid_idx]
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train models
        for name, model in self.models.items():
            logger.info(f"Training {name.upper()} model...")
            model.fit(X_scaled, y)
        
        self.is_trained = True
        logger.info("Regime classifier training complete!")
    
    def predict(self, df):
        """
        Predict current market regime.
        
        Returns:
            Dict with regime, probability, and confidence
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
        
        # Use latest data
        recent_df = df.tail(self.lookback)
        
        # Calculate features
        X = self._calculate_features(recent_df)
        X = X.iloc[-1:].values  # Get latest row
        
        # Standardize
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from both models
        rf_pred = self.rf_model.predict(X_scaled)[0]
        gb_pred = self.gb_model.predict(X_scaled)[0]
        
        # Get probabilities
        rf_proba = self.rf_model.predict_proba(X_scaled)[0]
        gb_proba = self.gb_model.predict_proba(X_scaled)[0]
        
        # Ensemble: average probabilities
        ensemble_proba = (rf_proba + gb_proba) / 2
        regime = np.argmax(ensemble_proba)
        confidence = ensemble_proba[regime]
        
        # Map regime to names
        regime_names = ['BEARISH', 'SIDEWAYS', 'BULLISH']
        
        return {
            'regime': regime_names[regime],
            'regime_code': regime,
            'confidence': float(confidence),
            'probabilities': {
                'bearish': float(ensemble_proba[0]),
                'sideways': float(ensemble_proba[1]),
                'bullish': float(ensemble_proba[2])
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_sequence(self, df):
        """
        Predict regime for recent periods (last 5 days).
        
        Returns:
            List of regime predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
        
        recent_df = df.tail(self.lookback)
        X = self._calculate_features(recent_df)
        
        # Get last 5 rows
        X_recent = X.tail(5).values
        X_scaled = self.scaler.transform(X_recent)
        
        predictions = []
        regime_names = ['BEARISH', 'SIDEWAYS', 'BULLISH']
        
        for i, X_row in enumerate(X_scaled):
            rf_proba = self.rf_model.predict_proba([X_row])[0]
            gb_proba = self.gb_model.predict_proba([X_row])[0]
            ensemble_proba = (rf_proba + gb_proba) / 2
            
            regime = np.argmax(ensemble_proba)
            
            predictions.append({
                'timestamp': df.index[-5+i].isoformat() if hasattr(df.index[-5+i], 'isoformat') else str(df.index[-5+i]),
                'regime': regime_names[regime],
                'confidence': float(ensemble_proba[regime])
            })
        
        return predictions
    
    def get_feature_importance(self):
        """Get feature importances from trained models."""
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
        
        # Get feature names
        features = self._calculate_features(pd.DataFrame({'close': [1, 2, 3]})).columns.tolist()
        
        return {
            'rf_importance': dict(zip(features, self.rf_model.feature_importances_)),
            'gb_importance': dict(zip(features, self.gb_model.feature_importances_))
        }
    
    def save(self, filepath):
        """Save trained models."""
        joblib.dump({
            'rf': self.rf_model,
            'gb': self.gb_model,
            'scaler': self.scaler,
            'window': self.window,
            'lookback': self.lookback
        }, filepath)
        logger.info(f"Models saved to {filepath}")
    
    def load(self, filepath):
        """Load trained models."""
        data = joblib.load(filepath)
        self.rf_model = data['rf']
        self.gb_model = data['gb']
        self.scaler = data['scaler']
        self.window = data['window']
        self.lookback = data['lookback']
        self.is_trained = True
        logger.info(f"Models loaded from {filepath}")


if __name__ == "__main__":
    # Example usage
    print("\nPhase 10: Market Regime Classifier")
    print("=" * 50)
    
    # Create sample data
    from utils.backtester import HistoricalDataGenerator
    gen = HistoricalDataGenerator()
    df = gen.generate_with_market_events(years=2)
    
    # Initialize and train
    classifier = RegimeClassifier()
    classifier.fit(df)
    
    # Predict current regime
    result = classifier.predict(df)
    print(f"\n📊 Current Market Regime:")
    print(f"   Regime: {result['regime']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Probabilities: {result['probabilities']}")
    
    # Get recent predictions
    print(f"\n📈 Recent Regime History:")
    for pred in classifier.predict_sequence(df):
        print(f"   {pred['timestamp']}: {pred['regime']} ({pred['confidence']:.2%})")
