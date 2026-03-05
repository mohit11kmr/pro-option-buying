"""
Database Migration Script for PostgreSQL
=========================================
Creates PostgreSQL tables for production deployment.
Run this script to initialize the database schema.
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'trading'),
            user=os.getenv('DB_USER', 'trading'),
            password=os.getenv('DB_PASSWORD', 'trading')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_tables():
    """Create all necessary tables for the trading system."""

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Market Data Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                volume BIGINT,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
            ON market_data(symbol, timestamp);
        """)

        # Trades Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50) UNIQUE,
                symbol VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL, -- BUY/SELL
                quantity INTEGER NOT NULL,
                entry_price DECIMAL(10,2),
                exit_price DECIMAL(10,2),
                pnl DECIMAL(10,2),
                status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, FILLED, CANCELLED
                strategy VARCHAR(100),
                timestamp TIMESTAMP NOT NULL,
                exit_timestamp TIMESTAMP,
                broker VARCHAR(50) DEFAULT 'angel_one',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_trades_status_timestamp
            ON trades(status, timestamp);
        """)

        # AI Signals Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_signals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                signal_type VARCHAR(10) NOT NULL, -- BUY/SELL
                strategy VARCHAR(100),
                entry_price DECIMAL(10,2),
                take_profit DECIMAL(10,2),
                stop_loss DECIMAL(10,2),
                confidence DECIMAL(3,2),
                timestamp TIMESTAMP NOT NULL,
                status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, EXECUTED, EXPIRED
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_ai_signals_symbol_timestamp
            ON ai_signals(symbol, timestamp);
        """)

        # Portfolio Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price DECIMAL(10,2),
                current_price DECIMAL(10,2),
                pnl DECIMAL(10,2),
                broker VARCHAR(50) DEFAULT 'angel_one',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, broker)
            );
        """)

        # Risk Metrics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                total_capital DECIMAL(12,2),
                deployed_capital DECIMAL(12,2),
                available_margin DECIMAL(12,2),
                daily_pnl DECIMAL(10,2),
                max_drawdown DECIMAL(10,2),
                sharpe_ratio DECIMAL(5,2),
                win_rate DECIMAL(5,2),
                total_trades INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            );
        """)

        # Telegram Alerts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_alerts (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                alert_type VARCHAR(50),
                timestamp TIMESTAMP NOT NULL,
                sent BOOLEAN DEFAULT FALSE
            );
        """)

        # TradingView Webhooks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tradingview_webhooks (
                id SERIAL PRIMARY KEY,
                signal_id VARCHAR(100) UNIQUE,
                payload JSONB,
                processed BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3Commas Smart Trades Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threecommas_trades (
                id SERIAL PRIMARY KEY,
                trade_id VARCHAR(100) UNIQUE,
                pair VARCHAR(20),
                side VARCHAR(10),
                quantity DECIMAL(15,8),
                entry_price DECIMAL(10,2),
                status VARCHAR(20),
                payload JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # User Sessions Table (for JWT)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100),
                token_hash VARCHAR(256),
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        logger.info("✅ All database tables created successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def create_initial_config():
    """Create initial configuration data."""

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Insert default risk configuration
        cursor.execute("""
            INSERT INTO risk_metrics (
                date, total_capital, deployed_capital, available_margin,
                daily_pnl, max_drawdown, sharpe_ratio, win_rate, total_trades
            ) VALUES (
                CURRENT_DATE, 100000.00, 0.00, 100000.00,
                0.00, 0.00, 0.00, 0.00, 0
            ) ON CONFLICT (date) DO NOTHING;
        """)

        conn.commit()
        logger.info("✅ Initial configuration created!")
        return True

    except Exception as e:
        logger.error(f"❌ Initial config creation failed: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Setting up PostgreSQL database for Nifty Trading System")
    print("=" * 60)

    # Create tables
    if create_tables():
        # Create initial config
        if create_initial_config():
            print("\n✅ Database setup completed successfully!")
            print("📊 Tables created:")
            print("   - market_data")
            print("   - trades")
            print("   - ai_signals")
            print("   - portfolio")
            print("   - risk_metrics")
            print("   - telegram_alerts")
            print("   - tradingview_webhooks")
            print("   - threecommas_trades")
            print("   - user_sessions")
        else:
            print("\n❌ Initial configuration failed!")
    else:
        print("\n❌ Database setup failed!")
        exit(1)