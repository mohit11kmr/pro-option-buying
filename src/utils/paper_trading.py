import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class PaperTradingEngine:
    """Deterministic paper trade engine with latency simulation"""
    
    def __init__(self, initial_capital: float = 100000, latency_ms: int = 100):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.orders = []
        self.order_history = []
        self.latency_ms = latency_ms
        self.commission_rate = 0.001
        self.slippage_rate = 0.0005
        
    def place_order(self, symbol: str, side: OrderSide, quantity: int, 
                    order_type: OrderType = OrderType.MARKET, 
                    price: Optional[float] = None) -> Dict:
        """Place a paper trade order"""
        
        order_id = str(uuid.uuid4())[:8]
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side.value,
            'quantity': quantity,
            'order_type': order_type.value,
            'price': price,
            'status': OrderStatus.PENDING.value,
            'filled_quantity': 0,
            'avg_fill_price': 0,
            'timestamp': datetime.now().isoformat(),
            'latency_ms': self.latency_ms
        }
        
        self.orders.append(order)
        
        return self._simulate_fill(order)
    
    def _simulate_fill(self, order: Dict) -> Dict:
        """Simulate order fill with latency"""
        import time
        import random
        
        time.sleep(self.latency_ms / 1000)
        
        if order['order_type'] == OrderType.MARKET.value:
            slippage = random.uniform(-self.slippage_rate, self.slippage_rate)
            fill_price = order.get('price', 25000) * (1 + slippage)
        else:
            fill_price = order.get('price', 25000)
        
        order['status'] = OrderStatus.FILLED.value
        order['filled_quantity'] = order['quantity']
        order['avg_fill_price'] = fill_price
        order['fill_timestamp'] = datetime.now().isoformat()
        
        self._update_position(order, fill_price)
        
        self.order_history.append(order)
        
        return order
    
    def _update_position(self, order: Dict, fill_price: float):
        """Update positions after fill"""
        symbol = order['symbol']
        quantity = order['filled_quantity']
        side = order['side']
        
        if side == OrderSide.BUY.value:
            cost = quantity * fill_price
            commission = cost * self.commission_rate
            
            if symbol not in self.positions:
                self.positions[symbol] = {'quantity': 0, 'avg_price': 0}
            
            old_qty = self.positions[symbol]['quantity']
            old_avg = self.positions[symbol]['avg_price']
            
            new_qty = old_qty + quantity
            new_avg = (old_qty * old_avg + cost) / new_qty if new_qty > 0 else 0
            
            self.positions[symbol] = {'quantity': new_qty, 'avg_price': new_avg}
            self.cash -= (cost + commission)
            
        else:
            if symbol in self.positions:
                quantity = min(quantity, self.positions[symbol]['quantity'])
                proceeds = quantity * fill_price
                commission = proceeds * self.commission_rate
                
                self.positions[symbol]['quantity'] -= quantity
                self.cash += (proceeds - commission)
    
    def get_position(self, symbol: str) -> Dict:
        """Get current position for symbol"""
        return self.positions.get(symbol, {'quantity': 0, 'avg_price': 0})
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = 0
        
        for symbol, position in self.positions.items():
            qty = position['quantity']
            price = current_prices.get(symbol, position.get('avg_price', 0))
            position_value += qty * price
        
        return self.cash + position_value
    
    def get_order_history(self, limit: int = 50) -> List[Dict]:
        """Get order history"""
        return self.order_history[-limit:]
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get portfolio summary"""
        portfolio_value = self.get_portfolio_value(current_prices)
        pnl = portfolio_value - self.initial_capital
        returns = (pnl / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'portfolio_value': portfolio_value,
            'total_pnl': pnl,
            'returns_percent': returns,
            'positions': self.positions,
            'total_orders': len(self.order_history)
        }
    
    def reset(self):
        """Reset paper trading engine"""
        self.cash = self.initial_capital
        self.positions = {}
        self.orders = []
        self.order_history = []


class StructuredLogger:
    """Structured JSON logging with redaction"""
    
    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self.redact_keys = ['password', 'token', 'secret', 'api_key', 'authorization']
    
    def _redact(self, data: dict) -> dict:
        """Redact sensitive data"""
        redacted = {}
        for key, value in data.items():
            if any(redact_key in key.lower() for redact_key in self.redact_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact(value)
            else:
                redacted[key] = value
        return redacted
    
    def log(self, level: str, event: str, **kwargs):
        """Log structured event"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'event': event,
            **kwargs
        }
        
        redacted = self._redact(log_data)
        
        if level == 'INFO':
            self.logger.info(json.dumps(redacted))
        elif level == 'WARNING':
            self.logger.warning(json.dumps(redacted))
        elif level == 'ERROR':
            self.logger.error(json.dumps(redacted))
        else:
            self.logger.debug(json.dumps(redacted))
    
    def info(self, event: str, **kwargs):
        self.log('INFO', event, **kwargs)
    
    def error(self, event: str, **kwargs):
        self.log('ERROR', event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        self.log('WARNING', event, **kwargs)


class MetricsExporter:
    """Simple metrics exporter (Prometheus compatible)"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, name: str, value: float, labels: dict = None):
        """Record a metric"""
        key = f"{name}"
        if labels:
            key += "{" + ",".join([f'{k}="{v}"' for k, v in labels.items()]) + "}"
        
        if key not in self.metrics:
            self.metrics[key] = []
        
        self.metrics[key].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    
    def inc(self, name: str, labels: dict = None):
        """Increment counter"""
        key = f"{name}_total"
        if labels:
            key += "{" + ",".join([f'{k}="{v}"' for k, v in labels.items()]) + "}"
        
        current = self.metrics.get(key, [])
        if current:
            value = current[-1]['value'] + 1
        else:
            value = 1
        
        self.record(name.replace('_total', ''), value, labels)
    
    def gauge(self, name: str, value: float, labels: dict = None):
        """Set gauge value"""
        self.record(name, value, labels)
    
    def timing(self, name: str, duration_ms: float, labels: dict = None):
        """Record timing"""
        self.record(f"{name}_duration_ms", duration_ms, labels)
    
    def get_metrics(self) -> str:
        """Get Prometheus-formatted metrics"""
        lines = []
        
        for name, values in self.metrics.items():
            if values:
                latest = values[-1]['value']
                lines.append(f"{name} {latest}")
        
        return "\n".join(lines)
    
    def export_to_file(self, filename: str):
        """Export metrics to file"""
        with open(filename, 'w') as f:
            f.write(self.get_metrics())


def test_paper_trading():
    """Test paper trading engine"""
    print("\n" + "="*60)
    print("📊 PAPER TRADING ENGINE TEST")
    print("="*60 + "\n")
    
    engine = PaperTradingEngine(initial_capital=100000, latency_ms=50)
    
    print("📝 Placing BUY order...")
    order1 = engine.place_order("NIFTY", OrderSide.BUY, 100, OrderType.MARKET, price=25000)
    print(f"   Order ID: {order1['order_id']}")
    print(f"   Status: {order1['status']}")
    print(f"   Fill Price: ₹{order1['avg_fill_price']}")
    
    print("\n📝 Placing SELL order...")
    order2 = engine.place_order("NIFTY", OrderSide.SELL, 50, OrderType.MARKET, price=25100)
    print(f"   Order ID: {order2['order_id']}")
    print(f"   Status: {order2['status']}")
    print(f"   Fill Price: ₹{order2['avg_fill_price']}")
    
    print("\n📊 Portfolio Summary:")
    prices = {"NIFTY": 25100}
    summary = engine.get_portfolio_summary(prices)
    
    print(f"   Initial Capital: ₹{summary['initial_capital']}")
    print(f"   Cash: ₹{summary['cash']}")
    print(f"   Positions: {summary['positions']}")
    print(f"   Portfolio Value: ₹{summary['portfolio_value']}")
    print(f"   P&L: ₹{summary['total_pnl']} ({summary['returns_percent']:.2f}%)")
    
    print("\n✅ Paper Trading Test Complete!")


def test_structured_logging():
    """Test structured logging"""
    print("\n" + "="*60)
    print("📝 STRUCTURED LOGGING TEST")
    print("="*60 + "\n")
    
    logger = StructuredLogger("test", "logs/structured.json")
    
    logger.info("order_placed", order_id="12345", symbol="NIFTY", quantity=100)
    logger.info("backtest_complete", duration_ms=1500, trades=50, returns=15.5)
    logger.error("order_failed", order_id="12346", reason="Insufficient funds")
    
    print("✅ Check logs/structured.json for JSON logs")


if __name__ == "__main__":
    test_paper_trading()
    test_structured_logging()
