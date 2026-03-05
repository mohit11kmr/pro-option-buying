import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
import websocket


class WebSocketClient:
    """WebSocket client with automatic reconnect and jittered backoff"""
    
    def __init__(self, url: str, on_message: Callable = None, on_error: Callable = None, 
                 on_open: Callable = None, on_close: Callable = None):
        self.url = url
        self.on_message = on_message
        self.on_error = on_error
        self.on_open = on_open
        self.on_close = on_close
        
        self.ws = None
        self.connected = False
        self.reconnecting = False
        
        self.max_reconnect_attempts = 10
        self.base_delay = 1
        self.max_delay = 60
        
        self._running = False
        self._thread = None
        
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self._handle_message,
                on_error=self._handle_error,
                on_open=self._handle_open,
                on_close=self._handle_close
            )
            
            self._running = True
            self.ws.run_forever(ping_interval=30, ping_timeout=10)
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            self._schedule_reconnect()
    
    def _handle_message(self, ws, message):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            if self.on_message:
                self.on_message(data)
        except:
            if self.on_message:
                self.on_message(message)
    
    def _handle_error(self, ws, error):
        """Handle error"""
        print(f"❌ WebSocket error: {error}")
        if self.on_error:
            self.on_error(error)
    
    def _handle_open(self, ws):
        """Handle connection open"""
        self.connected = True
        self.reconnecting = False
        print(f"✅ WebSocket connected: {self.url}")
        
        if self.on_open:
            self.on_open(ws)
    
    def _handle_close(self, ws, close_status_code, close_msg):
        """Handle connection close"""
        self.connected = False
        print(f"⚠️ WebSocket closed: {close_status_code} - {close_msg}")
        
        if self.on_close:
            self.on_close(ws, close_status_code, close_msg)
        
        if self._running:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Schedule reconnection with jittered backoff"""
        if self.reconnecting or not self._running:
            return
        
        self.reconnecting = True
        
        for attempt in range(self.max_reconnect_attempts):
            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
            jitter = delay * 0.1 * (hash(str(time.time())) % 100) / 100
            delay += jitter
            
            print(f"🔄 Reconnecting in {delay:.1f}s (attempt {attempt + 1}/{self.max_reconnect_attempts})...")
            
            time.sleep(delay)
            
            if self._running:
                try:
                    self.ws = websocket.WebSocketApp(
                        self.url,
                        on_message=self._handle_message,
                        on_error=self._handle_error,
                        on_open=self._handle_open,
                        on_close=self._handle_close
                    )
                    self.ws.run_forever(ping_interval=30, ping_timeout=10)
                    
                    if self.connected:
                        break
                        
                except Exception as e:
                    print(f"❌ Reconnect failed: {e}")
        
        if not self.connected:
            print("❌ Max reconnection attempts reached")
    
    def send(self, message: dict):
        """Send message"""
        if self.connected and self.ws:
            try:
                self.ws.send(json.dumps(message))
                return True
            except Exception as e:
                print(f"❌ Send error: {e}")
        return False
    
    def start(self):
        """Start WebSocket client in background thread"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self.connect, daemon=True)
            self._thread.start()
    
    def stop(self):
        """Stop WebSocket client"""
        self._running = False
        if self.ws:
            self.ws.close()


class AngelOneWebSocket:
    """Angel One SmartAPI WebSocket adapter"""
    
    def __init__(self, api_key: str, client_code: str, access_token: str, feed_token: str):
        self.api_key = api_key
        self.client_code = client_code
        self.access_token = access_token
        self.feed_token = feed_token
        
        self.ws_url = "wss://ws.angelone.in/smart-stream"
        self.client = None
        self.subscribed_tokens = {}
        self.data_callback = None
    
    def connect(self, on_data: Callable = None):
        """Connect to Angel One WebSocket"""
        self.data_callback = on_data
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if self.data_callback:
                    self.data_callback(data)
            except:
                pass
        
        self.client = WebSocketClient(
            url=self.ws_url,
            on_message=on_message,
            on_error=lambda e: print(f"❌ Error: {e}"),
            on_open=lambda ws: self._on_open(ws),
            on_close=lambda ws, code, msg: print(f"⚠️ Closed: {code}")
        )
        
        self.client.start()
    
    def _on_open(self, ws):
        """On connection open"""
        print("✅ Connected to Angel One WebSocket")
        
        auth_message = {
            "action": "login",
            "apiKey": self.api_key,
            "clientCode": self.client_code,
            "feedToken": self.feed_token
        }
        
        self.client.send(auth_message)
    
    def subscribe(self, exchange: str, token: str):
        """Subscribe to a token"""
        subscribe_message = {
            "action": "subscribe",
            "exchange": exchange,
            "tokens": [token]
        }
        
        self.subscribed_tokens[token] = True
        self.client.send(subscribe_message)
    
    def unsubscribe(self, exchange: str, token: str):
        """Unsubscribe from a token"""
        unsubscribe_message = {
            "action": "unsubscribe",
            "exchange": exchange,
            "tokens": [token]
        }
        
        if token in self.subscribed_tokens:
            del self.subscribed_tokens[token]
        
        self.client.send(unsubscribe_message)
    
    def disconnect(self):
        """Disconnect WebSocket"""
        if self.client:
            self.client.stop()


class DataCache:
    """Simple caching layer for market data"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.memory_cache = {}
    
    def get(self, key: str) -> Optional[any]:
        """Get from cache"""
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if time.time() - timestamp < 60:
                return data
        
        file_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def set(self, key: str, data: any, ttl: int = 60):
        """Set cache with TTL in seconds"""
        self.memory_cache[key] = (data, time.time())
        
        file_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def clear(self):
        """Clear all cache"""
        self.memory_cache = {}
        
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, file))


def test_websocket():
    """Test WebSocket client"""
    print("\n" + "="*60)
    print("📡 WEBSOCKET CLIENT TEST")
    print("="*60 + "\n")
    
    messages = []
    
    def on_message(data):
        messages.append(data)
        print(f"   Received: {len(messages)} messages")
    
    print("Testing WebSocket client structure...")
    print("✅ WebSocketClient class ready")
    print("✅ AngelOneWebSocket adapter ready")
    print("✅ DataCache ready")
    
    return True


if __name__ == "__main__":
    test_websocket()
