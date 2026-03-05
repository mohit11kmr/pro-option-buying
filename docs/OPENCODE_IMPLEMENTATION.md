# OpenCode CLI Implementation Commands - All Phases

Run these commands one-by-one in your terminal. Make sure you're in the project root directory and venv is activated.

---

## 🚀 Phase 9: Live Execution & Order Management

### Step 1: Create Live Order Executor Module
```bash
opencode create src/utils/live_order_executor.py --description "
Create a production-grade live order executor with SmartAPI integration.

Include these classes:
1. LiveOrderExecutor - Main executor with methods:
   - place_live_order(symbol, quantity, order_type, price, stop_loss, target)
   - modify_order(order_id, new_price, new_quantity)
   - cancel_order(order_id)
   - get_position_pnl(symbol)
   - track_active_orders()
   - handle_partial_fills()
   - auto_hedge_position(symbol, hedge_ratio)

2. OrderTracker - Tracks live P&L:
   - track_entry_price(symbol, price)
   - calculate_live_pnl(symbol)
   - get_position_details(symbol)
   - alert_on_target_hit()
   - alert_on_stoploss_hit()

3. PositionManager - Manages positions:
   - get_open_positions()
   - get_margin_usage()
   - calculate_position_size(capital, stop_loss)
   - hedge_position(symbol, direction)

Error handling: SmartAPI connection failures, partial fills, order rejections
Logging: All trades to trades.log with JSON format
"
```

### Step 2: Integrate Live Orders into Flask API
```bash
opencode modify src/web/app.py --description "
Add these new Flask routes for live trading:

1. POST /api/trades/execute-live
   - Accept: {symbol, quantity, entry_price, stop_loss, target}
   - Call LiveOrderExecutor
   - Return: {order_id, status, execution_price}

2. GET /api/trades/live-status
   - Return all active live orders with current P&L

3. PUT /api/trades/close-live/{order_id}
   - Close a specific live order
   - Return final P&L

4. GET /api/positions/margin
   - Return margin used, available, utilization %

5. POST /api/trades/auto-hedge
   - Accept symbol and hedge_ratio
   - Auto-create hedge position

6. WebSocket: /socket.io live P&L stream
   - Emit live_pnl every 500ms for active positions
   - Emit order_filled, order_rejected, order_modified

Import LiveOrderExecutor, PositionManager, OrderTracker
Add error handlers for SmartAPI failures
"
```

### Step 3: Create Live Trading Frontend Dashboard
```bash
opencode create frontend/live-trading.html --description "
Create institutional live trading dashboard with:

1. Active Orders Panel:
   - Table: Symbol | Entry | SL | Target | Current Price | P&L | % Return | Action(Close/Modify)
   - Live updates every 500ms via WebSocket

2. Open Positions Summary:
   - Total capital deployed
   - Total unrealized P&L
   - Max drawdown today
   - Margin utilized / available

3. Order Execution Panel:
   - Quick order form: Symbol | Qty | Entry | SL | Target | Hedge%
   - Execute button with confirmation
   - Recent order history

4. Live P&L Chart:
   - Real-time equity curve
   - Drawdown overlay
   - Entry/exit markers

5. Trade Notifications:
   - Order filled notifications
   - Target hit alerts
   - Stop-loss hit alerts
   - Margin warning alerts

Styling: Green/red for P&L, responsive design
"
```

---

## 🧠 Phase 10: Advanced ML & Regime Detection

### Step 1: Create Market Regime Classifier
```bash
opencode create src/utils/ml/regime_classifier.py --description "
Create market regime detection with:

1. RegimeClassifier class:
   - detect_regime(price_data) -> 'BULL' | 'BEAR' | 'SIDEWAYS'
   - Signals adjust weights based on regime

Methods:
   - RSI oscillator analysis
   - ATR volatility analysis
   - Trend detection (EMA slopes)
   - Volume profile analysis
   - Pattern recognition (Bollinger Band squeezes)

2. RegimeAdapter class:
   - Adjust signal confidence by regime
   - In BULL: trust uptrend signals more
   - In SIDEWAYS: trust mean-reversion signals more
   - In BEAR: trust downtrend signals more

3. Regime Persistence Tracker:
   - How long in current regime?
   - Probability of regime change?
   - Historical regime durations?

Store regime history in database
Return: {regime, confidence, stability_score, expected_duration}
"
```

