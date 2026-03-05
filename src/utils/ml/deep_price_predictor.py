"""
Phase 10: Deep Price Prediction with LSTM + Transformer
Advanced neural network models for market price forecasting.
Author: Nifty Options Toolkit
"""

import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
from sklearn.preprocessing import MinMaxScaler
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformerBlock(layers.Layer):
    """Transformer attention block with multi-head attention."""
    
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super().__init__()
        self.att = layers.MultiHeadAttention(
            num_heads=num_heads, 
            key_dim=embed_dim
        )
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output)
        out1 = self.layernorm1(inputs + attn_output)
        
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output)
        return self.layernorm2(out1 + ffn_output)


class LSTMPredictor:
    """
    LSTM-based price predictor for time series forecasting.
    """
    
    def __init__(self, lookback=60, forecast_period=5):
        """
        Initialize LSTM predictor.
        
        Args:
            lookback: Historical window size
            forecast_period: Future periods to predict
        """
        self.lookback = lookback
        self.forecast_period = forecast_period
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        
    def _prepare_data(self, df, lookback=None):
        """Prepare data for LSTM training."""
        if lookback is None:
            lookback = self.lookback
        
        data = df['close'].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(len(scaled_data) - lookback - self.forecast_period):
            X.append(scaled_data[i:i+lookback])
            y.append(scaled_data[i+lookback:i+lookback+self.forecast_period])
        
        return np.array(X), np.array(y)
    
    def build_model(self):
        """Build LSTM model."""
        model = keras.Sequential([
            layers.LSTM(128, activation='relu', input_shape=(self.lookback, 1), return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(64, activation='relu', return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(self.forecast_period, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, df, epochs=25, batch_size=32, validation_split=0.1):
        """
        Train LSTM predictor.
        
        Args:
            df: DataFrame with OHLC data
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation set ratio
        """
        logger.info("Preparing data for LSTM training...")
        X, y = self._prepare_data(df)
        
        logger.info(f"Training set shape: X={X.shape}, y={y.shape}")
        
        self.model = self.build_model()
        
        logger.info("Training LSTM model...")
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        logger.info("LSTM training complete!")
        return history
    
    def predict_next(self, df):
        """
        Predict next prices.
        
        Returns:
            List of predicted prices for next forecast_period
        """
        if self.model is None:
            raise ValueError("Model must be trained first!")
        
        # Use last lookback periods
        recent_data = df['close'].values[-self.lookback:].reshape(-1, 1)
        scaled_data = self.scaler.transform(recent_data)
        
        X = np.array([scaled_data])
        predictions = self.model.predict(X, verbose=0)[0]
        
        # Inverse transform
        predictions = self.scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
        
        # Create forecast dates
        last_date = df.index[-1]
        if hasattr(last_date, 'to_pydatetime'):
            last_date = last_date.to_pydatetime()
        
        forecast_dates = [
            (last_date + timedelta(days=i+1)).isoformat() 
            for i in range(len(predictions))
        ]
        
        return {
            'forecast': predictions.tolist(),
            'forecast_dates': forecast_dates,
            'current_price': float(df['close'].iloc[-1])
        }
    
    def predict_confidence(self, df, num_simulations=100):
        """
        Generate confidence intervals using Monte Carlo simulations.
        
        Returns:
            Predictions with confidence intervals
        """
        if self.model is None:
            raise ValueError("Model must be trained first!")
        
        predictions = []
        
        for _ in range(num_simulations):
            recent_data = df['close'].values[-self.lookback:].reshape(-1, 1)
            scaled_data = self.scaler.transform(recent_data)
            X = np.array([scaled_data])
            pred = self.model.predict(X, verbose=0)[0]
            pred = self.scaler.inverse_transform(pred.reshape(-1, 1)).flatten()
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # Calculate percentiles
        mean_pred = np.mean(predictions, axis=0)
        conf_5 = np.percentile(predictions, 5, axis=0)
        conf_95 = np.percentile(predictions, 95, axis=0)
        
        return {
            'forecast': mean_pred.tolist(),
            'confidence_5': conf_5.tolist(),
            'confidence_95': conf_95.tolist(),
            'current_price': float(df['close'].iloc[-1])
        }


class TransformerPredictor:
    """
    Transformer-based price predictor with attention mechanism.
    """
    
    def __init__(self, lookback=60, forecast_period=5):
        """
        Initialize Transformer predictor.
        
        Args:
            lookback: Historical window size
            forecast_period: Future periods to predict
        """
        self.lookback = lookback
        self.forecast_period = forecast_period
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        
    def _prepare_data(self, df):
        """Prepare data for Transformer training."""
        data = df['close'].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(len(scaled_data) - self.lookback - self.forecast_period):
            X.append(scaled_data[i:i+self.lookback])
            y.append(scaled_data[i+self.lookback:i+self.lookback+self.forecast_period])
        
        return np.array(X), np.array(y)
    
    def build_model(self):
        """Build Transformer model."""
        inputs = layers.Input(shape=(self.lookback, 1))
        
        # Embed input
        x = layers.Dense(64)(inputs)
        
        # Transformer blocks
        for _ in range(2):
            x = TransformerBlock(
                embed_dim=64,
                num_heads=4,
                ff_dim=128,
                rate=0.1
            )(x)
        
        # Global average pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # Dense layers
        x = layers.Dense(32, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        
        # Output
        outputs = layers.Dense(self.forecast_period, activation='sigmoid')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, df, epochs=25, batch_size=32):
        """Train Transformer predictor."""
        logger.info("Preparing data for Transformer training...")
        X, y = self._prepare_data(df)
        
        logger.info(f"Training set shape: X={X.shape}, y={y.shape}")
        
        self.model = self.build_model()
        
        logger.info("Training Transformer model...")
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            verbose=1
        )
        
        logger.info("Transformer training complete!")
        return history
    
    def predict_next(self, df):
        """Predict next prices using Transformer."""
        if self.model is None:
            raise ValueError("Model must be trained first!")
        
        recent_data = df['close'].values[-self.lookback:].reshape(-1, 1)
        scaled_data = self.scaler.transform(recent_data)
        
        X = np.array([scaled_data])
        predictions = self.model.predict(X, verbose=0)[0]
        
        predictions = self.scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
        
        last_date = df.index[-1]
        if hasattr(last_date, 'to_pydatetime'):
            last_date = last_date.to_pydatetime()
        
        forecast_dates = [
            (last_date + timedelta(days=i+1)).isoformat() 
            for i in range(len(predictions))
        ]
        
        return {
            'forecast': predictions.tolist(),
            'forecast_dates': forecast_dates,
            'current_price': float(df['close'].iloc[-1])
        }


class EnsemblePricePredictor:
    """
    Ensemble of LSTM and Transformer models for robust predictions.
    """
    
    def __init__(self, lookback=60, forecast_period=5):
        """Initialize ensemble predictor."""
        self.lookback = lookback
        self.forecast_period = forecast_period
        self.lstm_predictor = LSTMPredictor(lookback, forecast_period)
        self.transformer_predictor = TransformerPredictor(lookback, forecast_period)
        
    def fit(self, df, epochs=25):
        """Train both LSTM and Transformer models."""
        logger.info("Training LSTM predictor...")
        self.lstm_predictor.fit(df, epochs=epochs, batch_size=32)
        
        logger.info("Training Transformer predictor...")
        self.transformer_predictor.fit(df, epochs=epochs, batch_size=32)
        
        logger.info("Ensemble training complete!")
    
    def predict_next(self, df):
        """
        Ensemble prediction combining LSTM and Transformer.
        
        Returns:
            Averaged predictions with model-specific forecasts
        """
        lstm_pred = self.lstm_predictor.predict_next(df)
        transformer_pred = self.transformer_predictor.predict_next(df)
        
        # Average predictions
        ensemble_forecast = (
            np.array(lstm_pred['forecast']) + 
            np.array(transformer_pred['forecast'])
        ) / 2
        
        return {
            'ensemble_forecast': ensemble_forecast.tolist(),
            'lstm_forecast': lstm_pred['forecast'],
            'transformer_forecast': transformer_pred['forecast'],
            'forecast_dates': lstm_pred['forecast_dates'],
            'current_price': lstm_pred['current_price'],
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_with_confidence(self, df):
        """Prediction with confidence bands."""
        predictions = []
        
        # Run multiple predictions
        for _ in range(10):
            pred = self.predict_next(df)
            predictions.append(pred['ensemble_forecast'])
        
        predictions = np.array(predictions)
        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)
        
        return {
            'forecast': mean_pred.tolist(),
            'upper_band': (mean_pred + 1.96 * std_pred).tolist(),
            'lower_band': (mean_pred - 1.96 * std_pred).tolist(),
            'forecast_dates': self.lstm_predictor.predict_next(df)['forecast_dates'],
            'current_price': float(df['close'].iloc[-1])
        }


if __name__ == "__main__":
    print("\nPhase 10: Deep Price Prediction")
    print("=" * 50)
    
    from utils.backtester import HistoricalDataGenerator
    gen = HistoricalDataGenerator()
    df = gen.generate_with_market_events(years=1).tail(500)
    
    # Train ensemble predictor
    ensemble = EnsemblePricePredictor(lookback=60, forecast_period=5)
    ensemble.fit(df, epochs=10)
    
    # Predict
    result = ensemble.predict_next(df)
    print(f"\n📊 Next 5 Days Price Forecast:")
    print(f"   Current Price: ₹{result['current_price']:.2f}")
    print(f"   Ensemble Forecast: {[f'₹{p:.2f}' for p in result['ensemble_forecast']]}")
