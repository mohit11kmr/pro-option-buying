#!/bin/bash
# Phase 10: Advanced ML & Regime Detection
# Copy & paste commands one-by-one

echo "Starting Phase 10: Advanced ML & Regime Detection..."
echo "======================================================"

# Command 1: Market Regime Classifier
echo "[1/4] Creating Market Regime Classifier..."
opencode create src/utils/ml/regime_classifier.py --description "
Create market regime detection system:

1. RegimeClassifier class:
   - detect_regime(price_data, rsi, atr, trend) -> returns 'BULL' | 'BEAR' | 'SIDEWAYS'
   - _analyze_rsi_pattern(rsi_series)
   - _analyze_volatility_pattern(atr_series)
   - _detect_bollinger_squeeze()
   
   Logic:
   - BULL: RSI > 60 AND price > EMA200 AND ATR increasing
   - BEAR: RSI < 40 AND price < EMA200 AND ATR high
   - SIDEWAYS: RSI between 40-60 OR Bollinger Band squeeze

Methods:
   - get_regime_confidence() -> float (0-1)
   - get_regime_stability() -> bool (stable or changing?)
   - predict_regime_duration() -> int days

2. RegimeAdapter class:
   - adjust_signal_confidence(signal, regime) -> adjusted_confidence
   - adjust_signal_weights(regime) -> weight dict
   
   In BULL regime: uptrend signals weight +0.3
   In BEAR regime: downtrend signals weight +0.3
   In SIDEWAYS: mean-reversion signals weight +0.3

3. RegimePersistenceTracker:
   - track_regime_history(timestamp, regime)
   - get_days_in_regime()
   - get_average_regime_duration()
   - probability_of_regime_change()

4. Database Integration:
   - Store regime_history table: timestamp, regime, confidence, atr, rsi
   - Log regime changes to market.log

Return format:
   {
     'regime': 'BULL',
     'confidence': 0.87,
     'stability': True,
     'days_in_regime': 5,
     'probability_change': 0.15,
     'strength_score': 8.2
   }
"

echo "✅ Step 1 Completed!"
echo ""

# Command 2: Reinforcement Learning Optimizer
echo "[2/4] Creating RL-Based Parameter Optimizer..."
opencode create src/utils/ml/rl_optimizer.py --description "
Implement Reinforcement Learning parameter optimization:

1. QLearningOptimizer class:
   State space:
   - market_regime (BULL=0, BEAR=1, SIDEWAYS=2)
   - rsi_level (0-100)
   - volatility_level (0-5 scale)
   - trend_strength (0-1)
   
   Action space:
   - signal_strength (1-10 multiplier)
   - risk_multiplier (0.5-2.0)
   
   Reward:
   - +1 for profitable trade
   - -1 for losing trade
   - -0.5 for exceeded max daily loss

Methods:
   - initialize_q_table(state_space, action_space)
   - train_on_live_trades(trade_history)
   - get_optimal_params(current_state) -> {signal_strength, risk_multiplier}
   - update_q_values(state, action, reward, next_state)
   - epsilon_greedy_action_selection(state, epsilon=0.1)
   
   Hyperparameters:
   - learning_rate: 0.1
   - discount_factor: 0.95
   - epsilon: 0.1 (exploration rate)

2. PolicyGradient class:
   - Neural network: 2 hidden layers (64 neurons each)
   - Policy network learns action probability distribution
   - Loss: policy gradient loss + entropy regularization
   
Methods:
   - train_policy(trajectory) -> loss
   - get_policy_action_distribution(state) -> probabilities
   - update_policy_weights()

3. Performance Validator:
   - Only apply new policy if:
     a) Sharpe Ratio > 1.0
     b) Loss during test period < 5%
     c) Win rate > 40%
   - Rollback to previous policy if criteria not met
   - Version control: keep last 3 policies

4. Training Schedule:
   - Daily at 3:45 PM (after market hours)
   - Uses last 30 days of live trades
   - Logs policy changes to policy_history.json
   - Alert user of policy updates

Database: 
   - Store q_table as JSON blob
   - Store policy_version, performance metrics
"

echo "✅ Step 2 Completed!"
echo ""

# Command 3: Deep Learning Price Predictor
echo "[3/4] Creating Deep Learning Price Predictor..."
opencode create src/utils/ml/deep_price_predictor.py --description "
Implement LSTM + Transformer price prediction:

1. LSTMPricePredictor class:
   - Architecture: 3-layer LSTM with 128 hidden units
   - Attention mechanism: Luong attention
   - Dropout: 0.2 per layer
   
   Input: 60-minute OHLCV history (last 60 candles)
   Output: Next 15-min price prediction + confidence + std_dev
   
Methods:
   - predict_next_price(price_history) -> {'price': float, 'confidence': float, 'upper_bound': float, 'lower_bound': float}
   - train_on_historical_data(df, epochs=50, batch_size=32)
   - evaluate_accuracy(test_df) -> {'mae': float, 'rmse': float, 'mape': float}
   - get_model_summary()
   
   Training details:
   - Loss function: Mean Absolute Percentage Error (MAPE)
   - Optimizer: Adam (lr=0.001)
   - Early stopping: patience=5
   - Training/Validation split: 80/20