### Step 2: Create Reinforcement Learning Optimizer
```bash
opencode create src/utils/ml/rl_optimizer.py --description "
Implement RL-based parameter optimization:

1. QLearningOptimizer class:
   - State space: Current market regime, RSI, Volatility
   - Action space: Signal strength (1-10), Risk multiplier (0.5-2.0)
   - Reward: Daily P&L vs max drawdown

Methods:
   - train_on_live_trades(trade_history) 
   - get_optimal_params(current_state) -> params dict
   - update_q_values(state, action, reward)

2. PolicyGradient class:
   - Alternative to Q-learning
   - Policy network learns best action probabilities
   - Trains daily at 3:45 PM

3. Performance Validator:
   - Only apply new policy if Sharpe > 1.0
   - Rollback if loss increases

Training: Daily, uses last 30 days of trades
Logging: Policy changes to policy_history.json
"
```

### Step 3: Create Deep Learning Price Predictor
```bash
opencode create src/utils/ml/deep_price_predictor.py --description "
Implement LSTM + Transformer models:

1. LSTMPricePredictor class:
   - 3-layer LSTM with attention mechanisms
   - Input: 60-minute price history
   - Output: Next 15-min price prediction + confidence

Methods:
   - predict_next_price(price_history) -> {predicted_price, confidence, std_dev}
   - train_on_historical_data(df)
   - evaluate_accuracy(test_df)

2. TransformerPredictor class:
   - Self-attention for capturing long-term dependencies
   - Better for capturing regime changes
   - Multi-head attention (8 heads)

3. EnsemblePricePredictor:
   - Combines LSTM + Transformer
   - Weighted average based on recent accuracy

Training: Daily at 3:45 PM on last 20 days data
Logging: Model accuracy, MAE, RMSE to metrics.json
Model persistence: Save to models/ directory
"
```

### Step 4: Create AI Signal Ensemble
```bash
opencode modify src/utils/ml/signal_generator.py --description "
Enhance signal generator with ensemble methods:

1. Add EnsembleSignalGenerator:
   - Combines 5 independent signals:
     a) Price Predictor (LSTM)
     b) Sentiment Analyzer
     c) Options Flow Analyzer
     d) Volatility Mean-Reversion
     e) Trend Following

2. Add voting mechanism:
   - Majority vote (3+ == strong signal)
   - Weighted vote (by accuracy history)
   - Confidence = number of models agreeing

3. Add drift detection:
   - Monitor signal accuracy daily
   - Alert if accuracy drops below 40%
   - Automatically disable broken models

Return signal with:
   {direction, confidence, ensemble_votes, strongest_signal, weakest_signal}
"
```

---

## 📲 Phase 11: Telegram/Discord Bot Integration

### Step 1: Create Telegram Bot Service
```bash
opencode create src/utils/telegram_bot.py --description "
Create production-grade Telegram bot:

1. TelegramBot class:
   - Command handlers: /start, /status, /execute, /close, /positions, /stats
   - Auto-send trade alerts (order filled, target/SL hit)
   - Auto-send daily summary at 3:45 PM

Methods:
   - send_trade_alert(trade_data)
   - send_position_update(positions)
   - send_daily_summary(pnl_stats)
   - send_risk_alert(alert_type)
   - handle_user_commands(command, args)

2. Command Handlers:
   - /start: Setup & get user ID
   - /status: Current positions with P&L
   - /execute symbol qty entry sl target: Place order via bot
   - /close order_id: Close position via bot
   - /positions: List all open positions
   - /stats: Win rate, profit factor, daily PnL
   - /alerts: View recent alerts

3. Alert Manager:
   - Queue system for alerts
   - Batch alerts if market moving fast
   - Avoid alert spam (max 10 per minute)

4. Message Templates:
   - Trade execution notification
   - Target hit notification
   - Stop-loss hit notification
   - Risk warning notification
   - Daily performance summary

Integration: Send to Flask via webhook
Logging: All messages to telegram.log
"
```

