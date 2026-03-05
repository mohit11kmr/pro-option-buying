"""
Phase 14: 3Commas Integration
Create and manage smart trades through 3Commas API.
Author: Nifty Options Toolkit
"""

import requests
import json
import hmac
import hashlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SmartTradeConfig:
    """Configuration for 3Commas smart trade."""
    pair: str  # e.g., "NIFTYUSDT"
    position: str  # "buy" or "sell"
    entry_points: List[Dict]  # [{"percent": 100, "price": 24800}]
    take_profit_price: Optional[float] = None
    stoploss_price: Optional[float] = None
    leverage: float = 1.0
    notes: str = ""


class ThreeCommasAPI:
    """
    3Commas REST API client for smart trade execution.
    
    Requires API key and secret from 3Commas:
    https://3commas.io/api_access_tokens
    """
    
    BASE_URL = "https://api.3commas.io/public/api/v1"
    
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        """
        Initialize 3Commas API client.
        
        Args:
            api_key: 3Commas API key
            api_secret: 3Commas API secret
            use_testnet: Use testnet endpoint
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_testnet = use_testnet
        self.session = requests.Session()
        self.nonce_multiplier = int(time.time() * 1000)
    
    def _get_nonce(self) -> str:
        """Generate unique nonce for API authentication."""
        self.nonce_multiplier += 1
        return str(self.nonce_multiplier)
    
    def _sign_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Sign API request with HMAC-SHA256.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            data: Request body (for POST/PUT)
        
        Returns:
            Headers dict with signature
        """
        nonce = self._get_nonce()
        
        if data:
            body = json.dumps(data)
        else:
            body = ""
        
        # Create signature string
        signature_string = f"{method}\n{path}\n{body}\n{nonce}"
        
        # HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "Authorization": f"Bearer {self.api_key}",
            "NONCE": nonce,
            "Signature": signature,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, path: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """
        Make authenticated API request.
        
        Args:
            method: HTTP method
            path: API endpoint
            data: Request body
        
        Returns:
            Response JSON
        """
        url = f"{self.BASE_URL}{path}"
        headers = self._sign_request(method, path, data)
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=data, **kwargs)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data, **kwargs)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data, **kwargs)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_accounts(self) -> List[Dict]:
        """
        Get list of exchange accounts.
        
        Returns:
            List of account info
        """
        return self._request("GET", "/accounts")
    
    def get_smart_trades(self, account_id: int, status: str = "active") -> List[Dict]:
        """
        Get smart trades for account.
        
        Args:
            account_id: Exchange account ID
            status: "active", "completed", "canceled"
        
        Returns:
            List of smart trades
        """
        return self._request(
            "GET",
            f"/accounts/{account_id}/smart_trades",
            {"status": status}
        )
    
    def create_smart_trade(self, account_id: int, config: SmartTradeConfig) -> Dict:
        """
        Create a smart trade.
        
        Args:
            account_id: Exchange account ID
            config: SmartTradeConfig object
        
        Returns:
            Created trade info
        """
        payload = {
            "pair": config.pair,
            "position": config.position,
            "entry_points": config.entry_points,
            "leverage": {"type": "isolated", "value": config.leverage}
        }
        
        # Add optional fields
        if config.take_profit_price:
            payload["take_profit"] = {
                "type": "price",
                "value": config.take_profit_price
            }
        
        if config.stoploss_price:
            payload["stoploss"] = {
                "type": "price",
                "value": config.stoploss_price
            }
        
        if config.notes:
            payload["notes"] = config.notes
        
        logger.info(f"Creating smart trade: {config.pair}")
        
        return self._request(
            "POST",
            f"/accounts/{account_id}/smart_trades",
            payload
        )
    
    def update_smart_trade(self, account_id: int, trade_id: str, 
                          take_profit: Optional[float] = None,
                          stoploss: Optional[float] = None) -> Dict:
        """
        Update smart trade TP/SL.
        
        Args:
            account_id: Exchange account ID
            trade_id: Smart trade ID
            take_profit: New take profit price
            stoploss: New stop loss price
        
        Returns:
            Updated trade info
        """
        payload = {}
        
        if take_profit:
            payload["take_profit"] = {
                "type": "price",
                "value": take_profit
            }
        
        if stoploss:
            payload["stoploss"] = {
                "type": "price",
                "value": stoploss
            }
        
        logger.info(f"Updating smart trade {trade_id}: TP={take_profit}, SL={stoploss}")
        
        return self._request(
            "PUT",
            f"/accounts/{account_id}/smart_trades/{trade_id}",
            payload
        )
    
    def close_smart_trade(self, account_id: int, trade_id: str) -> Dict:
        """
        Close a smart trade.
        
        Args:
            account_id: Exchange account ID
            trade_id: Smart trade ID
        
        Returns:
            Closed trade info
        """
        logger.info(f"Closing smart trade {trade_id}")
        
        return self._request(
            "DELETE",
            f"/accounts/{account_id}/smart_trades/{trade_id}"
        )
    
    def get_market_data(self, exchange: str, pair: str) -> Dict:
        """
        Get current market data for a pair.
        
        Args:
            exchange: Exchange name (e.g., "binance")
            pair: Trading pair (e.g., "BTCUSDT")
        
        Returns:
            Market data with current price
        """
        # This would use market data endpoint
        # Simplified for example
        return {"price": 0, "pair": pair}


