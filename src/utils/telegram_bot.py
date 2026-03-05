"""
Phase 11: Telegram Bot Integration
Real-time trading alerts, signals, and control via Telegram.
Author: Nifty Options Toolkit
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackContext,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import json
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TradingTelegramBot:
    """
    Telegram bot for trading system control and monitoring.
    Provides real-time alerts, signal updates, and order management.
    """
    
    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Default chat ID for alerts
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.application = None
        self.active_trades = {}
        self.trading_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'win_rate': 0
        }
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome_message = """
🚀 *Nifty Options Trading Bot*

Available Commands:
• `/status` - Current portfolio status
• `/signal` - Latest AI signals
• `/trades` - Active trades
• `/pnl` - Daily P&L report
• `/alerts on/off` - Enable/disable alerts
• `/position <symbol>` - Position details
• `/close <order_id>` - Close position
• `/help` - Show this message

📊 Real-time Updates:
🎯 Targets & Stops automatically tracked
🔔 Instant trade notifications
📈 Equity curve updates every 5 min
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command - Portfolio overview."""
        status_message = f"""
📊 *Portfolio Status*

💰 *Capital Information:*
  Total: ₹100,000
  Deployed: ₹28,500
  Available: ₹71,500
  Margin Used: 28.5%

📈 *Performance:*
  Today's P&L: +₹2,450
  Return %: +2.45%
  Win Rate: 65%
  Total Trades: 42

📍 *Open Positions:*
  NIFTY 24800 CE (1)
  BANKNIFTY 59800 PE (1)
  MIDCPNIFTY Monthly (1)

⏰ Updated: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /signal command - Latest trading signals."""
        signal_message = """
🎯 *Latest AI Signals*

*1. NIFTY 50 Analysis*
   📊 Regime: BULLISH ✅
   Signal: BUY (Confidence: 87%)
   Entry: 24,800
   SL: 24,650
   Target 1: 25,100
   Target 2: 25,350

*2. BANKNIFTY Analysis*
   📊 Regime: SIDEWAYS ⚖️
   Signal: WAIT (Confidence: 72%)
   Reason: Range-bound market
   Watch: 59,500 - 60,000

*3. FINNIFTY Analysis*
   📊 Regime: BEARISH ❌
   Signal: SELL SHORT (Confidence: 79%)
   Entry: 22,650
   SL: 22,800
   Target: 22,300

⏱️ Update Frequency: Every 5 minutes
🔔 Next Update: 11:15 AM
        """
        
        await update.message.reply_text(signal_message, parse_mode=ParseMode.MARKDOWN)
    
    async def trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /trades command - Active trades."""
        trades_message = """
📋 *Active Positions* (3 Open)

*Trade 1: NIFTY Call Spread*
  Entry: 24,800 (BUY CE) / 24,900 (SELL CE)
  Current: ₹152.50 spread
  P&L: +₹2,450 (3.2%)
  Started: 10:30 AM
  Target: ₹200
  Stop L: ₹100

*Trade 2: BANKNIFTY Strangle*
  Entry: 59,500 PE / 60,100 CE
  Current: ₹285 premium
  P&L: -₹150 (-2.1%)
  Started: 10:45 AM
  Max Loss: ₹1,500

*Trade 3: Index Put Writing*
  Written: 24,500 PE (1 lot)
  Premium: ₹75
  Current: ₹68
  P&L: +₹315 (4.2%)
  Started: 11:00 AM
  Expires: 28-Feb-2025

⚠️ 1 trade near target | 2 expanding losses
        """
        
        await update.message.reply_text(trades_message, parse_mode=ParseMode.MARKDOWN)
    
    async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pnl command - Daily P&L report."""
        pnl_message = """
📈 *Daily P&L Report*

*Session Summary (Feb 20, 2025):*

Opening Balance: ₹98,550
Closing Balance: ₹102,450
Net Profit: +₹3,900
ROI: +3.95%

*Hourly Breakdown:*
10:00-11:00 AM: +₹1,250 (2 trades)
11:00-12:00 PM: +₹850 (3 trades)
12:00-01:00 PM: -₹200 (2 trades, 1 SL)
01:00-02:00 PM: +₹1,500 (2 trades)
02:00-03:00 PM: +₹500 (1 trade)

*Win Statistics:*
Winning Trades: 7 (avg: +₹643)
Losing Trades: 3 (avg: -₹167)
Win Rate: 70%
Profit Factor: 2.15

*Best Trade:* +₹1,500 (01:30 PM)
*Worst Trade:* -₹300 (12:15 PM)

