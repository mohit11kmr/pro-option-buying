# 🔥 OpenCode Commands - Quick Copy-Paste Reference

## Start Here (Activate venv first!)
```bash
cd '/home/mohit/Desktop/system repair by antigravity/nifty_options (copy 2)/'
source venv/bin/activate
```

---

## PHASE 9: LIVE EXECUTION & ORDER MANAGEMENT

### Command 1: Create Live Order Executor
```bash
opencode create src/utils/live_order_executor.py --description "
Create a production-grade live order executor with SmartAPI integration.

Include these classes:
1. LiveOrderExecutor - Main executor:
   place_live_order(symbol, quantity, order_type, price, stop_loss, target)
   modify_order(order_id, new_price, new_quantity)
   cancel_order(order_id)
   get_position_pnl(symbol)
   track_active_orders()
   handle_partial_fills()
   auto_hedge_position(symbol, hedge_ratio)

2. OrderTracker:
   track_entry_price(symbol, price)
   calculate_live_pnl(symbol)
   get_position_details(symbol)
   alert_on_target_hit()
   alert_on_stoploss_hit()

3. PositionManager:
   get_open_positions()
   get_margin_usage()
   calculate_position_size(capital, stop_loss)
   hedge_position(symbol, direction)

Error handling for SmartAPI, logging to trades.log in JSON format
"
```

### Command 2: Integrate into Flask
```bash
opencode modify src/web/app.py --description "
Add new Flask routes for live trading:
1. POST /api/trades/execute-live -> LiveOrderExecutor.place_live_order()
2. GET /api/trades/live-status -> all active orders with P&L
3. PUT /api/trades/close-live/{order_id} -> close position
4. GET /api/positions/margin -> margin info
5. POST /api/trades/auto-hedge -> create hedge
6. WebSocket /socket.io live_pnl stream every 500ms

Import: from utils.live_order_executor import LiveOrderExecutor, OrderTracker, PositionManager
"
```

### Command 3: Create Live Trading Dashboard
```bash
opencode create frontend/live-trading.html --description "
Create institutional live trading dashboard:
1. Active Orders Panel: Table with Symbol|Entry|SL|Target|Price|P&L|%Return|Actions
2. Position Summary: Total deployed, unrealized PnL, max DD, margin used
3. Quick Order Form: Symbol|Qty|Entry|SL|Target|AutoHedge%, Execute button
4. Live P&L Chart: Real-time equity curve with drawdown overlay
5. Notifications: Order filled, target hit, SL hit, margin warning alerts

Use TradingView Lightweight Charts or Chart.js
Dark theme, monospace for prices, responsive mobile design
"
```

---

## PHASE 10: ADVANCED ML & REGIME DETECTION

### Command 1: Market Regime Classifier
```bash
opencode create src/utils/ml/regime_classifier.py --description "
Create market regime detection:
1. RegimeClassifier:
   detect_regime(price_data, rsi, atr) -> 'BULL'|'BEAR'|'SIDEWAYS'
   Logic: BULL if RSI>60 AND price>EMA200, BEAR if RSI<40 AND price<EMA200, else SIDEWAYS
   get_regime_confidence() -> 0-1
   get_regime_stability() -> bool
   predict_regime_duration() -> days

2. RegimeAdapter:
   adjust_signal_confidence(signal, regime) -> adjusted
   In BULL: uptrend signals +0.3, in BEAR: downtrend +0.3, in SIDEWAYS: mean-reversion +0.3

3. RegimePersistenceTracker:
   track_regime_history(timestamp, regime)
   get_days_in_regime()
   probability_of_regime_change()

Database: regime_history table with timestamp, regime, confidence, atr, rsi
"
```

### Command 2: RL Parameter Optimizer
```bash
opencode create src/utils/ml/rl_optimizer.py --description "
Implement Reinforcement Learning optimizer:
1. QLearningOptimizer:
   State: market_regime, rsi_level, volatility_level, trend_strength
   Action: signal_strength (1-10), risk_multiplier (0.5-2.0)
   Reward: +1 profitable, -1 loss, -0.5 max daily loss exceeded
   Methods: train_on_live_trades(), get_optimal_params(state), update_q_values()

2. PolicyGradient:
   Neural network 2 hidden layers (64 neurons)
   Learn action probability distribution
   Train daily 3:45 PM

3. PerformanceValidator:
   Only apply if Sharpe > 1.0
   Rollback if loss increases
   Keep last 3 policies

Training: Daily on last 30 days trades
"
```

