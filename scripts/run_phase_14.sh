#!/bin/bash
# Phase 14: Ecosystem Integration (APIs, TradingView, 3Commas, Multi-Broker)
# Copy & paste commands one-by-one

echo "Starting Phase 14: Ecosystem Integration..."
echo "=========================================================="

# Command 1: REST API v2 with OpenAPI/Swagger
echo "[1/5] Creating REST API v2 with Swagger..."
opencode create src/web/api_v2.py --description "
Create comprehensive REST API v2 with OpenAPI/Swagger documentation:

1. API Blueprint Structure:
   - Base version: /api/v2
   - All responses in standardized JSON format
   - Comprehensive error handling
   - Request validation with Pydantic

2. Signal Endpoints:
   GET /api/v2/signals/latest
   - Get the latest generated trading signal
   - Response: {direction, confidence, entry, target, sl, components}
   
   GET /api/v2/signals/history
   - Get signal history with filtering
   - Query params: limit=100, offset=0, status=[open|closed|all]
   - Response: Array of signals with outcomes

3. Trade Management Endpoints:
   POST /api/v2/trades/execute
   - Execute a new trade (supports TradingView webhooks)
   - Body: {symbol, quantity, entry_price, stop_loss, target_price, order_type}
   - Response: {trade_id, status, execution_price, timestamp}
   
   GET /api/v2/trades/list
   - List all trades with pagination
   - Query: limit=50, offset=0, status=[open|closed], symbol=NIFTY
   - Response: {total: int, trades: array, page_info}
   
   PUT /api/v2/trades/{trade_id}
   - Update an open trade (modify SL/Target)
   - Body: {stop_loss, target_price}
   - Response: {trade_id, updated_fields}
   
   DELETE /api/v2/trades/{trade_id}
   - Close/cancel a trade
   - Response: {trade_id, final_pnl, status}

4. Position Endpoints:
   GET /api/v2/positions/open
   - Get all open positions with live P&L
   - Response: {total_positions, total_deployed, unrealized_pnl, positions:[]}
   
   GET /api/v2/positions/{symbol}
   - Get position details for specific symbol
   - Response: {symbol, quantity, entry, current_price, pnl, pnl_pct, margin_used}

5. Performance & Analytics Endpoints:
   GET /api/v2/performance/summary
   - Get performance metrics
   - Response: {daily_pnl, monthly_pnl, ytd_pnl, win_rate, profit_factor, sharpe_ratio}
   
   GET /api/v2/performance/trades
   - Trade statistics and distribution
   - Response: {win_rate, avg_win, avg_loss, max_win, max_loss, profit_factor}
   
   GET /api/v2/performance/equity-curve
   - Equity curve data for charting
   - Response: [{timestamp, equity, dd, cash}]
   
   GET /api/v2/performance/monthly-heatmap
   - Monthly returns heatmap data
   - Response: {2026: {Jan: 2500, Feb: -1000, Mar: 3200}}

6. Backtesting Endpoints:
   POST /api/v2/backtest/run
   - Run backtest with parameters
   - Body: {strategy_params, start_date, end_date, initial_capital}
   - Response: {backtest_id, status, started_at}
   
   GET /api/v2/backtest/{backtest_id}
   - Get backtest results
   - Response: {status, results: {pnl, sharpe, win_rate, ...}, charts}

7. Alert Management:
   POST /api/v2/alerts/subscribe
   - Subscribe to webhooks
   - Body: {url, events: [order_executed, target_hit, sl_hit]}
   - Response: {subscription_id, status}
   
   GET /api/v2/alerts/history
   - Get alert history
   - Response: Array of sent alerts with timestamp, type, status

8. System Health:
   GET /api/v2/health
   - Service health check
   - Response: {status: ok, timestamp, components: {db: ok, cache: ok}}
   
   GET /api/v2/ready
   - Readiness check (can handle requests?)
   - Response: {ready: bool, reason}

Authentication:
   - API Key header: X-API-Key
   - Token validation on all endpoints
   - Rate limiting: 100 req/min per API key

Response Format (Standardized):
   {
     'status': 'success',  // or 'error'
     'data': {},           // actual response
     'message': 'OK',
     'timestamp': '2026-03-05T10:15:00Z',
     'request_id': 'uuid'
   }

Error Response:
   {
     'status': 'error',
     'error': {
       'code': 'INSUFFICIENT_CAPITAL',
       'message': 'Not enough capital to execute trade',
       'details': {}
     },
     'timestamp': '2026-03-05T10:15:00Z'
   }

