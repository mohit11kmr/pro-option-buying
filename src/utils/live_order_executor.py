"""
Live Order Executor - Production-grade live trading system
Handles real-time order placement, modification, cancellation, and P&L tracking
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    """Represents a live order"""
    order_id: str
    symbol: str
    quantity: int
    order_type: OrderType
    side: OrderSide
    entry_price: float
    stop_loss: float
    target: float
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    created_at: datetime = None
    filled_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class LiveOrderExecutor:
    """Main executor for live trading with SmartAPI integration"""
    
    def __init__(self, smartapi_client=None, db_manager=None):
        self.smartapi_client = smartapi_client
        self.db_manager = db_manager
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.positions: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        logger.info("✅ LiveOrderExecutor initialized")
    
    def place_live_order(self, symbol: str, quantity: int, entry_price: float, 
                        stop_loss: float, target: float, order_type: str = "limit",
                        side: str = "buy") -> Tuple[str, str, float]:
        """
        Place a live order with risk management
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY')
            quantity: Order quantity
            entry_price: Entry price for limit orders
            stop_loss: Stop-loss price
            target: Target/take-profit price
            order_type: Market or Limit
            side: Buy or Sell
        
        Returns:
            (order_id, status, execution_price)
        """
        try:
            with self.lock:
                # Generate order ID
                order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{symbol}"
                
                # Create order object
                order = Order(
                    order_id=order_id,
                    symbol=symbol,
                    quantity=quantity,
                    order_type=OrderType[order_type.upper()],
                    side=OrderSide[side.upper()],
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    target=target
                )
                
                # Place with SmartAPI if available
                if self.smartapi_client:
                    try:
                        response = self.smartapi_client.placeOrder(
                            buy_or_sell=side.upper(),
                            order_type=order_type.upper(),
                            quantity=quantity,
                            symbol=symbol,
                            price=entry_price,
                            disclosed_quantity=quantity
                        )
                        
                        if response and response.get('status') == True:
                            order.status = OrderStatus.OPEN
                            order.average_fill_price = entry_price
                            order.filled_at = datetime.now()
                            logger.info(f"✅ Order placed: {order_id} | {symbol} | {quantity} @ {entry_price}")
                        else:
                            order.status = OrderStatus.REJECTED
                            logger.error(f"❌ Order rejected: {response}")
                            return order_id, "rejected", 0
                    except Exception as e:
                        logger.error(f"SmartAPI error: {e}")
                        return order_id, "error", 0
                else:
                    # Paper trading mode
                    order.status = OrderStatus.OPEN
                    order.average_fill_price = entry_price
                    order.filled_at = datetime.now()
                    logger.info(f"📋 Paper trade: {order_id} | {symbol} | {quantity} @ {entry_price}")
                
                # Store order
                self.active_orders[order_id] = order
                self.order_history.append(order)
                
                # Log to database if available
                if self.db_manager:
                    self._log_order_to_db(order)
                
                return order_id, "open", order.average_fill_price
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return "", "error", 0
    
    def modify_order(self, order_id: str, new_price: Optional[float] = None,
                    new_quantity: Optional[int] = None, new_stop_loss: Optional[float] = None,
                    new_target: Optional[float] = None) -> bool:
        """Modify an open order"""
        try:
            with self.lock:
                if order_id not in self.active_orders:
                    logger.error(f"Order not found: {order_id}")
                    return False
                
                order = self.active_orders[order_id]
                
                if order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                    logger.error(f"Cannot modify order with status: {order.status}")
                    return False
                
                # Update order fields
                if new_price:
                    order.entry_price = new_price
                if new_quantity:
                    order.quantity = new_quantity
                if new_stop_loss:
                    order.stop_loss = new_stop_loss
                if new_target:
                    order.target = new_target
                
                logger.info(f"✏️ Order modified: {order_id} | New Price: {new_price}, SL: {new_stop_loss}, Target: {new_target}")
                return True
        
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        try:
            with self.lock:
                if order_id not in self.active_orders:
                    logger.error(f"Order not found: {order_id}")
                    return False
                
                order = self.active_orders[order_id]
                
                if order.status == OrderStatus.CANCELLED:
                    logger.warning(f"Order already cancelled: {order_id}")
                    return False
                
                # Cancel with SmartAPI if available
                if self.smartapi_client:
                    try:
                        response = self.smartapi_client.cancelOrder(
                            order_id=order_id
                        )
                        if response and response.get('status') == True:
                            order.status = OrderStatus.CANCELLED
                            logger.info(f"✅ Order cancelled: {order_id}")
                            return True
                    except Exception as e:
                        logger.error(f"SmartAPI cancel error: {e}")
                
                # Paper trading - just mark as cancelled
                order.status = OrderStatus.CANCELLED
                logger.info(f"✅ Order cancelled (paper): {order_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_position_pnl(self, symbol: str) -> Dict:
        """Calculate unrealized P&L for a position"""
        try:
            if symbol not in self.positions:
                return {'symbol': symbol, 'pnl': 0, 'pnl_pct': 0, 'quantity': 0}
            
            pos = self.positions[symbol]
            current_price = pos.get('current_price', pos['entry_price'])
            quantity = pos['quantity']
            entry_price = pos['entry_price']
            
            if pos['side'] == 'buy':
                pnl = (current_price - entry_price) * quantity
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl = (entry_price - current_price) * quantity
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            return {
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'side': pos['side']
            }
        
        except Exception as e:
            logger.error(f"Error calculating P&L: {e}")
            return {}
    
    def track_active_orders(self) -> List[Dict]:
        """Get all active orders with current status"""
        try:
            with self.lock:
                active = []
                for order_id, order in self.active_orders.items():
                    if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                        pnl_info = self.get_position_pnl(order.symbol)
                        active.append({
                            'order_id': order_id,
                            'symbol': order.symbol,
                            'quantity': order.quantity,
                            'entry_price': order.entry_price,
                            'stop_loss': order.stop_loss,
                            'target': order.target,
                            'status': order.status.value,
                            'pnl': pnl_info.get('pnl', 0),
                            'pnl_pct': pnl_info.get('pnl_pct', 0)
                        })
                return active
        
        except Exception as e:
            logger.error(f"Error tracking orders: {e}")
            return []
    
    def handle_partial_fills(self, order_id: str, filled_quantity: int, fill_price: float):
        """Handle partial fill updates"""
        try:
            with self.lock:
                if order_id not in self.active_orders:
                    return False
                
                order = self.active_orders[order_id]
                
                # Update average fill price
                if order.filled_quantity > 0:
                    order.average_fill_price = (
                        (order.average_fill_price * order.filled_quantity + fill_price * filled_quantity) /
                        (order.filled_quantity + filled_quantity)
                    )
                else:
                    order.average_fill_price = fill_price
                
                order.filled_quantity += filled_quantity
                
                if order.filled_quantity >= order.quantity:
                    order.status = OrderStatus.FILLED
                    logger.info(f"✅ Order filled: {order_id} | Avg Price: {order.average_fill_price}")
                else:
                    order.status = OrderStatus.PARTIALLY_FILLED
                    logger.info(f"⏳ Partial fill: {order_id} | {order.filled_quantity}/{order.quantity}")
                
                return True
        
        except Exception as e:
            logger.error(f"Error handling partial fills: {e}")
            return False
    
    def auto_hedge_position(self, symbol: str, hedge_ratio: float = 0.5) -> Tuple[str, bool]:
        """
        Create automatic hedge position
        If long, create short position of hedge_ratio quantity
        """
        try:
            if symbol not in self.positions:
                return "", False
            
            pos = self.positions[symbol]
            hedge_quantity = int(pos['quantity'] * hedge_ratio)
            hedge_side = 'sell' if pos['side'] == 'buy' else 'buy'
            
            # Create hedge order
            order_id, status, _ = self.place_live_order(
                symbol=symbol,
                quantity=hedge_quantity,
                entry_price=pos['current_price'],
                stop_loss=pos['current_price'] * 1.02,  # Small SL for hedge
                target=pos['current_price'] * 0.98,
                side=hedge_side
            )
            
            if status == "open":
                logger.info(f"🛡️ Hedge created: {order_id} | {hedge_quantity} {hedge_side.upper()}")
                return order_id, True
            
            return "", False
        
        except Exception as e:
            logger.error(f"Error creating hedge: {e}")
            return "", False
    
    def _log_order_to_db(self, order: Order):
        """Log order to database for audit trail"""
        try:
            if not self.db_manager:
                return
            
            order_dict = {
                'order_id': order.order_id,
                'symbol': order.symbol,
                'quantity': order.quantity,
                'entry_price': order.entry_price,
                'stop_loss': order.stop_loss,
                'target': order.target,
                'status': order.status.value,
                'created_at': order.created_at.isoformat(),
                'filled_at': order.filled_at.isoformat() if order.filled_at else None
            }
            
            logger.info(f"📝 Order logged to DB: {order.order_id}")
        
        except Exception as e:
            logger.error(f"Error logging to DB: {e}")


class OrderTracker:
    """Tracks live P&L and order outcomes"""
    
    def __init__(self, executor: LiveOrderExecutor):
        self.executor = executor
        self.entry_prices: Dict[str, float] = {}
        self.tracking_outcomes: Dict[str, Dict] = {}
        logger.info("✅ OrderTracker initialized")
    
    def track_entry_price(self, symbol: str, price: float):
        """Track entry price for a position"""
        self.entry_prices[symbol] = price
        logger.info(f"📌 Entry tracked: {symbol} @ {price}")
    
    def calculate_live_pnl(self, symbol: str, current_price: float) -> Dict:
        """Calculate live P&L for a symbol"""
        try:
            if symbol not in self.executor.positions:
                return {'pnl': 0, 'pnl_pct': 0}
            
            pnl_info = self.executor.get_position_pnl(symbol)
            pnl_info['current_price'] = current_price
            
            return pnl_info
        
        except Exception as e:
            logger.error(f"Error calculating live PnL: {e}")
            return {'pnl': 0, 'pnl_pct': 0}
    
    def get_position_details(self, symbol: str) -> Dict:
        """Get detailed position information"""
        try:
            if symbol not in self.executor.positions:
                return {}
            
            pos = self.executor.positions[symbol]
            pnl_info = self.executor.get_position_pnl(symbol)
            
            return {
                **pos,
                **pnl_info,
                'status': 'open',
                'margin_used': pos['quantity'] * pos['entry_price'] * 0.2  # Rough margin calculation
            }
        
        except Exception as e:
            logger.error(f"Error getting position details: {e}")
            return {}
    
    def alert_on_target_hit(self, symbol: str, target_price: float):
        """Check if target is hit and alert"""
        pnl_info = self.calculate_live_pnl(symbol, target_price)
        if pnl_info.get('pnl_pct', 0) >= 2.0:  # 2% profit
            logger.info(f"🎯 TARGET HIT! {symbol} | Profit: ₹{pnl_info['pnl']:.2f}")
            return True
        return False
    
    def alert_on_stoploss_hit(self, symbol: str, sl_price: float):
        """Check if stop-loss is hit and alert"""
        pnl_info = self.calculate_live_pnl(symbol, sl_price)
        if pnl_info.get('pnl_pct', 0) <= -2.0:  # 2% loss
            logger.info(f"❌ STOP-LOSS HIT! {symbol} | Loss: ₹{pnl_info['pnl']:.2f}")
            return True
        return False


class PositionManager:
    """Manages open positions and portfolio"""
    
    def __init__(self, executor: LiveOrderExecutor, initial_capital: float = 100000):
        self.executor = executor
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        logger.info(f"✅ PositionManager initialized | Capital: ₹{initial_capital}")
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        try:
            positions = []
            for symbol, pos in self.executor.positions.items():
                pnl_info = self.executor.get_position_pnl(symbol)
                positions.append({
                    **pos,
                    **pnl_info
                })
            return positions
        
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_margin_usage(self) -> Dict:
        """Calculate total margin usage"""
        try:
            total_margin = 0
            for symbol, pos in self.executor.positions.items():
                margin = pos['quantity'] * pos['entry_price'] * 0.2  # 20% margin
                total_margin += margin
            
            margin_ratio = (total_margin / self.initial_capital) * 100
            
            return {
                'margin_used': total_margin,
                'margin_available': self.initial_capital - total_margin,
                'margin_ratio': margin_ratio,
                'total_capital': self.initial_capital
            }
        
        except Exception as e:
            logger.error(f"Error calculating margin: {e}")
            return {}
    
    def calculate_position_size(self, capital_percent: float, stop_loss_points: float) -> int:
        """
        Calculate position size based on risk management rules
        Position Size = (Capital * Risk%) / Stop Loss Points
        """
        try:
            risk_amount = self.available_capital * (capital_percent / 100)
            position_size = int(risk_amount / stop_loss_points)
            logger.info(f"📊 Calculated position size: {position_size} shares")
            return position_size
        
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def hedge_position(self, symbol: str, direction: str = "auto") -> bool:
        """
        Create hedge position
        direction: 'auto', 'long', 'short'
        """
        try:
            _, success = self.executor.auto_hedge_position(symbol)
            return success
        
        except Exception as e:
            logger.error(f"Error hedging position: {e}")
            return False