### Command 3: Deep Learning Price Predictor
```bash
opencode create src/utils/ml/deep_price_predictor.py --description "
Implement LSTM + Transformer price prediction:
1. LSTMPricePredictor:
   3-layer LSTM (128 units), Luong attention
   Input: 60-min OHLCV history, Output: next 15-min price + confidence + bounds
   Methods: predict_next_price(), train_on_historical_data(), evaluate_accuracy()
   Loss: MAPE, Optimizer: Adam(0.001), Early stopping: patience=5

2. TransformerPredictor:
   Self-attention (8 heads), Feed-forward (256 units)
   Better long-term dependencies

3. EnsemblePricePredictor:
   LSTM (weight 0.6) + Transformer (0.4)
   Dynamic weight adjustment based on accuracy

Training: Daily 3:45 PM on last 20 days
Models saved to models/lstm_latest.h5, models/transformer_latest.h5
"
```

### Command 4: Enhance Signal Generator
```bash
opencode modify src/utils/ml/signal_generator.py --description "
Add ensemble and drift detection:
1. EnsembleSignalGenerator:
   5 signals vote: Price Predictor, Sentiment, Options Flow, Volatility Mean-Reversion, Trend
   Majority vote (3+ = strong signal)
   Consensus threshold: need 3/5 signals
   Return: {direction, confidence, votes, strongest_signal, weakest_signal}

2. DriftDetector:
   Monitor daily accuracy per signal
   Alert if accuracy < 40%
   Auto-disable broken models
   get_health_report()

Enhanced return: Include regime, consensus, prediction_accuracy, risk_reward_ratio
"
```

---

## PHASE 11: TELEGRAM/DISCORD BOT INTEGRATION

### Command 1: Telegram Bot
```bash
opencode create src/utils/telegram_bot.py --description "
Create Telegram bot:
1. TelegramBot:
   Methods: send_message(), send_alert(), send_trade_notification()
   Commands: /start, /status, /execute SYMBOL QTY ENTRY SL TARGET, /close ORDER_ID
   /positions, /stats, /alerts, /help

2. AlertManager:
   Queue system (max 10/min to avoid spam)
   Alert types: TRADE_EXECUTED, TARGET_HIT, STOPLOSS_HIT, MARGIN_WARNING, DAILY_SUMMARY
   Batch alerts if market fast moving
   Deduplication: no duplicate in 1 min

3. Message Templates:
   ✅ TRADE EXECUTED: Symbol, Entry, SL, Target, Qty, Time
   🎯 TARGET HIT: Symbol, Target, Actual, Profit, Time Held
   ❌ STOP-LOSS HIT: Symbol, SL, Actual, Loss, Time Held
   📊 DAILY SUMMARY: Trades, Win Rate, PnL, Profit Factor, Max DD
   ⚠️ MARGIN ALERT: Margin Used %, Available, Action

Environment: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID from .env
"
```

### Command 2: Discord Bot
```bash
opencode create src/utils/discord_bot.py --description "
Create Discord bot:
1. DiscordBot with same commands as Telegram
2. Rich embeds (color-coded: green profit, red loss, yellow warning)
3. Channels: #trading-alerts, #daily-summary, #risk-warnings, #trades-log, #commands
4. Methods: send_embedded_alert(), send_position_table(), send_performance_chart()
5. Each trade notification is rich embed card with fields

Environment: DISCORD_BOT_TOKEN, DISCORD_SERVER_ID, DISCORD_CHANNEL_IDS from .env
"
```

### Command 3: Flask Integration
```bash
opencode modify src/web/app.py --description "
Add to Flask:
1. Routes:
   POST /api/telegram/webhook
   POST /api/discord/webhook
   GET /api/alerts/history
   POST /api/alerts/test

2. Background threads:
   telegram_listener_thread
   discord_listener_thread
   daily_summary_thread (3:45 PM)
   position_update_thread (every 5 min)

3. Alert dispatcher: Send to both platforms
   - TRADE_EXECUTED -> both
   - TARGET_HIT -> both + email
   - STOPLOSS_HIT -> both + email
   - MARGIN_WARNING -> both + sound
   - DAILY_SUMMARY -> both (formatted)

Initialize on startup: init_bot_threads()
"
```

---

## PHASE 12: ADVANCED BACKTESTING

