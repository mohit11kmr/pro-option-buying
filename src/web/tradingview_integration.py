"""
Phase 14: TradingView Webhook Integration
Receive trading signals from TradingView Alert webhooks.
Author: Nifty Options Toolkit
"""

from flask import Flask, request, jsonify
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import hmac
import hashlib
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradingViewSignal:
    """Represents a TradingView webhook signal."""
    symbol: str
    signal_type: str  # BUY, SELL
    strategy: str
    entry_price: float
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    leverage: float = 1.0
    message: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TradingViewWebhookHandler:
    """
    Handle TradingView Alert webhooks for automated signal execution.
    
    Setup in TradingView:
    1. Create alert with Pine Script condition
    2. Set webhook URL: https://your-domain.com/hooks/tradingview
    3. Set message template with JSON payload
    """
    
    def __init__(self, webhook_secret: str = None):
        """
        Initialize TradingView webhook handler.
        
        Args:
            webhook_secret: Secret for validating webhook signatures
        """
        self.webhook_secret = webhook_secret
        self.signal_history: List[TradingViewSignal] = []
        self.max_history = 1000
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature (if secret is configured).
        
        Args:
            payload: Raw webhook payload
            signature: Provided signature
        
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True  # No verification if secret not set
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_webhook(self, data: Dict) -> Optional[TradingViewSignal]:
        """
        Parse TradingView webhook payload.
        
        Expected message format (in TradingView alert):
        {
            "symbol": "{{ticker}}",
            "signal": "BUY",
            "strategy": "MA-Crossover",
            "entry": {{close}},
            "tp": {{close}} * 1.05,
            "sl": {{close}} * 0.98
        }
        
        Args:
            data: Parsed webhook data
        
        Returns:
            TradingViewSignal object or None if invalid
        """
        try:
            # Extract from nested message field if present
            if 'message' in data:
                message_str = data['message']
                try:
                    message_data = json.loads(message_str)
                    data.update(message_data)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            signal = TradingViewSignal(
                symbol=data.get('symbol', '').upper(),
                signal_type=data.get('signal', data.get('action', 'BUY')).upper(),
                strategy=data.get('strategy', 'TradingView-Alert'),
                entry_price=float(data.get('entry', data.get('price', 0))),
                take_profit=float(data.get('tp', data.get('target', 0))) if data.get('tp') or data.get('target') else None,
                stop_loss=float(data.get('sl', data.get('stoploss', 0))) if data.get('sl') or data.get('stoploss') else None,
                leverage=float(data.get('leverage', 1.0)),
                message=data.get('message', '')
            )
            
            # Validate required fields
            if not signal.symbol or signal.entry_price <= 0:
                logger.warning(f"Invalid signal: missing required fields")
                return None
            
            logger.info(f"Parsed TradingView signal: {signal.symbol} {signal.signal_type} @ {signal.entry_price}")
            return signal
            
        except Exception as e:
            logger.error(f"Failed to parse webhook: {e}")
            return None
    
    def process_signal(self, signal: TradingViewSignal) -> Dict:
        """
        Process signal and execute trade.
        
        Args:
            signal: TradingViewSignal object
        
        Returns:
            Execution result
        """
        # Add to history
        self.signal_history.append(signal)
        if len(self.signal_history) > self.max_history:
            self.signal_history.pop(0)
        
        logger.info(f"Processing signal: {signal}")
        
        result = {
            'status': 'processed',
            'signal_id': f"TV{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'symbol': signal.symbol,
            'action': signal.signal_type,
            'entry_price': signal.entry_price,
            'message': f"Signal received from {signal.strategy}"
        }
        
        # TODO: Execute trade based on signal
        # - Route to appropriate broker adapter
        # - Apply risk management rules
        # - Log to database
        # - Send notifications
        
        return result
    
    def get_signal_history(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get signal history.
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Number of signals to return
        
        Returns:
            List of signals
        """
        signals = self.signal_history
        
        if symbol:
            signals = [s for s in signals if s.symbol == symbol.upper()]
        
        # Return most recent signals
        return [
            {
                'symbol': s.symbol,
                'signal': s.signal_type,
                'entry': s.entry_price,
                'tp': s.take_profit,
                'sl': s.stop_loss,
                'strategy': s.strategy,
                'timestamp': s.timestamp
            }
            for s in signals[-limit:]
        ]
    
    def get_statistics(self) -> Dict:
        """Get statistics about received signals."""
        if not self.signal_history:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'symbols_traded': [],
                'strategies_used': []
            }
        
        buy_count = sum(1 for s in self.signal_history if s.signal_type == 'BUY')
        sell_count = sum(1 for s in self.signal_history if s.signal_type == 'SELL')
        symbols = set(s.symbol for s in self.signal_history)
        strategies = set(s.strategy for s in self.signal_history)
        
        return {
            'total_signals': len(self.signal_history),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'buy_sell_ratio': buy_count / sell_count if sell_count > 0 else buy_count,
            'symbols_traded': list(symbols),
            'strategies_used': list(strategies),
            'unique_symbols': len(symbols),
            'unique_strategies': len(strategies)
        }


def create_tradingview_routes(app: Flask, handler: TradingViewWebhookHandler):
    """
    Register TradingView webhook routes.
    
    Args:
        app: Flask application
        handler: TradingViewWebhookHandler instance
    """
    
    @app.route('/hooks/tradingview', methods=['POST'])
    def tradingview_webhook():
        """
        Main webhook endpoint for TradingView alerts.
        
        Expected JSON payload:
        {
            "symbol": "NIFTY",
            "signal": "BUY",
            "strategy": "MA-Crossover",
            "entry": 24800,
            "tp": 25100,
            "sl": 24650
        }
        """
        try:
            # Get and log raw data for debugging
            raw_data = request.get_data(as_text=True)
            
            # Verify signature if configured
            signature = request.headers.get('X-TV-Signature', '')
            if not handler.verify_signature(raw_data, signature):
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Parse JSON
            try:
                data = request.get_json()
            except Exception as e:
                logger.error(f"Failed to parse JSON: {e}")
                return jsonify({'error': 'Invalid JSON'}), 400
            
            logger.info(f"Received TradingView webhook: {data}")
            
            # Parse signal
            signal = handler.parse_webhook(data)
            if not signal:
                return jsonify({'error': 'Invalid signal data'}), 400
            
            # Process signal
            result = handler.process_signal(signal)
            
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/hooks/tradingview/signals', methods=['GET'])
    def tradingview_signal_history():
        """Get TradingView signal history."""
        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 10))
        
        history = handler.get_signal_history(symbol, limit)
        return jsonify({'signals': history}), 200
    
    @app.route('/hooks/tradingview/stats', methods=['GET'])
    def tradingview_statistics():
        """Get TradingView signal statistics."""
        stats = handler.get_statistics()
        return jsonify(stats), 200
    
    @app.route('/hooks/tradingview/test', methods=['GET', 'POST'])
    def tradingview_test():
        """Test endpoint for TradingView webhook configuration."""
        if request.method == 'POST':
            # Simulate receiving a signal
            test_signal = {
                "symbol": "NIFTY",
                "signal": "BUY",
                "strategy": "Test-Strategy",
                "entry": 24800,
                "tp": 25100,
                "sl": 24650
            }
            result = handler.process_signal(handler.parse_webhook(test_signal))
            return jsonify({
                'message': 'Test signal processed',
                'result': result
            }), 200
        
        return jsonify({
            'message': 'TradingView webhook is operational',
            'webhook_url': '/hooks/tradingview',
            'test_url': '/hooks/tradingview/test',
            'history_url': '/hooks/tradingview/signals',
            'stats_url': '/hooks/tradingview/stats'
        }), 200


# Pine Script example for TradingView alert
PINESCRIPT_EXAMPLE = """
//@version=5
strategy("Trading System Webhook", overlay=true)

// Your strategy logic here
ma20 = ta.sma(close, 20)
ma50 = ta.sma(close, 50)

buySignal = ta.crossover(ma20, ma50)
sellSignal = ta.crossunder(ma20, ma50)

if buySignal
    strategy.entry("BUY", strategy.long)
    
if sellSignal
    strategy.close("BUY")

// Webhook message for external execution
webhookMessage = json.stringify(json.object(
    "symbol", syminfo.tickerid,
    "signal", buySignal ? "BUY" : sellSignal ? "SELL" : "HOLD",
    "strategy", "MA-Crossover",
    "entry", close,
    "tp", close * 1.05,
    "sl", close * 0.98,
    "leverage", 1.0
))

// Alert (place this in TradingView alert with webhook)
if buySignal or sellSignal
    alert(webhookMessage, alert.freq_once_per_bar)
"""


if __name__ == "__main__":
    from flask import Flask
    
    app = Flask(__name__)
    handler = TradingViewWebhookHandler(webhook_secret=None)
    
    create_tradingview_routes(app, handler)
    
    print("\n🎯 TradingView Webhook Integration")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST   /hooks/tradingview  - Main webhook")
    print("  GET    /hooks/tradingview/signals - Signal history")
    print("  GET    /hooks/tradingview/stats - Statistics")
    print("  GET/POST /hooks/tradingview/test - Test endpoint")
    print("\nExample TradingView Alert Message:")
    print(json.dumps({
        "symbol": "NIFTY",
        "signal": "BUY",
        "strategy": "MA-Crossover",
        "entry": 24800,
        "tp": 25100,
        "sl": 24650
    }, indent=2))
    print("\n")
    
    app.run(debug=True, port=5000)