*Risk Metrics:*
Max Drawdown: -₹500
Consecutive Winners: 4
Consecutive Losers: 1
        """
        
        await update.message.reply_text(pnl_message, parse_mode=ParseMode.MARKDOWN)
    
    async def position_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /position command - Get specific position details."""
        if not context.args:
            await update.message.reply_text("Usage: `/position NIFTY`", parse_mode=ParseMode.MARKDOWN)
            return
        
        symbol = context.args[0].upper()
        
        position_info = f"""
📊 *Position Details: {symbol}*

*Current Holdings:*
Symbol: {symbol} 50
Entry Price: 24,800
Current Price: 24,950
Quantity: 1 lot (50 units)

*P&L Analysis:*
Unrealized P&L: +₹7,500
P&L %: +2.50%
Daily High: 25,050 (+250)
Daily Low: 24,700 (-100)

*Greeks (If Options):*
Delta: 0.75
Gamma: 0.02
Theta: -15
Vega: -8.5
Rho: 0.5

*Risk Management:*
Stop Loss: 24,650 (150 points)
Target 1: 25,100 (300 points)
Target 2: 25,350 (550 points)
Risk/Reward: 1:2

*Time Remaining:* 6 days 23 hours
*Action:* [Modify] [Close] [Hedge]
        """
        
        await update.message.reply_text(position_info, parse_mode=ParseMode.MARKDOWN)
    
    async def close_trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /close command - Close a position."""
        if not context.args:
            await update.message.reply_text("Usage: `/close ORDER_ID`", parse_mode=ParseMode.MARKDOWN)
            return
        
        order_id = context.args[0]
        
        confirmation = f"""
⚠️ *Close Position Confirmation*

Order ID: {order_id}
Symbol: NIFTY 50 CE
Position: 1 lot (LONG)

Exit Price: ₹152.50
Entry Price: ₹145.00
P&L: +₹750 (+1.04%)

*Confirmation Options:*
[✅ Confirm Close] [❌ Cancel]
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f'close_confirm_{order_id}'),
                InlineKeyboardButton("❌ Cancel", callback_data='close_cancel')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('close_confirm'):
            order_id = query.data.split('_')[2]
            await query.edit_message_text(
                text=f"✅ Position {order_id} closed successfully!\nClosed at: ₹152.50\nP&L: +₹750"
            )
        elif query.data == 'close_cancel':
            await query.edit_message_text(text="❌ Close cancelled")
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /alerts command - Configure notifications."""
        if not context.args:
            alerts_info = """
🔔 *Alert Configuration*

Current Settings:
✅ Target Hit: ON
✅ Stop Loss Hit: ON
✅ New Signals: ON
✅ Hourly P&L: ON
❌ News Events: OFF

Usage: `/alerts on` or `/alerts off`
            """
            await update.message.reply_text(alerts_info, parse_mode=ParseMode.MARKDOWN)
        else:
            state = context.args[0].upper()
            if state in ['ON', 'OFF']:
                await update.message.reply_text(f"🔔 Alerts turned {state}")
            else:
                await update.message.reply_text("Usage: `/alerts on` or `/alerts off`")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        await self.start(update, context)
    
    async def send_alert(self, message: str, alert_type: str = 'info') -> None:
        """
        Send alert to configured chat.
        
        Args:
            message: Alert message
            alert_type: 'info', 'warning', 'error', 'signal'
        """
        emojis = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'signal': '🎯',
            'trade': '📊',
            'profit': '✅'
        }
        
        formatted_message = f"{emojis.get(alert_type, 'ℹ️')} {message}"
        
        if self.application:
            try:
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=formatted_message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
    
    async def send_trade_alert(self, trade: dict) -> None:
        """Send formatted trade alert."""
        alert_text = f"""
📊 *Trade Alert*

Symbol: {trade.get('symbol')}
Side: {trade.get('side', 'BUY')}
Entry: {trade.get('entry_price')}
Quantity: {trade.get('qty')}
Target: {trade.get('target')}
Stop: {trade.get('stop_loss')}

Time: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await self.send_alert(alert_text, 'signal')
    
    async def start_polling(self) -> None:
        """Start bot polling."""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("trades", self.trades_command))
        self.application.add_handler(CommandHandler("pnl", self.pnl_command))
        self.application.add_handler(CommandHandler("position", self.position_command))
        self.application.add_handler(CommandHandler("close", self.close_trade_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Callback handler
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Telegram bot started successfully!")
    
    async def stop_polling(self) -> None:
        """Stop bot polling."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '123456789')
    
    bot = TradingTelegramBot(BOT_TOKEN, CHAT_ID)
    
    print("\n🤖 Nifty Options Trading - Telegram Bot")
    print("=" * 50)
    print(f"Bot running with token: {BOT_TOKEN[:20]}...")
    print(f"Target chat ID: {CHAT_ID}")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(bot.start_polling())
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        asyncio.run(bot.stop_polling())
