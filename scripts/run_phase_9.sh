#!/bin/bash
# Quick Start: Copy & paste each command one-by-one

# First, verify you're in the right directory and venv is activated:
# cd /home/mohit/Desktop/system\ repair\ by\ antigravity/nifty_options\ \(copy\ 2\)/
# source venv/bin/activate

echo "Starting Phase 9: Live Execution & Order Management..."
echo "=================================================="

# Command 1: Live Order Executor Module
echo "[1/3] Creating Live Order Executor..."
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
Integration: Connect to SmartAPI through existing API credentials
Database: Store all orders and positions in db_manager
"

echo "✅ Step 1 Completed!"
echo ""

# Command 2: Flask Integration
echo "[2/3] Integrating with Flask API..."
opencode modify src/web/app.py --description "
Add these new Flask routes for live trading:

1. POST /api/trades/execute-live
   - Accept JSON: {symbol, quantity, entry_price, stop_loss, target}
   - Call LiveOrderExecutor.place_live_order()
   - Return: {order_id, status, execution_price, timestamp}

2. GET /api/trades/live-status
   - Return all active live orders with current P&L
   - Include: {symbol, entry_price, current_price, pnl, pnl_pct, status}

3. PUT /api/trades/close-live/{order_id}
   - Close a specific live order using order_id
   - Return final P&L and execution details

4. GET /api/positions/margin
   - Return {margin_used, margin_available, utilization_pct, total_capital}

5. POST /api/trades/auto-hedge
   - Accept: {symbol, hedge_ratio}
   - Auto-create hedge position using PositionManager
   - Return: {hedge_order_id, quantity_hedged}

6. WebSocket enhancement: /socket.io live P&L stream
   - Emit live_pnl event every 500ms for active positions
   - Emit order_filled, order_rejected, order_modified, target_hit, stoploss_hit
   - Include trade details in each emission

Import statements needed:
   from utils.live_order_executor import LiveOrderExecutor, OrderTracker, PositionManager

Error handlers for SmartAPI connection failures, add try-catch for all endpoints
Add before_request and after_request hooks for transaction management
"

echo "✅ Step 2 Completed!"
echo ""

# Command 3: Frontend Dashboard
echo "[3/3] Creating Live Trading Frontend..."
opencode create frontend/live-trading.html --description "
Create institutional live trading dashboard with:

1. Active Orders Panel:
   - HTML Table: Symbol | Entry Price | SL | Target | Current Price | P&L | % Return | Actions
   - Live updates every 500ms via WebSocket
   - Color coding: Green for profit, Red for loss
   - Action buttons: Close Position, Modify Order

2. Open Positions Summary Widget:
   - Total capital deployed
   - Total unrealized P&L (green/red)
   - Max drawdown today
   - Margin utilized (%) / available
   - Positions count

3. Quick Order Execution Panel:
   - Form fields: Symbol, Quantity, Entry Price, SL, Target, Auto-Hedge % (0-100)
   - Execute button with visual confirmation
   - Recent order history table (last 10 orders)

4. Live P&L Chart:
   - Real-time equity curve (TradingView Lightweight Charts)
   - Drawdown overlay (red area)
   - Entry/exit price markers
   - Time range selector (1H, 4H, 1D)

5. Live Notifications Area:
   - Scrolling notification feed
   - Order filled: 'NIFTY 1 share @ 24800'
   - Target hit: 'NIFTY reached target 24900'
   - Stop-loss hit: 'NIFTY stopped at 24700'
   - Margin warning: 'Margin used 85%, limit 90%'
   - Color coded by type

Styling:
   - Modern dark theme (like professional trading platforms)
   - Responsive mobile-friendly design
   - Font: Monospace for prices (better readability)
   - Charts: Use Chart.js or TradingView Lightweight Charts

JavaScript:
   - Connect to /socket.io
   - Listen to live_pnl, order_filled, order_rejected events
   - Update all elements in real-time
   - Calculate P&L locally for instant feedback

HTML Structure:
   - Header: Navigation with link to live-trading.html
   - Left Sidebar: Position summary widget
   - Main Content: Active orders table + P&L chart
   - Right Sidebar: Order execution form + notifications

Make it look institutional and professional!
"

echo "✅ Step 3 Completed!"
echo ""
echo "=================================================="
echo "✅ Phase 9 Complete! All live execution modules created."
echo ""
echo "Next: Run Phase 10 commands in next terminal session"
echo "Or continue with Phase 11, 12, 13, 14..."
echo ""