### Step 2: Create Discord Bot
```bash
opencode create src/utils/discord_bot.py --description "
Create Discord bot for trading alerts:

1. DiscordBot class:
   - Same commands as Telegram: /status, /execute, /close, /positions, /stats
   - Rich embeds for visual alerts
   - Channel integration (alerts go to #trading-alerts)

Methods:
   - send_embedded_alert(title, description, color)
   - send_position_table(positions)
   - send_performance_chart(chart_image)
   - handle_slash_commands()

2. Channel Structure:
   - #trading-alerts: All trade notifications
   - #daily-summary: End-of-day stats
   - #risk-warnings: Max loss, margin warnings
   - #trades-log: Detailed trade logs

3. Rich Visualizations:
   - Embed card for each trade
   - Color-coded (green/red)
   - Include entry, target, SL, P&L

Integration: Connect to Flask via Discord.py
Logging: Discord messages to discord.log
"
```

### Step 3: Integrate Bot into Flask
```bash
opencode modify src/web/app.py --description "
Add bot integrations to Flask:

1. New routes:
   - POST /api/telegram/webhook - Telegram webhook endpoint
   - POST /api/discord/webhook - Discord webhook endpoint
   - GET /api/alerts/history - View all alerts sent

2. Background threads:
   - Daily summary at 3:45 PM
   - Position update every 5 minutes
   - Risk alerts on demand

3. Environment variables:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
   - DISCORD_BOT_TOKEN
   - DISCORD_CHANNEL_ID

Import TelegramBot, DiscordBot
Initialize on startup
"
```

---

## 📊 Phase 12: Advanced Backtesting (Monte Carlo, VAR, Stress Tests)

### Step 1: Create Monte Carlo Simulator
```bash
opencode create src/utils/monte_carlo_simulator.py --description "
Implement Monte Carlo simulation for risk analysis:

1. MonteCarloSimulator class:
   - Generate 10,000 random price paths from historical volatility
   - Calculate 95th percentile VAR (Value at Risk)
   - Calculate max expected drawdown

Methods:
   - simulate_trading_paths(num_simulations=10000, days_ahead=30)
   - calculate_var(confidence_level=0.95)
   - calculate_cvar(confidence_level=0.95)
   - get_drawdown_distribution()
   - stress_test_position(entry, sl, target, num_sims)

2. Output:
   - Probability of hitting target
   - Probability of hitting stop-loss
   - Expected return distribution
   - Worst case scenario (worst 5%)
   - Best case scenario (best 5%)

Visualization: Generate histogram of outcomes
Logging: Results to monte_carlo_results.json
"
```

### Step 2: Create Stress Test Module
```bash
opencode create src/utils/stress_tester.py --description "
Create stress testing scenarios:

1. StressTester class:
   - Scenario 1: 2% market gap down (March 2020 COVID style)
   - Scenario 2: 5% flash crash (2010 flash crash)
   - Scenario 3: Range-bound market (sideways 2 weeks)
   - Scenario 4: High volatility (VIX-like environment)
   - Scenario 5: Low volatility (boring market)

Methods:
   - run_stress_scenario(scenario_name, strategy, backtest_data)
   - calculate_max_loss(scenario)
   - estimate_survival_probability(scenario)
   - generate_stress_report()

2. Report includes:
   - Portfolio P&L under each scenario
   - Win rate under each scenario
   - Maximum consecutive loss
   - Expected shortfall

Logging: stress_test_report.json with all scenarios
"
```

### Step 3: Create Walk-Forward + Expanding Window Optimizer
```bash
opencode create src/utils/advanced_backtest_tools.py --description "
Add advanced backtesting techniques:

1. ExpandingWindowOptimizer:
   - Start with first 90 days of data
   - Train model on expanding window (90→120→150 days)
   - Test on next 30 days, don't overlap training

2. WalkForwardAnalyzer:
   - Multi-period walk-forward: 90-day train, 30-day test, shift by 30 days
   - Prevents look-ahead bias
   - More realistic than standard backtest

3. ParameterOptimizer:
   - Grid search optimal parameters
   - Report: parameter sensitivity
   - Identify parameter sweet spots
   - Show performance stability

Methods:
   - optimize_parameters(param_grid, initial_capital)
   - run_walk_forward_test(train_window, test_window)
   - generate_sensitivity_analysis()

Logging: Results to optimization_results.json
"
```

---

## 🏭 Phase 13: Production Deployment (Docker, K8s)

