#!/bin/bash
# Phase 11: Telegram/Discord Bot Integration
# Copy & paste commands one-by-one

echo "Starting Phase 11: Telegram/Discord Bot Integration..."
echo "======================================================"

# Command 1: Telegram Bot
echo "[1/3] Creating Telegram Bot Service..."
opencode create src/utils/telegram_bot.py --description "
Create production-grade Telegram bot for trading alerts:

1. TelegramBot class:
   - Initialize with bot_token and chat_id from .env
   - Auto-reconnect with exponential backoff
   - Message queue system to prevent API spam

Methods:
   Core Communication:
   - send_message(text, chat_id=None) -> bool
   - send_alert(alert_type, data) -> bool
   - send_trade_notification(trade_data)
   - send_position_update(positions)
   - send_daily_summary(pnl_stats)
   - send_risk_alert(alert_type, details)

   Command Handlers:
   - handle_command(command, args) -> response
   - /start -> Initialize user, send welcome message
   - /status -> Current positions with P&L, margin used
   - /execute -> Place order: /execute NIFTY 1 24800 24650 24950
   - /close -> Close position: /close {order_id}
   - /positions -> List all open positions
   - /stats -> Daily PnL, win rate, profit factor, trades count
   - /alerts -> View recent 10 alerts
   - /help -> Show all commands

2. AlertManager class:
   - Queue system for alerts (max 10 per minute to avoid spam)
   - Alert types: TRADE_EXECUTED, TARGET_HIT, STOPLOSS_HIT, MARGIN_WARNING, DAILY_SUMMARY
   - Batch related alerts if market moves fast
   - Deduplication: Don't send same alert twice

Methods:
   - queue_alert(alert_type, data)
   - process_alert_queue() -> sends max 10 alerts/min
   - batch_alerts(alert_list) -> single message
   - is_duplicate_alert(alert) -> bool

3. Message Templates:
   Trade Execution:
   '''
   ✅ TRADE EXECUTED
   Symbol: NIFTY 50
   Entry: ₹24,800
   Stop-Loss: ₹24,650
   Target: ₹24,950
   Quantity: 1
   Timestamp: 2026-03-05 10:15:00
   '''

   Target Hit:
   '''
   🎯 TARGET HIT!
   Symbol: NIFTY 50
   Target Price: ₹24,950
   Actual Price: ₹24,952
   Profit: ₹152 (0.61%)
   Time Held: 2h 15m
   '''

   Stop-Loss Hit:
   '''
   ❌ STOP-LOSS HIT
   Symbol: NIFTY 50
   SL Price: ₹24,650
   Actual Price: ₹24,648
   Loss: -₹152 (-0.61%)
   Time Held: 1h 30m
   '''

   Daily Summary:
   '''
   📊 DAILY SUMMARY - 2026-03-05
   Total Trades: 8
   Winning Trades: 5 (62.5%)
   Losing Trades: 3 (37.5%)
   Total P&L: +₹2,450
   Win Rate: 62.5%
   Profit Factor: 1.85
   Max Drawdown: -₹520
   Sharpe Ratio: 1.2
   '''

   Margin Warning:
   '''
   ⚠️ MARGIN ALERT
   Margin Used: 87% (₹87,000 / ₹100,000)
   Margin Available: 13% (₹13,000)
   Action Recommended: Close some positions if not confident
   '''

4. Integration with Flask:
   - Webhook endpoint: POST /api/telegram/webhook
   - Polling option: Background thread polls for new messages
   - Command dispatcher routes commands to handlers

5. Error Handling:
   - Connection timeouts: Retry with exponential backoff
   - API rate limits: Queue and retry
   - Invalid command: Send helpful error message
   - Invalid credentials in .env: Alert on startup

6. Logging:
   - All messages to telegram.log (JSON format)
   - Include timestamp, user_id, message_type, content
   - Separate SUCCESS/ERROR logs

Environment Variables (in .env):
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   TELEGRAM_ENABLE=true/false
"

echo "✅ Step 1 Completed!"
echo ""

# Command 2: Discord Bot
echo "[2/3] Creating Discord Bot Service..."
opencode create src/utils/discord_bot.py --description "
Create Discord bot for trading alerts:

1. DiscordBot class:
   - Initialize with bot_token from .env
   - Connect to Discord server/channel
   - Support rich embeds for visual alerts

Methods:
   - send_embedded_alert(title, description, color)
   - send_position_table(positions) -> formatted embed
   - send_performance_chart(chart_image)
   - send_trade_notification(trade_data)
   - handle_slash_command(interaction) -> response

2. Slash Commands:
   - /status -> Current positions + P&L
   - /execute symbol qty entry sl target -> Place order
   - /close order_id -> Close position
   - /positions -> List all open positions
   - /stats -> Daily performance stats
   - /alerts -> View recent alerts
   - /help -> Show all commands

