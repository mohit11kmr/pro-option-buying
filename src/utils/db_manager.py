import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class DatabaseManager:
    def __init__(self, db_path: str = "data/trading_app.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # --- Existing tables ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strike REAL NOT NULL,
                type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                pnl REAL,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                sl REAL,
                tp REAL,
                max_trades INTEGER,
                trailing_sl REAL,
                risk_per_trade REAL,
                daily_loss_limit REAL,
                capital REAL,
                time_exit INTEGER,
                min_confidence REAL,
                min_adx REAL,
                vol_spike REAL,
                min_ivp REAL
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM app_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO app_config (
                    id, sl, tp, max_trades, trailing_sl, 
                    risk_per_trade, daily_loss_limit, capital, 
                    time_exit, min_confidence, min_adx, 
                    vol_spike, min_ivp
                )
                VALUES (1, 25.0, 40.0, 3, 20.0, 2.0, 5.0, 200000.0, 45, 60.0, 20.0, 1.5, 12.0)
            """)

        # --- Self-Learning Tables ---

        # 1. Log every AI signal generated
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                recommendation TEXT,
                score REAL,
                confidence REAL,
                price_component REAL,
                pattern_component REAL,
                sentiment_component REAL,
                options_component REAL,
                nifty_price REAL,
                weights_json TEXT,
                verdict TEXT
            )
        """)

        # 2. Track outcome of each signal (filled after 15/30/60 min)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL,
                check_after_mins INTEGER NOT NULL,
                actual_price REAL,
                price_change_pct REAL,
                was_correct INTEGER,
                checked_at TEXT,
                FOREIGN KEY (signal_id) REFERENCES signal_log(id)
            )
        """)

        # 3. Track model performance over time
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT,
                accuracy REAL,
                f1_score REAL,
                samples_used INTEGER,
                trained_at TEXT NOT NULL
            )
        """)

        # 4. Store live market snapshots for training
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                timeframe TEXT DEFAULT '5m'
            )
        """)

        # 6. Institutional Paper Trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strike REAL,
                option_type TEXT,
                entry_price REAL NOT NULL,
                lots INTEGER NOT NULL,
                sl REAL,
                tp REAL,
                status TEXT DEFAULT 'OPEN',
                exit_price REAL,
                exit_time TEXT,
                pnl REAL,
                reason TEXT
            )
        """)

        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    # ========================
    #  INSTITUTIONAL: Paper Trades
    # ========================

    def add_paper_trade(self, symbol: str, entry_price: float, lots: int, 
                        strike: float = None, option_type: str = None,
                        sl: float = None, tp: float = None, reason: str = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO paper_trades 
            (timestamp, symbol, strike, option_type, entry_price, lots, sl, tp, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (datetime.now().isoformat(), symbol, strike, option_type, entry_price, lots, sl, tp, reason))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def get_paper_trades(self, limit: int = 100, status: str = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM paper_trades WHERE status = ? ORDER BY timestamp DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM paper_trades ORDER BY timestamp DESC LIMIT ?", (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    def update_paper_trade(self, trade_id: int, exit_price: float, status: str = 'CLOSED') -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get entry info to calculate PnL
        cursor.execute("SELECT entry_price, lots, option_type FROM paper_trades WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
            
        entry_price, lots, opt_type = row
        
        # Calculate PnL (for Nifty Options, standard mult = 50 but we use lots)
        # Assuming lots is quantity of contracts
        multiplier = 25  # Modern Nifty lot size
        
        if opt_type == 'PUT':
            pnl = (entry_price - exit_price) * lots * multiplier
        else: # CALL or SPOT/FUT
            pnl = (exit_price - entry_price) * lots * multiplier
            
        cursor.execute("""
            UPDATE paper_trades 
            SET exit_price = ?, exit_time = ?, pnl = ?, status = ? 
            WHERE id = ?
        """, (exit_price, datetime.now().isoformat(), pnl, status, trade_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def get_trade_stats(self) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total PnL, Win Rate, Profit Factor
        cursor.execute("SELECT pnl FROM paper_trades WHERE status = 'CLOSED'")
        pnls = [row[0] for row in cursor.fetchall() if row[0] is not None]
        
        if not pnls:
            conn.close()
            return {"total_pnl": 0, "win_rate": 0, "profit_factor": 0, "total_trades": 0}
            
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        total_pnl = sum(pnls)
        win_rate = (len(wins) / len(pnls)) * 100
        
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        
        conn.close()
        return {
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "total_trades": len(pnls),
            "avg_win": round(sum(wins)/len(wins), 2) if wins else 0,
            "avg_loss": round(sum(losses)/len(losses), 2) if losses else 0
        }

    # ========================
    #  EXISTING: Trade Journal
    # ========================

    def add_trade(
        self,
        strike: float,
        trade_type: str,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        timestamp: Optional[str] = None
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        ts = timestamp or datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO trade_journal (strike, type, entry_price, exit_price, pnl, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (strike, trade_type, entry_price, exit_price, pnl, ts))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id
    
    def get_trades(self, limit: int = 100) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, strike, type, entry_price, exit_price, pnl, timestamp
            FROM trade_journal ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def update_trade(self, trade_id: int, exit_price: float, pnl: float) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE trade_journal SET exit_price = ?, pnl = ? WHERE id = ?",
                       (exit_price, pnl, trade_id))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_trade(self, trade_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trade_journal WHERE id = ?", (trade_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    # ========================
    #  EXISTING: Config
    # ========================

    def get_config(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM app_config WHERE id = 1")
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        if row:
            config = dict(zip(columns, row))
            config.pop('id', None)
            return config
        return {}
    
    def update_config(self, **kwargs) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        config = self.get_config()
        for key, value in kwargs.items():
            if key in config and value is not None:
                config[key] = value
        fields = ", ".join([f"{k} = ?" for k in config.keys()])
        values = list(config.values())
        cursor.execute(f"UPDATE app_config SET {fields} WHERE id = 1", values)
        conn.commit()
        conn.close()
        return True

    # ========================
    #  SELF-LEARNING: Signal Log
    # ========================

    def log_signal(self, signal: Dict, nifty_price: float, weights: Dict) -> int:
        """Log an AI signal for tracking."""
        conn = self._get_connection()
        cursor = conn.cursor()
        components = signal.get('components', {})
        cursor.execute("""
            INSERT INTO signal_log 
            (timestamp, recommendation, score, confidence,
             price_component, pattern_component, sentiment_component,
             options_component, nifty_price, weights_json, verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            signal.get('recommendation', 'HOLD'),
            signal.get('score', 0),
            signal.get('confidence', 0),
            components.get('price_prediction', 0),
            components.get('pattern_recognition', 0),
            components.get('sentiment', 0),
            components.get('options_flow', 0),
            nifty_price,
            json.dumps(weights),
            signal.get('verdict', '')
        ))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def get_pending_outcomes(self, check_after_mins: int) -> List[Dict]:
        """Get signals that need outcome verification."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sl.id, sl.timestamp, sl.recommendation, sl.nifty_price,
                   sl.price_component, sl.pattern_component, 
                   sl.sentiment_component, sl.options_component
            FROM signal_log sl
            WHERE sl.id NOT IN (
                SELECT signal_id FROM signal_outcomes WHERE check_after_mins = ?
            )
            AND julianday('now') - julianday(sl.timestamp) >= ? / 1440.0
            ORDER BY sl.timestamp DESC LIMIT 100
        """, (check_after_mins, check_after_mins))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    def record_outcome(self, signal_id: int, check_after_mins: int,
                       actual_price: float, price_change_pct: float,
                       was_correct: bool) -> int:
        """Record the outcome of a signal."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signal_outcomes 
            (signal_id, check_after_mins, actual_price, price_change_pct,
             was_correct, checked_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (signal_id, check_after_mins, actual_price, price_change_pct,
              1 if was_correct else 0, datetime.now().isoformat()))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def get_accuracy_stats(self, days: int = 7) -> Dict:
        """Get signal accuracy statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(was_correct) as correct,
                AVG(was_correct) * 100 as accuracy_pct,
                check_after_mins
            FROM signal_outcomes so
            JOIN signal_log sl ON so.signal_id = sl.id
            WHERE julianday('now') - julianday(sl.timestamp) <= ?
            GROUP BY check_after_mins
        """, (days,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return {
            'by_timeframe': results,
            'days': days,
            'timestamp': datetime.now().isoformat()
        }

    def get_component_accuracy(self, days: int = 7) -> Dict:
        """Get accuracy per signal component."""
        conn = self._get_connection()
        cursor = conn.cursor()
        # For each component, check if its direction matched the actual outcome
        cursor.execute("""
            SELECT 
                sl.price_component, sl.pattern_component,
                sl.sentiment_component, sl.options_component,
                so.was_correct, so.price_change_pct
            FROM signal_outcomes so
            JOIN signal_log sl ON so.signal_id = sl.id
            WHERE julianday('now') - julianday(sl.timestamp) <= ?
            AND so.check_after_mins = 15
        """, (days,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {'price': 50, 'pattern': 50, 'sentiment': 50, 'options': 50}

        # Calculate per-component accuracy
        components = {'price': [], 'pattern': [], 'sentiment': [], 'options': []}
        for row in rows:
            price_c, pattern_c, sentiment_c, options_c, was_correct, change = row
            actual_dir = 1 if change > 0 else (-1 if change < 0 else 0)
            
            components['price'].append(1 if (price_c > 0) == (actual_dir > 0) else 0)
            components['pattern'].append(1 if (pattern_c > 0) == (actual_dir > 0) else 0)
            components['sentiment'].append(1 if (sentiment_c > 0) == (actual_dir > 0) else 0)
            components['options'].append(1 if (options_c > 0) == (actual_dir > 0) else 0)

        return {k: round(sum(v) / len(v) * 100, 1) if v else 50.0 
                for k, v in components.items()}

    # ========================
    #  SELF-LEARNING: Weights
    # ========================

    def save_weights(self, weights: Dict, trigger: str = "auto") -> None:
        """Save weight snapshot to history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weight_history (timestamp, price_weight, pattern_weight,
                                        sentiment_weight, options_weight, trigger)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(),
              weights.get('price_prediction', 0.25),
              weights.get('pattern_recognition', 0.25),
              weights.get('sentiment', 0.25),
              weights.get('options_flow', 0.25),
              trigger))
        conn.commit()
        conn.close()

    def get_latest_weights(self) -> Optional[Dict]:
        """Get the most recent optimized weights."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price_weight, pattern_weight, sentiment_weight, options_weight
            FROM weight_history ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'price_prediction': row[0],
                'pattern_recognition': row[1],
                'sentiment': row[2],
                'options_flow': row[3]
            }
        return None

    def get_weight_history(self, limit: int = 50) -> List[Dict]:
        """Get weight change history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, price_weight, pattern_weight, 
                   sentiment_weight, options_weight, trigger
            FROM weight_history ORDER BY id DESC LIMIT ?
        """, (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    # ========================
    #  SELF-LEARNING: Market Data
    # ========================

    def store_snapshot(self, open: float, high: float, low: float,
                      close: float, volume: float, timeframe: str = '5m') -> int:
        """Store a market data snapshot."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_snapshots (timestamp, open, high, low, close, volume, timeframe)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), open, high, low, close, volume, timeframe))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def get_snapshots(self, days: int = 30, timeframe: str = '5m') -> List[Dict]:
        """Get stored market snapshots."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, open, high, low, close, volume
            FROM market_snapshots
            WHERE timeframe = ?
            AND julianday('now') - julianday(timestamp) <= ?
            ORDER BY timestamp ASC
        """, (timeframe, days))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_snapshot_count(self) -> int:
        """Get total number of stored snapshots."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_snapshots")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    # ========================
    #  SELF-LEARNING: Model Performance
    # ========================

    def log_model_performance(self, model_name: str, version: str,
                              accuracy: float, f1_score: float = 0,
                              samples_used: int = 0) -> None:
        """Log model training performance."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO model_performance 
            (model_name, version, accuracy, f1_score, samples_used, trained_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (model_name, version, accuracy, f1_score, samples_used,
              datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_model_history(self, model_name: str = None, limit: int = 20) -> List[Dict]:
        """Get model performance history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if model_name:
            cursor.execute("""
                SELECT model_name, version, accuracy, f1_score, samples_used, trained_at
                FROM model_performance WHERE model_name = ?
                ORDER BY trained_at DESC LIMIT ?
            """, (model_name, limit))
        else:
            cursor.execute("""
                SELECT model_name, version, accuracy, f1_score, samples_used, trained_at
                FROM model_performance ORDER BY trained_at DESC LIMIT ?
            """, (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_signal_log(self, limit: int = 50) -> List[Dict]:
        """Get recent signal log entries."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, recommendation, score, confidence, nifty_price
            FROM signal_log ORDER BY id DESC LIMIT ?
        """, (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results


    def get_detailed_signal_log(self, limit: int = 1000) -> List[Dict]:
        """Get full detailed signal log entries including components and weights."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sl.*, 
                   so15.was_correct as correct_15m, 
                   so30.was_correct as correct_30m, 
                   so60.was_correct as correct_60m
            FROM signal_log sl
            LEFT JOIN signal_outcomes so15 ON sl.id = so15.signal_id AND so15.check_after_mins = 15
            LEFT JOIN signal_outcomes so30 ON sl.id = so30.signal_id AND so30.check_after_mins = 30
            LEFT JOIN signal_outcomes so60 ON sl.id = so60.signal_id AND so60.check_after_mins = 60
            ORDER BY sl.id DESC LIMIT ?
        """, (limit,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results


if __name__ == "__main__":
    db = DatabaseManager()
    
    db.add_trade(strike=25000, trade_type="CALL", entry_price=150.5, timestamp="2025-01-15T10:00:00")
    db.add_trade(strike=25100, trade_type="PUT", entry_price=75.2)
    
    print("Trades:", db.get_trades())
    print("Config:", db.get_config())
    
    db.update_config(sl=60.0, max_trades=10)
    print("Updated Config:", db.get_config())


if __name__ == "__main__":
    db = DatabaseManager()
    
    db.add_trade(strike=25000, trade_type="CALL", entry_price=150.5, timestamp="2025-01-15T10:00:00")
    db.add_trade(strike=25100, trade_type="PUT", entry_price=75.2)
    
    print("Trades:", db.get_trades())
    print("Config:", db.get_config())
    
    db.update_config(sl=60.0, max_trades=10)
    print("Updated Config:", db.get_config())