### Step 1: Create Dockerfile for Multi-Stage Build
```bash
opencode create Dockerfile --description "
Create production-grade multi-stage Dockerfile:

Stage 1 - Builder:
   - Python 3.11 slim image
   - Install dependencies from requirements.txt
   - Compile packages

Stage 2 - Runtime:
   - Copy only runtime dependencies
   - Copy source code
   - Set environment variables
   - Expose port 5000
   - Health check: curl /health every 30s

Include:
   - Non-root user 'trading'
   - Volume mounts for /logs, /data, /config
   - Environment variables: FLASK_ENV, DEBUG, LOG_LEVEL
   - CMD: gunicorn --workers 4 --timeout 60 src.web.app:app

Optimize for:
   - Small image size
   - Fast startup
   - Security (non-root)
"
```

### Step 2: Create Docker Compose for Full Stack
```bash
opencode create docker-compose.yml --description "
Create docker-compose.yml with services:

1. Flask Web Service (port 5000):
   - Volume mounts for logs, data, config
   - Environment file: .env
   - Restart policy: always
   - Health check: /health endpoint

2. PostgreSQL Database (port 5432):
   - Image: postgres:15
   - Volume: postgres_data (persistent)
   - Init script: migrations/init.sql (for market snapshots, signals, trades)

3. Redis Cache (port 6379):
   - Image: redis:7-alpine
   - Volume: redis_data (persistent)
   - Used for caching price data

4. ML Training Service (background):
   - Build from same Dockerfile
   - Command: python src/utils/ml/training_worker.py
   - Runs daily retraining

Networks: trading-network (all services connected)
Logging: JSON logs to /logs directory
"
```

### Step 3: Create Kubernetes Deployment Files
```bash
opencode create k8s/deployment.yaml --description "
Create Kubernetes deployment:

1. Deployment:
   - Image: trading-app:latest
   - Replicas: 2 (for HA)
   - Resources: requests (500m CPU, 512Mi RAM), limits (1000m, 1Gi)
   - Liveness probe: /health
   - Readiness probe: /ready
   - Environment: ConfigMap for settings, Secret for credentials

2. Service:
   - Type: LoadBalancer
   - Port 80 -> 5000
   - Session affinity: None (stateless)

3. HorizontalPodAutoscaler:
   - Min replicas: 2
   - Max replicas: 10
   - Target CPU: 70%
   - Target memory: 80%

Include labels: app=nifty-trading, tier=web, env=prod
"
```

### Step 4: Create Kubernetes Database & Redis
```bash
opencode create k8s/statefulset.yaml --description "
Create StatefulSet for PostgreSQL:

1. PostgreSQL StatefulSet:
   - 1 master, 2 replicas
   - PersistentVolume: 50Gi
   - Init container: run migrations
   - Service: trading-db (headless for replicas)

2. Redis StatefulSet:
   - 1 master, 1 replica
   - PersistentVolume: 10Gi
   - Service: trading-cache

3. ConfigMaps:
   - database config
   - Redis config
   - App configuration

Include backup strategy: Daily snapshots
"
```

### Step 5: Create CI/CD Pipeline (GitHub Actions)
```bash
opencode create .github/workflows/deploy.yml --description "
Create GitHub Actions CI/CD pipeline:

Triggers: push to main, PR creation

Jobs:
1. Test:
   - Run pytest with coverage
   - Check code quality (flake8, black)
   - Type checking (mypy)
   - Report coverage to codecov

2. Build:
   - Build Docker image
   - Push to Docker Hub / AWS ECR
   - Tag with git commit hash

3. Deploy:
   - Only on main branch
   - Update Kubernetes deployment
   - Wait for rollout to complete
   - Run smoke tests
   - Slack notification on success/failure

Include: Docker build cache optimization
"
```

---

## 🌐 Phase 14: Ecosystem Integration