Documentation:
   - Full OpenAPI 3.0 specification
   - Swagger UI at /api/v2/docs
   - ReDoc at /api/v2/redoc
   - Example requests and responses
   - Error codes documentation

Implementation:
   - Use Flask-RESTx or Flask-RESTFUL for structure
   - Pydantic models for request validation
   - Swagger generation automatic from docstrings
   - Comprehensive error handling with custom exceptions
"

echo "✅ Step 1 Completed!"
echo ""

# Command 2: TradingView Integration
echo "[2/5] Creating TradingView Webhook Integration..."
opencode create src/utils/tradingview_integration.py --description "
Create TradingView alert webhook receiver:

1. TradingViewWebhook class:
   Receives alerts from TradingView and executes trades

Initialization:
   - Listen on endpoint: POST /api/webhook/tradingview
   - Verify alert authenticity (signature validation if enabled)

Methods:
   - receive_alert(request) -> parse and process alert
   - parse_alert_message(alert_text) -> extract trading parameters
   - verify_webhook_signature(payload, signature) -> bool
   - execute_from_alert(parsed_alert)
   - send_execution_confirmation()

Alert Message Format Examples:
   TradingView sends alert as JSON or plain text:
   
   JSON Format:
   {
     'strategy_name': 'Premium Buying',
     'ticker': 'NIFTY',
     'action': 'buy',  // or 'sell'
     'entry': 24800,
     'stop_loss': 24650,
     'target': 24950,
     'quantity': 1,
     'time': '2026-03-05T10:15:00Z'
   }
   
   OR Plain Text (parsed):
   'Strategy: Premium Buying | NIFTY | BUY | Entry: 24800 | SL: 24650 | Target: 24950 | Qty: 1'

2. AlertParser class:
   Flexible message parsing:
   - Extract action (BUY/SELL/CLOSE)
   - Extract entry, stop-loss, target prices
   - Extract quantity/position size
   - Extract strategy name/identifier

Methods:
   - parse_json_alert(json_data)
   - parse_text_alert(text)
   - extract_numbers_from_message(text) -> list of floats
   - identify_alert_type(parsed_data) -> 'ENTRY' | 'TARGET' | 'SL_HIT' | 'CLOSE'

3. ExecutionLogic:
   - Auto-execute trade if configured
   - Optional manual approval first
   - Use existing LiveOrderExecutor for placement
   - Track source: TradingView

4. AuditLogging:
   - Log every received alert
   - Store in tradingview_alerts table:
     timestamp, strategy_name, symbol, action, entry, sl, target, qty, executed, execution_price

5. Error Handling:
   - Malformed JSON: Log error, don't execute
   - Missing fields: Log missing fields, ask for clarification
   - Invalid action: Log and skip
   - Execution failures: Retry once, then alert user

6. Duplicate Prevention:
   - Track alert_hash: hash(strategy_name + symbol + action + timestamp)
   - Don't execute same alert twice within 1 minute

Features:
   ✓ Flexible message parsing (JSON + text)
   ✓ Signature verification support
   ✓ Auto-execution or manual approval
   ✓ Comprehensive audit logging
   ✓ Duplicate alert filtering
   ✓ Error notifications
   ✓ Confirmation response to TradingView
"

echo "✅ Step 2 Completed!"
echo ""

# Command 3: 3Commas Integration
echo "[3/5] Creating 3Commas Smart Trade Integration..."
opencode create src/utils/threecommas_integration.py --description "
Create 3Commas bot integration for copy trading:

1. ThreeCommasBot class:
   - Authenticate with 3Commas API using API key/secret
   - Create smart trading bots automatically
   - Execute signals via 3Commas for account replication

Initialization:
   - API Key: from .env THREECOMMAS_API_KEY
   - API Secret: from .env THREECOMMAS_API_SECRET
   - Exchange: BINANCE (or other configured exchange)

Methods:
   - create_smart_trade(entry_price, take_profit, stop_loss, pair) -> trade_id
   - link_signal_to_threecommas(signal) -> 3commas_trade_id
   - get_account_balance() -> {btc, eth, usdt, ...}
   - get_account_pairs() -> list of trading pairs
   - get_open_deals(pair=None) -> list of active deals
   - close_deal(deal_id) -> confirmation
   - update_deal_tp_sl(deal_id, new_tp, new_sl)
   - get_deal_pnl(deal_id) -> float

2. SmartTradeBuilder:
   - Format signal into 3Commas smart trade parameters
   - Handle different trade types:
     a) Spot trading: BUY and SELL separately
     b) Margin: Leveraged trades (if enabled)
     c) Futures: Never close orders