class SmartTradeOrchestrator:
    """
    Orchestrates smart trade creation across multiple exchanges via 3Commas.
    Bridges our trading signals to 3Commas for execution.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize orchestrator."""
        self.api = ThreeCommasAPI(api_key, api_secret)
        self.accounts = {}
        self.active_trades = {}
    
    def initialize(self) -> bool:
        """
        Initialize orchestrator and load accounts.
        
        Returns:
            True if successful
        """
        try:
            accounts = self.api.get_accounts()
            
            for account in accounts:
                self.accounts[account['id']] = {
                    'name': account.get('name'),
                    'exchange': account.get('exchange_name'),
                    'balance': account.get('total_btc')
                }
            
            logger.info(f"Loaded {len(self.accounts)} accounts from 3Commas")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def execute_signal_as_smart_trade(self, account_id: int, signal: Dict) -> Optional[str]:
        """
        Execute trading signal as 3Commas smart trade.
        
        Args:
            account_id: 3Commas account ID
            signal: Trading signal dict with entry/tp/sl
        
        Returns:
            Smart trade ID if successful, None otherwise
        """
        try:
            # Convert signal to smart trade config
            position = "buy" if signal['side'] == 'BUY' else "sell"
            
            config = SmartTradeConfig(
                pair=signal['symbol'],
                position=position,
                entry_points=[{
                    "percent": 100,
                    "price": signal['entry_price']
                }],
                take_profit_price=signal.get('target'),
                stoploss_price=signal.get('stop_loss'),
                notes=f"Signal from {signal.get('source', 'AI')} - {signal.get('strategy', 'Unknown')}"
            )
            
            # Create trade via 3Commas
            result = self.api.create_smart_trade(account_id, config)
            trade_id = result.get('id')
            
            if trade_id:
                self.active_trades[trade_id] = {
                    'account_id': account_id,
                    'symbol': signal['symbol'],
                    'created_at': time.time()
                }
                logger.info(f"Created smart trade {trade_id}")
                
            return trade_id
            
        except Exception as e:
            logger.error(f"Failed to execute signal: {e}")
            return None
    
    def sync_position(self, account_id: int, symbol: str, 
                     current_price: float, new_tp: Optional[float] = None,
                     new_sl: Optional[float] = None) -> bool:
        """
        Synchronize position TP/SL with market conditions.
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            current_price: Current market price
            new_tp: New take profit price
            new_sl: New stop loss price
        
        Returns:
            True if successful
        """
        try:
            trades = self.api.get_smart_trades(account_id, status="active")
            
            for trade in trades:
                if trade['pair'] == symbol:
                    trade_id = trade['id']
                    self.api.update_smart_trade(
                        account_id,
                        trade_id,
                        take_profit=new_tp,
                        stoploss=new_sl
                    )
                    logger.info(f"Synced trade {trade_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to sync position: {e}")
            return False
    
    def close_position(self, account_id: int, symbol: str) -> bool:
        """
        Close position for symbol.
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
        
        Returns:
            True if successful
        """
        try:
            trades = self.api.get_smart_trades(account_id, status="active")
            
            for trade in trades:
                if trade['pair'] == symbol:
                    self.api.close_smart_trade(account_id, trade['id'])
                    logger.info(f"Closed position for {symbol}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary across all accounts.
        
        Returns:
            Portfolio stats
        """
        total_trades = 0
        total_value = 0
        
        for account_id in self.accounts:
            trades = self.api.get_smart_trades(account_id)
            total_trades += len(trades)
        
        return {
            'accounts': len(self.accounts),
            'active_trades': total_trades,
            'synchronized': True
        }


# Example usage
if __name__ == "__main__":
    API_KEY = "YOUR_3COMMAS_API_KEY"
    API_SECRET = "YOUR_3COMMAS_API_SECRET"
    
    orchestrator = SmartTradeOrchestrator(API_KEY, API_SECRET)
    
    if orchestrator.initialize():
        print("\n✅ 3Commas Integration Ready")
        print("=" * 50)
        
        # List accounts
        for account_id, info in orchestrator.accounts.items():
            print(f"Account: {info['name']} ({info['exchange']})")
        
        # Execute sample signal
        sample_signal = {
            'symbol': 'NIFTYUSDT',
            'side': 'BUY',
            'entry_price': 24800,
            'target': 25100,
            'stop_loss': 24650,
            'source': 'AI-Trading-System',
            'strategy': 'MA-Crossover'
        }
        
        # Uncomment to execute (requires valid API credentials)
        # result = orchestrator.execute_signal_as_smart_trade(account_id, sample_signal)
    else:
        print("❌ Failed to initialize 3Commas API")