### Command 1: Monte Carlo Simulator
```bash
opencode create src/utils/monte_carlo_simulator.py --description "
Implement Monte Carlo (10,000 simulations):
1. MonteCarloSimulator:
   Geometric Brownian Motion: dS = μ*S*dt + σ*S*dW
   Methods: simulate_trading_paths(), calculate_var(95%), calculate_cvar(), stress_test_position()
   Output: {var_95, var_99, cvar_95, probability_target, probability_sl, max_dd_avg, best/worst_case, ev}

2. PathAnalyzer:
   get_percentile_path(percentile)
   visualize_cone_chart()
   track_path_statistics()

3. RiskReport:
   generate_summary_report()
   export_to_json()
   generate_visual_report() with charts

Vectorized with NumPy, 10k simulations in < 1 second
Database: monte_carlo_results table
"
```

### Command 2: Stress Tester
```bash
opencode create src/utils/stress_tester.py --description "
Create stress testing (5 scenarios):
1. COVID_CRASH: 20% gap down
2. FLASH_CRASH: 5% spike + recovery
3. RANGE_BOUND: 2 weeks sideways (ATR/2)
4. HIGH_VOLATILITY: 2x volatility
5. LOW_VOLATILITY: 0.5x volatility

Methods: run_stress_scenario(), calculate_max_loss(), estimate_survival_probability()
Output per scenario: Win rate, avg loss, max loss, recovery time
Generate report: Impact table, scoring, recommendations

Database: stress_test_results table
"
```

### Command 3: Advanced Backtest Tools
```bash
opencode create src/utils/advanced_backtest_tools.py --description "
Advanced techniques:
1. ExpandingWindowOptimizer:
   Train 90d → Test 30d, Expand to 120d → Test 120-150, repeat
   Output: consistency score, average performance

2. WalkForwardAnalyzer:
   Train 90d → Test 30d, Roll by 30d (90-120 vs 121-150)
   get_walk_forward_pe()

3. ParameterOptimizer:
   grid_search(param_grid) for all combinations
   random_search(param_space, num_trials=1000)
   bayesian_optimization(param_space, iterations=100)
   Output: best parameters, sensitivity analysis, sweet_spot

4. PerformanceAnalyzer:
   Metrics: Sharpe, Sortino, Calmar, Profit Factor, Win Rate, Max DD, Consecutive streaks
   Visualization: P&L curve, drawdown, monthly heatmap, underwater plot, rolling Sharpe
"
```

---

## PHASE 13: PRODUCTION DEPLOYMENT

### Command 1: Dockerfile
```bash
opencode create Dockerfile --description "
Multi-stage Docker build:
FROM python:3.11-slim as builder (build dependencies)
FROM python:3.11-slim (runtime, non-root user 'trading')

Features:
- Minimal image size
- Non-root user for security
- Health check: curl /health every 30s
- CMD: gunicorn --workers 4 --timeout 60
- Volumes: /app/logs, /app/data, /app/models
- ENV: FLASK_ENV, LOG_LEVEL, etc
"
```

### Command 2: Docker Compose
```bash
opencode create docker-compose.yml --description "
Full stack with 4 services:
1. web (Flask): port 5000, env from .env, healthcheck
2. db (PostgreSQL): port 5432, postgres_data volume, init migrations
3. cache (Redis): port 6379, redis_data volume
4. ml-trainer (background): training_worker.py

Network: trading-network
Environment: DATABASE_URL, REDIS_URL, etc from .env
"
```

### Command 3: Kubernetes Deployment
```bash
opencode create k8s/deployment.yaml --description "
K8s deployment:
- Replicas: 2
- Auto-scale: 2-10 pods
- Resources: request 500m CPU/512Mi RAM, limit 1000m/1Gi
- Probes: Liveness, Readiness
- Service: LoadBalancer on port 80
- HorizontalPodAutoscaler: CPU 70%, Memory 80%
"
```

### Command 4: Kubernetes StatefulSet
```bash
opencode create k8s/statefulset.yaml --description "
StatefulSets:
1. PostgreSQL: 1 master, 50Gi PV, init migrations
2. Redis: 1 deployment, 10Gi PV

Services: Headless for replicas, LoadBalancer for access
"
```

### Command 5: GitHub Actions CI/CD
```bash
opencode create .github/workflows/deploy.yml --description "
CI/CD Pipeline:
1. Test: pytest, coverage, black, flake8, mypy
2. Build: Docker build & push to GHCR
3. Deploy (on main): kubectl set image, rollout status, smoke tests
4. Notify: Slack webhook

Triggers: push to main/develop, PRs
"
```

---

## PHASE 14: ECOSYSTEM INTEGRATION