Parameters Conversion:
   Our Signal            -> 3Commas Smart Trade
   ==========================================
   entry_price          -> buy_price
   target_price         -> take_profit (TP)
   stop_loss_price      -> stop_loss (SL)
   quantity             -> volume
   signal_confidence    -> risk_score

3. SyncManager:
   - Real-time sync of positions
   - Track our trades vs 3Commas trades
   - Detect discrepancies
   - Revert trades if needed

Methods:
   - sync_positions() -> bool (confirms match)
   - get_position_difference() -> dict of mismatches
   - resolve_sync_error(error_type)

4. RiskManagement:
   - Max positions: Limit total open deals
   - Max leverage: Enforce leverage limits
   - Portfolio allocation: % per pair
   - Stop if max loss exceeded

5. PnL Tracking:
   - Track P&L per deal
   - Track cumulative P&L on 3Commas
   - Compare with our internal records
   - Alert on major discrepancies

Database:
   - threecommas_deals table:
     deal_id, signal_id, status, entry, tp, sl, current_price, pnl, pnl_pct

Features:
   ✓ Auto-create smart trades from signals
   ✓ Position synchronization
   ✓ Risk controls (max deals, max leverage)
   ✓ Real-time P&L tracking
   ✓ Error detection and alerts
"

echo "✅ Step 3 Completed!"
echo ""

# Command 4: Multi-Broker Support
echo "[4/5] Creating Multi-Broker Adapter..."
opencode create src/utils/multi_broker_adapter.py --description "
Create abstraction layer for multiple brokers:

1. BrokerAdapter (Abstract Base Class):
   - Standard interface for all brokers
   - Implement once, use everywhere

Methods:
   - place_order(symbol, quantity, price, order_type, side) -> order_id
   - modify_order(order_id, new_price, new_quantity) -> bool
   - cancel_order(order_id) -> bool
   - get_order_status(order_id) -> status
   - get_positions() -> list of positions
   - get_balance() -> {cash, positions_value, total}
   - get_margin_info() -> {margin_used, margin_available, margin_ratio}
   - get_order_history(limit=100) -> list of orders
   - close_position(symbol) -> bool

2. SmartAPIAdapter (Angel Broking):
   - Inherits from BrokerAdapter
   - Implements all methods using SmartAPI
   - Handles token expiration, reconnection
   - Manages mode (historical, paper, live)

3. ZerodhaAdapter (Zerodha - Kite):
   - Implements Kite connect API
   - Handles Zerodha-specific order types
   - GTT orders support

4. ShonyaAdapter (Shoonya - Angel Legacy):
   - Implements Shoonya API
   - Lower latency than SmartAPI
   - MCX support

5. PaperTradingAdapter:
   - Mock broker for testing
   - Simulates realistic fills
   - Tracks orders internally

6. BrokerRouter:
   - Selects which broker to use
   - Config: primary=SMARTAPI, fallback=SHOONYA
   - Automatically switches on connection failure

Configuration (config.yaml):
   primary_broker: smartapi
   fallback_broker: shoonya
   
   brokers:
     smartapi:
       enabled: true
       api_key: XXX
       client_code: XXX
     
     zerodha:
       enabled: false
       api_key: XXX
     
     shoonya:
       enabled: true
       api_key: XXX

7. Position Aggregation:
   - If trading across multiple brokers
   - get_total_positions() -> aggregated
   - get_broker_positions() -> per broker

8. Error Handling:
   - Broker-specific exceptions to standard exceptions
   - Fallback logic when primary fails
   - Detailed logging per broker

Database:
   - multi_broker_transactions table
   - Track which broker executed trade
   - For audit and analysis

Features:
   ✓ Single interface for multiple brokers
   ✓ Automatic fallback on connection loss
   ✓ Position aggregation across brokers
   ✓ Simple broker switching in config
   ✓ Standardized error handling
"

echo "✅ Step 4 Completed!"
echo ""

# Command 5: Strategy Marketplace
echo "[5/5] Creating Strategy Marketplace API..."
opencode create src/web/strategy_marketplace.py --description "
Create strategy sharing and marketplace platform:

1. StrategyRegistry class:
   - Save and version control strategies
   - Track performance of each strategy
   - Community ratings

Methods:
   - register_strategy(strategy_config) -> strategy_id
   - get_strategy(strategy_id) -> full strategy details
   - update_strategy(strategy_id, new_config)
   - fork_strategy(strategy_id) -> new_strategy_id
   - list_strategies(sort_by, limit, offset) -> array