3. Channel Organization:
   - #trading-alerts: Real-time trade notifications
   - #daily-summary: End-of-day performance report
   - #risk-warnings: Margin warnings, max loss alerts
   - #trades-log: Detailed trade history
   - #commands: Bot command responses
   - #health: Service health status

4. Rich Embeds:
   Each notification is a rich embed card with:
   - Title & Description
   - Color coding (Green for profit, Red for loss, Yellow for warning)
   - Fields: Entry, Target, SL, Current Price, P&L, % Return
   - Timestamp
   - Thumbnail (trend arrow emoji indicator)

5. Trade Notification Embed:
   Title: ✅ Trade Executed
   Fields:
   - Symbol: NIFTY 50
   - Entry: ₹24,800
   - Target: ₹24,950
   - SL: ₹24,650
   - Quantity: 1
   - Risk:Reward: 1:2
   Color: Green

6. Integration with Flask:
   - Background thread runs bot
   - Discord command responses routed through Flask
   - Bidirectional communication (bot <-> API)

7. Error Handling:
   - Graceful disconnection handling
   - Auto-reconnect with backoff
   - Fallback to Discord logs channel if main channel unavailable

Environment Variables (in .env):
   DISCORD_BOT_TOKEN=your_bot_token
   DISCORD_SERVER_ID=your_server_id
   DISCORD_CHANNEL_IDS={alerts: id, signals: id, ...}
   DISCORD_ENABLE=true/false
"

echo "✅ Step 2 Completed!"
echo ""

# Command 3: Flask Integration
echo "[3/3] Integrating Bots into Flask..."
opencode modify src/web/app.py --description "
Add bot integrations to Flask app:

1. New Flask Routes:
   - POST /api/telegram/webhook -> Handle Telegram messages
   - POST /api/discord/webhook -> Handle Discord interactions
   - GET /api/alerts/history -> Get alert history (last 100)
   - POST /api/alerts/test -> Send test alert to both platforms

2. Background Threads (Start on app startup):
   - telegram_listener_thread: Listen for Telegram messages
   - discord_listener_thread: Listen for Discord interactions
   - daily_summary_thread: Send daily summary at 3:45 PM
   - position_update_thread: Send position updates every 5 minutes

3. Alert Dispatcher:
   - When trade executed: Send to both Telegram & Discord
   - When target hit: Send to both platforms
   - When SL hit: Send to both platforms
   - When margin warning: Send to both platforms
   - When daily summary: Send to both platforms

4. Initialization code:
   ```python
   # In app initialization
   telegram_bot = TelegramBot(token, chat_id)
   discord_bot = DiscordBot(token, server_id)
   
   def init_bot_threads():
       Thread(target=telegram_bot.listen, daemon=True).start()
       Thread(target=discord_bot.listen, daemon=True).start()
       Thread(target=send_daily_summary, daemon=True).start()
       Thread(target=send_position_updates, daemon=True).start()
   
   init_bot_threads()
   ```

5. Alert Type Routing:
   TRADE_EXECUTED -> Both bots
   TARGET_HIT -> Both bots + Email notification
   STOPLOSS_HIT -> Both bots + Email notification
   MARGIN_WARNING -> Both bots + Sound alert
   DAILY_SUMMARY -> Both bots (formatted)

6. Environment Loading:
   Load TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID from .env
   Load DISCORD_BOT_TOKEN, DISCORD_SERVER_ID from .env
   Load TELEGRAM_ENABLE, DISCORD_ENABLE flags

7. Error Handling:
   - Handle missing bot tokens gracefully
   - Log failures but don't crash app
   - Retry failed message sends with backoff
   - Alert admin if both bots down

8. Testing:
   - POST /api/alerts/test with message
   - Verify message appears on both Telegram & Discord
"

echo "✅ Step 3 Completed!"
echo ""
echo "======================================================"
echo "✅ Phase 11 Complete! Bot integration created."
echo ""
echo "Key Features Added:"
echo "  ✓ Telegram Bot with 7 slash commands"
echo "  ✓ Discord Bot with 7 slash commands"
echo "  ✓ Real-time trade notifications"
echo "  ✓ Daily performance summaries"
echo "  ✓ Risk alerts and warnings"
echo "  ✓ Dual-platform redundancy"
echo ""
echo "Setup Instructions:"
echo "  1. Create Telegram bot at @BotFather, get bot token"
echo "  2. Get your Telegram chat ID"
echo "  3. Create Discord bot at Discord Developer Portal, get token"
echo "  4. Create Discord server and channel IDs"
echo "  5. Add TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID to .env"
echo "  6. Add DISCORD_BOT_TOKEN, DISCORD_SERVER_ID to .env"
echo ""
echo "Next: Run Phase 12 (Advanced Backtesting + Monte Carlo)"
echo ""