2. TransformerPredictor class:
   - Self-attention mechanism with 8 heads
   - Feed-forward network: 256 hidden units
   - Better captures long-term dependencies
   - Positional encoding: Sinusoidal
   
Methods:
   - predict_next_price(price_history) -> same output format
   - train_on_historical_data(df)
   - get_attention_weights() -> visualization data

3. EnsemblePricePredictor:
   - Combines LSTM (weight 0.6) + Transformer (weight 0.4)
   - Weighted average based on recent accuracy
   - Dynamic weight adjustment: Higher weight to recent winners
   
Methods:
   - predict_next_price(price_history) -> ensemble prediction
   - update_model_weights(recent_accuracy_lstm, recent_accuracy_transformer)
   - get_individual_predictions() -> {'lstm': float, 'transformer': float, 'ensemble': float}

4. Training & Persistence:
   - Daily retraining at 3:45 PM
   - Load last 20 days of data
   - Save models to models/lstm_latest.h5, models/transformer_latest.h5
   - Log metrics to predictions_metrics.json
   - Versioning: Keep last 3 model versions

5. Confidence Scoring:
   - Confidence = 1 - (prediction_error / std_dev)
   - Return bounds: prediction ± (1.96 * std_dev) for 95% CI

Database:
   - prediction_history table: timestamp, predicted_price, actual_price, confidence
   - model_performance table: model_name, accuracy_score, training_date
"

echo "✅ Step 3 Completed!"
echo ""

# Command 4: Enhanced Signal Generator with Ensemble
echo "[4/4] Enhancing Signal Generator with Ensemble Methods..."
opencode modify src/utils/ml/signal_generator.py --description "
Enhance signal generator with ensemble and drift detection:

1. Add EnsembleSignalGenerator class:
   Combines 5 independent signals with voting:
   - Price Predictor Signal (LSTM): bullish/bearish/neutral
   - Sentiment Analyzer Signal: bullish/bearish/neutral
   - Options Flow Analyzer Signal: bullish/bearish/neutral
   - Volatility Mean-Reversion Signal: bullish/bearish/neutral
   - Trend Following Signal: bullish/bearish/neutral

Methods:
   - generate_ensemble_signal(market_data) -> signal
   - get_signal_votes() -> {bullish: 4, bearish: 1, neutral: 0}
   - calculate_consensus_confidence() -> float (0-1)
   - get_strongest_signal() -> signal_name
   - get_weakest_signal() -> signal_name

Voting Logic:
   - Majority vote: 3+ votes = strong signal
   - Weighted vote: Recent accurate signals get higher weight
   - Consensus threshold: Need 3/5 signals agreeing for trade
   - Confidence: (agreeing_signals / 5) * 100

2. Add DriftDetector class:
   - Monitor signal accuracy daily
   - Track each signal's win rate (target hit vs not hit)
   - Alert if accuracy drops below 40% threshold
   - Automatically disable broken models

Methods:
   - calculate_model_accuracy(model_name, recent_trades)
   - detect_accuracy_drift(threshold=0.4)
   - flag_broken_model(model_name)
   - get_health_report() -> {signal_name: accuracy, status}

3. Enhanced Return Signal Format:
   {
     'direction': 'BUY',  // or SELL, HOLD
     'confidence': 0.87,  // 0-1 scale
     'ensemble_votes': {'bullish': 4, 'bearish': 1, 'neutral': 0},
     'strongest_signal': 'price_predictor',
     'weakest_signal': 'volatility_mean_reversion',
     'consensus': 'Strong Bullish (4/5 signals)',
     'entry_price': 24800,
     'stop_loss': 24650,
     'target': 24950,
     'risk_reward_ratio': 2.0,
     'regime': 'BULL',
     'regime_confidence': 0.87,
     'prediction_accuracy': 0.78,
     'timestamp': '2026-03-05T10:15:00Z'
   }

4. Integration with RegimeClassifier:
   - Adjust signal weights based on market regime
   - Show regime context in signal output
   - Filter signals: only take strong signals in trending markets

5. Logging & Monitoring:
   - Log all signals to signals.log
   - Track signal performance over time
   - Generate daily signal accuracy report
   - Alert on model health issues
"

echo "✅ Step 4 Completed!"
echo ""
echo "======================================================"
echo "✅ Phase 10 Complete! Advanced ML system created."
echo ""
echo "Key Features Added:"
echo "  ✓ Market Regime Detection (BULL/BEAR/SIDEWAYS)"
echo "  ✓ Reinforcement Learning Parameter Optimization"
echo "  ✓ Deep Learning LSTM + Transformer Predictors"
echo "  ✓ Ensemble Signal Generation with 5 Experts"
echo "  ✓ Model Drift Detection & Auto-Disable"
echo ""
echo "Next: Run Phase 11 (Telegram/Discord Bot Integration)"
echo ""