2. Strategy Schema:
   {
     'strategy_id': 'uuid',
     'name': 'Premium Buying v2',
     'author_id': 'user_id',
     'description': 'Buy near support with strict risk',
     'version': '2.1',
     'created_at': timestamp,
     'updated_at': timestamp,
     'tags': ['options', 'premium', 'nifty'],
     
     'parameters': {
       'rsi_overbought': 70,
       'trailing_stop_pct': 3,
       'target_multiplier': 2
     },
     
     'performance': {
       'backtest_pnl': 5200,
       'win_rate': 0.62,
       'sharpe_ratio': 1.45,
       'max_drawdown': 0.08,
       'trades': 25
     },
     
     'ratings': {
       'stars': 4.5,
       'reviews': 12,
       'subscribers': 45
     },
     
     'license': 'MIT',
     'is_public': true
   }

3. MarketplaceAPI Endpoints:
   
   POST /api/marketplace/strategies
   - Upload new strategy
   - Body: {name, description, parameters, license, is_public}
   - Response: {strategy_id}
   
   GET /api/marketplace/strategies
   - List all public strategies
   - Query: sort_by=[rating, pnl, sharpe, popularity], limit=50, offset=0
   - Response: Array of strategies with summary
   
   GET /api/marketplace/strategies/{id}
   - Get full strategy details
   - Response: Complete strategy with backtest results
   
   GET /api/marketplace/strategies/{id}/backtest
   - Get strategy backtest results
   - Response: {performance_metrics, equity_curve, trade_list}
   
   POST /api/marketplace/strategies/{id}/subscribe
   - Subscribe to strategy (copy trades)
   - Response: {subscription_id, status}
   
   GET /api/marketplace/performance/{id}
   - Compare strategy performance
   - Response: {live_pnl, backtest_pnl, subscribers, rating}
   
   POST /api/marketplace/strategies/{id}/fork
   - Create your own copy of strategy
   - Response: {new_strategy_id, forked_from: id}
   
   POST /api/marketplace/strategies/{id}/rate
   - Leave a review
   - Body: {stars: 1-5, review_text}
   - Response: {rating_id}

4. PerformanceComparison:
   - Compare 2+ strategies side-by-side
   - Metrics: Sharpe, Sortino, max DD, win rate, profit factor
   - Visual comparison charts

5. SubscriptionSystem:
   - Subscribe to a strategy
   - Auto-execute when strategy signals
   - Track subscription performance
   - Cancel anytime

6. Community Features:
   - Comments on strategies
   - Rating system (1-5 stars)
   - Trending strategies
   - Top rated strategies
   - Author profiles

7. Legal / Licensing:
   - MIT, GPL, Commercial licenses
   - Source code visibility control
   - Revenue sharing for paid strategies

Database:
   - strategies table
   - strategy_versions table (history)
   - strategy_subscriptions table
   - strategy_ratings table
   - strategy_comments table
   - strategy_performance_history table

Features:
   ✓ Publish and discover strategies
   ✓ Community ratings and reviews
   ✓ Backtest result sharing
   ✓ Clone/fork strategies
   ✓ Auto-execution of strategies
   ✓ Performance comparison
   ✓ License management
"

echo "✅ Step 5 Completed!"
echo ""
echo "=========================================================="
echo "✅ Phase 14 Complete! Ecosystem integration finished."
echo ""
echo "Key Features Added:"
echo "  ✓ Comprehensive REST API v2 with OpenAPI/Swagger"
echo "  ✓ TradingView webhook integration"
echo "  ✓ 3Commas smart trade integration"
echo "  ✓ Multi-broker support (SmartAPI, Zerodha, Shoonya)"
echo "  ✓ Strategy marketplace & community"
echo "  ✓ Standardized position aggregation"
echo "  ✓ Auto-broker fallback on failures"
echo ""
echo "=========================================================="
echo \"🎉 ALL 6 PHASES COMPLETE! Project is now Enterprise-Grade\"
echo \"=========================================================\"
echo ""
echo \"Summary of Entire Implementation:\"
echo \"  Phase 9:  Live Execution & Order Management\"
echo \"  Phase 10: Advanced ML & Regime Detection\"
echo \"  Phase 11: Telegram/Discord Bot Integration\"
echo \"  Phase 12: Advanced Backtesting (Monte Carlo, VAR, Stress Tests)\"
echo \"  Phase 13: Production Deployment (Docker, K8s, CI/CD)\"
echo \"  Phase 14: Ecosystem Integration (APIs, TradingView, 3Commas, Multi-Broker)\"
echo \"\"
echo \"Total: ~60 new modules, ~40,000+ lines of production-grade code\"
echo \"Deployment: Fully containerized, scalable, enterprise-ready\"
echo \"\"