### Command 1: REST API v2
```bash
opencode create src/web/api_v2.py --description "
Complete REST API v2 with OpenAPI:
Endpoints (20+):
- GET /api/v2/signals/latest
- GET /api/v2/signals/history
- POST /api/v2/trades/execute
- GET /api/v2/trades/list
- PUT /api/v2/trades/{id}
- DELETE /api/v2/trades/{id}
- GET /api/v2/positions/open
- GET /api/v2/positions/{symbol}
- GET /api/v2/performance/summary
- GET /api/v2/performance/equity-curve
- POST /api/v2/backtest/run
- GET /api/v2/backtest/{id}
- POST /api/v2/alerts/subscribe
- GET /api/v2/health, /api/v2/ready

Auth: X-API-Key header
Rate: 100 req/min per key
Docs: Swagger at /api/v2/docs, ReDoc at /api/v2/redoc
"
```

### Command 2: TradingView Integration
```bash
opencode create src/utils/tradingview_integration.py --description "
TradingView webhook receiver:
1. TelegramViewWebhook:
   POST /api/webhook/tradingview
   
2. AlertParser:
   Parse JSON or text messages
   Extract: action (BUY/SELL), entry, SL, target, qty
   
3. ExecutionLogic:
   Auto-execute or manual approval
   Use LiveOrderExecutor
   
4. AuditLogging:
   tradingview_alerts table
   timestamp, strategy_name, symbol, action, executed, execution_price
   
5. DuplicatePrevention:
   alert_hash, don't execute within 1 min
"
```

### Command 3: 3Commas Integration
```bash
opencode create src/utils/threecommas_integration.py --description "
3Commas smart trade creation:
1. ThreeCommasBot:
   Auth with API key/secret
   create_smart_trade(entry, tp, sl, pair)
   link_signal_to_threecommas(signal)
   get_account_balance(), get_open_deals(), close_deal()
   
2. SmartTradeBuilder:
   Convert signal params to 3Commas format
   
3. SyncManager:
   Real-time position sync
   Detect discrepancies
   
4. RiskManagement:
   Max positions, max leverage, portfolio allocation

Environment: THREECOMMAS_API_KEY, THREECOMMAS_API_SECRET
"
```

### Command 4: Multi-Broker Adapter
```bash
opencode create src/utils/multi_broker_adapter.py --description "
Broker abstraction layer:
1. BrokerAdapter (abstract):
   place_order(), modify_order(), cancel_order()
   get_positions(), get_balance(), get_margin_info()

2. SmartAPIAdapter (Angel)
3. ZerodhaAdapter (Kite)
4. ShonyaAdapter (legacy)
5. PaperTradingAdapter (mock)

6. BrokerRouter:
   primary=smartapi, fallback=shoonya
   Auto-switch on failure
   
Config (config.yaml): broker settings, API keys
"
```

### Command 5: Strategy Marketplace
```bash
opencode create src/web/strategy_marketplace.py --description "
Strategy sharing platform:
Endpoints:
- POST /api/marketplace/strategies (save strategy)
- GET /api/marketplace/strategies (list all)
- GET /api/marketplace/strategies/{id} (full details)
- GET /api/marketplace/strategies/{id}/backtest
- POST /api/marketplace/strategies/{id}/subscribe
- GET /api/marketplace/performance/{id}
- POST /api/marketplace/strategies/{id}/fork
- POST /api/marketplace/strategies/{id}/rate

Features: Registry, versioning, ratings, subscriptions, fork, comparison
Database: strategies, strategy_versions, subscriptions, ratings, comments, performance_history
"
```

---

## 🚀 Execute All at Once

```bash
# Phase 9
bash run_phase_9.sh

# Phase 10
bash run_phase_10.sh

# Phase 11
bash run_phase_11.sh

# Phase 12
bash run_phase_12.sh

# Phase 13
bash run_phase_13.sh

# Phase 14
bash run_phase_14.sh
```

---

## ✅ Verify Implementation

```bash
# Start Flask
python src/web/app.py

# Check endpoints
curl http://localhost:5000/api/v2/health

# View Swagger docs
curl http://localhost:5000/api/v2/docs

# Run tests
pytest test/ -v --cov=src

# Docker build
docker build -t nifty-trading:latest .
docker-compose up -d

# Kubernetes
kubectl apply -f k8s/
kubectl get pods
```

---

**Total: ~65 files | ~45,000 lines of code | 15-20 hours of implementation** 🎉

Good luck! The system will be enterprise-ready. 🚀
