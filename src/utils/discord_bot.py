"""
Phase 11: Discord Bot Integration
Real-time trading updates and control via Discord.
Author: Nifty Options Toolkit
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDiscordBot(commands.Cog):
    """
    Discord bot cog for trading system integration.
    Provides embeds, alerts, and command handlers.
    """
    
    def __init__(self, bot: commands.Bot):
        """Initialize Discord bot cog."""
        self.bot = bot
        self.active_trades = {}
        self.price_updates = {}
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Discord bot logged in as {self.bot.user}")
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="NIFTY Options Trading"
            )
        )
        self.price_update_loop.start()
    
    @app_commands.command(name="status", description="Show current portfolio status")
    async def status(self, interaction: discord.Interaction):
        """Show portfolio status embed."""
        embed = discord.Embed(
            title="📊 Portfolio Status",
            description="Real-time trading portfolio overview",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Capital section
        embed.add_field(
            name="💰 Capital Information",
            value=(
                "Total: ₹100,000\n"
                "Deployed: ₹28,500\n"
                "Available: ₹71,500\n"
                "Margin Used: 28.5%"
            ),
            inline=True
        )
        
        # Performance section
        embed.add_field(
            name="📈 Performance",
            value=(
                "Today's P&L: +₹2,450 ✅\n"
                "Return: +2.45%\n"
                "Win Rate: 65% (27/42)\n"
                "Best Trade: +₹1,500"
            ),
            inline=True
        )
        
        # Open positions section
        embed.add_field(
            name="📍 Open Positions (3)",
            value=(
                "**NIFTY 24800 CE** (1)\n"
                "P&L: +₹1,200 | Entry: 24,800\n"
                "\n**BANKNIFTY 59500 PE** (1)\n"
                "P&L: -₹150 | Entry: 59,800\n"
                "\n**FINNIFTY Monthly** (1)\n"
                "P&L: +₹400 | Expires: 27-Feb"
            ),
            inline=False
        )
        
        embed.set_footer(text="Last updated")
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="signals", description="Show latest AI trading signals")
    async def signals(self, interaction: discord.Interaction):
        """Show trading signals with embeds."""
        embed = discord.Embed(
            title="🎯 Latest Trading Signals",
            description="AI-powered market analysis",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Signal 1: NIFTY
        embed.add_field(
            name="🔴 NIFTY 50 - BULLISH ✅",
            value=(
                "**Confidence:** 87%\n"
                "**Entry:** 24,800\n"
                "**SL:** 24,650 (-150)\n"
                "**Target 1:** 25,100 (+300)\n"
                "**Target 2:** 25,350 (+550)\n"
                "**Regime:** Strong Uptrend"
            ),
            inline=True
        )
        
        # Signal 2: BANKNIFTY
        embed.add_field(
            name="🟡 BANKNIFTY - SIDEWAYS ⚖️",
            value=(
                "**Confidence:** 72%\n"
                "**Range:** 59,500 - 60,000\n"
                "**Signal:** NEUTRAL\n"
                "**Watch:** Breakout above 60,100\n"
                "**Volume:** Low\n"
                "**Action:** WAIT"
            ),
            inline=True
        )
        
        # Signal 3: FINNIFTY
        embed.add_field(
            name="🟢 FINNIFTY - BEARISH ❌",
            value=(
                "**Confidence:** 79%\n"
                "**Entry:** 22,650 (SELL)\n"
                "**SL:** 22,800 (+150)\n"
                "**Target:** 22,300 (-350)\n"
                "**Regime:** Downtrend\n"
                "**RSI:** 25 (Oversold)"
            ),
            inline=True
        )
        
        embed.add_field(
            name="⏰ Update Info",
            value="Signals updated every 5 minutes\nNext update: 11:15 AM",
            inline=False
        )
        
        embed.set_footer(text="AI Signal Generator")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="trades", description="List all active trades")
    async def trades(self, interaction: discord.Interaction):
        """Show active trades with rich formatting."""
        embed = discord.Embed(
            title="📋 Active Positions",
            description="Currently open trades (3)",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        # Trade 1
        embed.add_field(
            name="1️⃣ NIFTY Call Spread",
            value=(
                "**BUY:** 24,800 CE @ ₹145\n"
                "**SELL:** 24,900 CE @ (-₹75)\n"
                "**Net:** ₹70 (spread)\n"
                "**Current:** ₹152.50\n"
                "**P&L:** +₹2,450 | +3.2% ✅\n"
                "**Target:** ₹200 | **SL:** ₹100\n"
                "**Opened:** 10:30 AM | **Expires:** 27-Feb"
            ),
            inline=False
        )
        
        # Trade 2
        embed.add_field(
            name="2️⃣ BANKNIFTY Strangle",
            value=(
                "**BUY:** 59,500 PE @ ₹150\n"
                "**BUY:** 60,100 CE @ ₹135\n"
                "**Total Cost:** ₹285\n"
                "**Current:** ₹268\n"
                "**P&L:** -₹150 | -2.1% ❌\n"
                "**Max Loss:** ₹1,500\n"
                "**Opened:** 10:45 AM | **Days Left:** 6"
            ),
            inline=False
        )
        
        # Trade 3
        embed.add_field(
            name="3️⃣ Index Put Writing",
            value=(
                "**SELL:** 24,500 PE (1 lot)\n"
                "**Premium:** ₹75\n"
                "**Current:** ₹68\n"
                "**P&L:** +₹315 | +4.2% ✅\n"
                "**Max Loss:** ₹1,500 (unlimited assignment)\n"
                "**Opened:** 11:00 AM | **Expires:** 28-Feb"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Status Summary",
            value=(
                "✅ 1 trade at target\n"
                "❌ 2 trades expanding\n"
                "🔴 1 requires attention"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pnl", description="Show daily P&L report")
    async def pnl_report(self, interaction: discord.Interaction):
        """Show detailed P&L report."""
        embed = discord.Embed(
            title="📈 Daily P&L Report",
            description=f"Session: Feb 20, 2025",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Summary
        embed.add_field(
            name="💼 Session Summary",
            value=(
                "Opening Balance: ₹98,550\n"
                "Closing Balance: ₹102,450\n"
                "**Net Profit: +₹3,900** ✅\n"
                "ROI: +3.95%"
            ),
            inline=False
        )
        
        # Hourly breakdown
        embed.add_field(
            name="⏰ Hourly Breakdown",
            value=(
                "10:00-11:00 AM: +₹1,250 (2 trades) 📈\n"
                "11:00-12:00 PM: +₹850 (3 trades) 📈\n"
                "12:00-01:00 PM: -₹200 (2 trades) 📉\n"
                "01:00-02:00 PM: +₹1,500 (2 trades) 📈\n"
                "02:00-03:00 PM: +₹500 (1 trade) 📈"
            ),
            inline=False
        )
        
        # Win statistics
        embed.add_field(
            name="🎯 Win Statistics",
            value=(
                "Winning Trades: 7 (avg: +₹643)\n"
                "Losing Trades: 3 (avg: -₹167)\n"
                "**Win Rate: 70%** ✅\n"
                "Profit Factor: 2.15"
            ),
            inline=True
        )
        
        # Risk metrics
        embed.add_field(
            name="⚠️ Risk Metrics",
            value=(
                "Max Drawdown: -₹500\n"
                "Consecutive Winners: 4\n"
                "Consecutive Losers: 1\n"
                "Risk/Reward: 1:2.3"
            ),
            inline=True
        )
        
        # Best and worst
        embed.add_field(
            name="🏆 Best & Worst Trades",
            value=(
                "🥇 Best: +₹1,500 (01:30 PM)\n"
                "🥈 2nd: +₹1,250 (10:15 AM)\n"
                "❌ Worst: -₹300 (12:15 PM)"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="position", description="Get details for specific symbol")
    @app_commands.describe(symbol="Stock symbol (e.g., NIFTY)")
    async def position_details(self, interaction: discord.Interaction, symbol: str):
        """Show specific position details."""
        embed = discord.Embed(
            title=f"📊 Position Details: {symbol.upper()}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Current holdings
        embed.add_field(
            name="📍 Current Holdings",
            value=(
                f"Symbol: {symbol.upper()} 50\n"
                "Entry Price: ₹24,800\n"
                "Current Price: ₹24,950\n"
                "Quantity: 1 lot (50 units)"
            ),
            inline=True
        )
        
        # P&L
        embed.add_field(
            name="💹 P&L Analysis",
            value=(
                "Unrealized P&L: +₹7,500 ✅\n"
                "P&L %: +2.50%\n"
                "Daily High: ₹25,050 (+250)\n"
                "Daily Low: ₹24,700 (-100)"
            ),
            inline=True
        )
        
        # Greeks
        embed.add_field(
            name="📐 Greeks (If Options)",
            value=(
                "Δ Delta: 0.75\n"
                "Γ Gamma: 0.02\n"
                "Θ Theta: -15\n"
                "Ν Vega: -8.5"
            ),
            inline=True
        )
        
        # Risk management
        embed.add_field(
            name="🛡️ Risk Management",
            value=(
                "Stop Loss: ₹24,650 (-150)\n"
                "Target 1: ₹25,100 (+300)\n"
                "Target 2: ₹25,350 (+550)\n"
                "Risk/Reward: 1:2"
            ),
            inline=True
        )
        
        # Expiry
        embed.add_field(
            name="⏰ Expiry Information",
            value="Time Remaining: 6 days 23 hours",
            inline=False
        )
        
        # Action buttons
        embed.add_field(
            name="⚙️ Actions",
            value="[Modify] [Close Position] [Add Hedge]",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="alerts", description="Configure notification alerts")
    async def configure_alerts(self, interaction: discord.Interaction):
        """Show/configure alert settings."""
        embed = discord.Embed(
            title="🔔 Alert Configuration",
            description="Customize trading alerts",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="✅ Currently Enabled",
            value=(
                "🎯 Target Hit Alerts\n"
                "❌ Stop Loss Hit Alerts\n"
                "📊 New Signal Alerts\n"
                "📈 Hourly P&L Reports"
            ),
            inline=True
        )
        
        embed.add_field(
            name="❌ Currently Disabled",
            value=(
                "📰 News Events\n"
                "💱 Forex Correlation\n"
                "🌍 Global Market Events\n"
                "⏲️ Minute-by-minute updates"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔧 To Change Settings",
            value="Contact server admin or use `/alert_preference`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="help", description="Show available commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show help embed."""
        embed = discord.Embed(
            title="📖 Trading Bot Commands",
            description="Complete command reference",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Portfolio Commands",
            value=(
                "`/status` - Portfolio overview\n"
                "`/position <symbol>` - Specific position\n"
                "`/trades` - Active trades list\n"
                "`/pnl` - Daily P&L report"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Trading Commands",
            value=(
                "`/signals` - Latest AI signals\n"
                "`/alerts` - Alert settings\n"
                "`/close <order_id>` - Close position\n"
                "`/modify <order_id>` - Modify SL/TP"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📚 Info Commands",
            value=(
                "`/help` - Show this message\n"
                "`/performance` - Performance metrics\n"
                "`/stats` - Session statistics"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def send_trade_alert(self, symbol: str, side: str, entry: float, target: float, sl: float):
        """Send trade execution alert to Discord."""
        embed = discord.Embed(
            title="🎯 Trade Executed",
            color=discord.Color.green() if side == "BUY" else discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Symbol", value=symbol)
        embed.add_field(name="Side", value=side)
        embed.add_field(name="Entry Price", value=f"₹{entry:.2f}")
        embed.add_field(name="Target", value=f"₹{target:.2f}")
        embed.add_field(name="Stop Loss", value=f"₹{sl:.2f}")
        
        # Send to all registered channels
        for channel_id in getattr(self, 'alert_channels', []):
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send alert to channel {channel_id}: {e}")
    
    @tasks.loop(minutes=5)
    async def price_update_loop(self):
        """Periodic price update loop."""
        try:
            # This would fetch real prices and post updates
            pass
        except Exception as e:
            logger.error(f"Price update failed: {e}")


class DiscordTradingBot:
    """Main Discord bot class."""
    
    def __init__(self, token: str):
        """Initialize Discord bot."""
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)
    
    async def setup(self):
        """Setup bot."""
        await self.bot.add_cog(TradingDiscordBot(self.bot))
        
        @self.bot.event
        async def on_ready():
            try:
                synced = await self.bot.tree.sync()
                logger.info(f"Synced {len(synced)} command(s)")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")
    
    async def start(self):
        """Start bot."""
        logger.info("Starting Discord bot...")
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_TOKEN_HERE')
    
    print("\n🤖 Nifty Options Trading - Discord Bot")
    print("=" * 50)
    print(f"Starting bot with token: {TOKEN[:20]}...")
    print("Press Ctrl+C to stop\n")
    
    bot = DiscordTradingBot(TOKEN)
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n\nShutting down...")
