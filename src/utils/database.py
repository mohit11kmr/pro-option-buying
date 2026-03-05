"""
SQLite Database for Trading Data
================================
Provides SQLite database for storing historical data, trades, and signals.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd


class TradingDatabase:
    """SQLite database for trading data."""
    
    def __init__(self, db_path: str = "data/trading.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
            ON market_data(symbol, timestamp)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT,
                quantity INTEGER,
                price REAL,
                pnl REAL,
                strategy TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                recommendation TEXT,
                confidence REAL,
                score REAL,
                components TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                strategy TEXT,
                parameters TEXT,
                initial_capital REAL,
                final_capital REAL,
                total_pnl REAL,
                returns_percent REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                total_trades INTEGER,
                win_rate REAL,
                details TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT,
                entry_price REAL,
                entry_time TEXT,
                quantity INTEGER,
                current_price REAL,
                unrealized_pnl REAL,
                status TEXT DEFAULT 'OPEN',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(str(self.db_path))
    
    def insert_market_data(self, data: Dict) -> int:
        """Insert market data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO market_data (timestamp, symbol, open, high, low, close, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('timestamp'),
            data.get('symbol'),
            data.get('open'),
            data.get('high'),
            data.get('low'),
            data.get('close'),
            data.get('volume'),
            data.get('source')
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get market data."""
        conn = self._get_connection()
        
        query = "SELECT timestamp, symbol, open, high, low, close, volume FROM market_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def insert_trade(self, trade: Dict) -> int:
        """Insert a trade record."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (timestamp, symbol, direction, quantity, price, pnl, strategy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.get('timestamp'),
            trade.get('symbol'),
            trade.get('direction'),
            trade.get('quantity'),
            trade.get('price'),
            trade.get('pnl'),
            trade.get('strategy'),
            trade.get('notes')
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trade records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def insert_signal(self, signal: Dict) -> int:
        """Insert a signal record."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO signals (timestamp, symbol, recommendation, confidence, score, components)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            signal.get('timestamp'),
            signal.get('symbol'),
            signal.get('recommendation'),
            signal.get('confidence'),
            signal.get('score'),
            json.dumps(signal.get('components', {}))
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_signals(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get signal records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM signals
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def insert_backtest_result(self, result: Dict) -> int:
        """Insert backtest result."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO backtest_results
            (strategy, parameters, initial_capital, final_capital, total_pnl,
             returns_percent, sharpe_ratio, max_drawdown, total_trades, win_rate, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.get('strategy'),
            json.dumps(result.get('parameters', {})),
            result.get('initial_capital'),
            result.get('final_capital'),
            result.get('total_pnl'),
            result.get('returns_percent'),
            result.get('sharpe_ratio'),
            result.get('max_drawdown'),
            result.get('total_trades'),
            result.get('win_rate'),
            json.dumps(result.get('details', {}))
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_backtest_results(self, limit: int = 10) -> List[Dict]:
        """Get backtest results."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM backtest_results
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def update_position(self, position: Dict) -> int:
        """Update or insert position."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO positions
            (symbol, direction, entry_price, entry_time, quantity, current_price, unrealized_pnl, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position.get('symbol'),
            position.get('direction'),
            position.get('entry_price'),
            position.get('entry_time'),
            position.get('quantity'),
            position.get('current_price'),
            position.get('unrealized_pnl'),
            position.get('status', 'OPEN'),
            datetime.now().isoformat()
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_open_positions(self) -> List[Dict]:
        """Get open positions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM positions WHERE status = 'OPEN'
        """)
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results


def demo_database():
    """Demonstrate database functionality."""
    print("\n" + "="*60)
    print("DATABASE DEMO")
    print("="*60)
    
    db = TradingDatabase("data/demo_trading.db")
    
    db.insert_market_data({
        'timestamp': datetime.now().isoformat(),
        'symbol': 'NIFTY',
        'open': 25000,
        'high': 25100,
        'low': 24900,
        'close': 25050,
        'volume': 2000000,
        'source': 'demo'
    })
    
    print("Inserted market data")
    
    db.insert_trade({
        'timestamp': datetime.now().isoformat(),
        'symbol': 'NIFTY',
        'direction': 'BUY',
        'quantity': 100,
        'price': 25000,
        'pnl': 5000,
        'strategy': 'ma_crossover'
    })
    
    print("Inserted trade")
    
    db.insert_signal({
        'timestamp': datetime.now().isoformat(),
        'symbol': 'NIFTY',
        'recommendation': 'BUY',
        'confidence': 75,
        'score': 65,
        'components': {'price': 1, 'pattern': 0.5}
    })
    
    print("Inserted signal")
    
    trades = db.get_trades()
    print(f"\nTotal trades: {len(trades)}")


if __name__ == "__main__":
    demo_database()