### Step 1: Create REST API with OpenAPI/Swagger
```bash
opencode create src/web/api_v2.py --description "
Create comprehensive REST API v2 with OpenAPI docs:

Endpoints:
1. /api/v2/signals/latest - Get latest signal
2. /api/v2/signals/history - Get signal history with filters
3. /api/v2/trades/execute - Execute trade (supports webhook from TradingView)
4. /api/v2/trades/list - List trades with pagination
5. /api/v2/positions/open - Get open positions
6. /api/v2/performance/summary - Daily/weekly/monthly stats
7. /api/v2/alerts/subscribe - Subscribe to webhooks
8. /api/v2/backtest/run - Run backtest with parameters
9. /api/v2/health - Service health check

Documentation: Swagger/OpenAPI 3.0
Authentication: API key in headers
Rate limiting: 100 requests/minute
Response format: JSON with standardized structure
Error codes: 400, 401, 403, 404, 429, 500 with messages

Include pagination, filtering, sorting for all list endpoints
"
```

### Step 2: Create TradingView Integration
```bash
opencode create src/utils/tradingview_integration.py --description "
Create TradingView webhook receiver:

1. TradingViewWebhook class:
   - Listen on /api/webhook/tradingview
   - Receive alerts from TradingView
   - Parse alert message to extract: symbol, action (buy/sell), strategy_name

2. Alert Parser:
   - Extract entry, stop-loss, target from alert message
   - Auto-execute if configured
   - Log all received alerts

3. Methods:
   - verify_webhook_signature(data, signature)
   - parse_alert_message(alert_text)
   - execute_from_tradingview_alert(alert)
   - send_confirmation_back_to_tradingview()

Include: Error handling, duplicate alert prevention, audit logging
"
```

### Step 3: Create 3Commas Integration (Copy Trading)
```bash
opencode create src/utils/threecommas_integration.py --description "
Create 3Commas bot integration:

1. ThreeCommasBot class:
   - Authenticate with 3Commas API
   - Auto-create smart trading bots
   - Receive signals -> auto-create 3Commas orders

Methods:
   - create_smart_trade(entry, take_profit, stop_loss)
   - copy_signal_to_threecommas(signal)
   - get_account_balance()
   - get_open_deals()
   - close_deal(deal_id)

2. Strategy Linking:
   - Link each AI signal to 3Commas smart trade
   - Real-time sync of positions

Include: Error handling, API rate limiting
"
```

### Step 4: Create Multi-Broker Support
```bash
opencode create src/utils/multi_broker_adapter.py --description "
Create abstraction layer for multiple brokers:

1. BrokerAdapter abstract class:
   - place_order(symbol, qty, price, order_type)
   - get_positions()
   - get_balance()
   - modify_order(order_id, new_price)
   - cancel_order(order_id)

2. SmartAPI adapter (implemented)
3. Zerodha adapter (new)
4. Shoonya adapter (new)
5. Mock broker (for testing)

Router:
   - Config selects which broker
   - Seamless switching between brokers
   - Unified position tracking across brokers

Include: Margin calculation per broker, commission handling
"
```

### Step 5: Create API for Strategy Sharing
```bash
opencode create src/web/strategy_marketplace.py --description "
Create strategy marketplace API:

1. Strategy Registry:
   - Save strategy configs to database
   - Version control strategies
   - Rate strategies (1-5 stars)

2. Endpoints:
   - POST /api/marketplace/strategies - Upload strategy
   - GET /api/marketplace/strategies - List all strategies
   - GET /api/marketplace/strategies/{id}/backtest - View backtest
   - POST /api/marketplace/strategies/{id}/subscribe - Subscribe to strategy
   - GET /api/marketplace/performance/{id} - View strategy performance

3. Features:
   - Strategy preview (show parameters)
   - Performance comparison
   - Community ratings
   - Forks and modifications
   - License management

Database: New 'strategies' table with schema
"
```

---

## 📋 EXECUTION SUMMARY

**Total Changes: ~50 new files + 20 modified files**

**Recommended Execution Order:**
1. Phase 9 (Live Execution) - Foundation
2. Phase 10 (Advanced ML) - Intelligence
3. Phase 11 (Bot Integration) - Accessibility
4. Phase 12 (Advanced Backtesting) - Validation
5. Phase 13 (Deployment) - Production
6. Phase 14 (Ecosystem) - Integration

**Estimated Timeline:**
- Phase 9: 2-3 days
- Phase 10: 3-4 days
- Phase 11: 1-2 days
- Phase 12: 2-3 days
- Phase 13: 2-3 days
- Phase 14: 2-3 days

**Total: ~15-20 days of continuous implementation**

Start with: `opencode create src/utils/live_order_executor.py ...`
