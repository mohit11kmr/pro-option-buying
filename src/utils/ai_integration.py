import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.ml import AISignalGenerator, RiskAdjustedSignalGenerator
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Optional


class AIIntegration:
    def __init__(self):
        self.signal_generator = AISignalGenerator()
        self.risk_adjusted_generator = RiskAdjustedSignalGenerator()
        self.last_signal = None
        self.signal_cache_file = "ai_signal_cache.json"
        
    def get_ai_signal(self, market_data: Dict, options_data: Optional[Dict] = None) -> Dict:
        try:
            df = pd.DataFrame(market_data)
            
            signal = self.signal_generator.generate_comprehensive_signal(df, options_data)
            
            self.last_signal = signal
            self._cache_signal(signal)
            
            return signal
            
        except Exception as e:
            return {
                "error": str(e),
                "recommendation": "HOLD",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_risk_adjusted_signal(self, market_data: Dict, account_balance: float, options_data: Optional[Dict] = None) -> Dict:
        try:
            df = pd.DataFrame(market_data)
            
            signal = self.risk_adjusted_generator.generate_signal_with_risk(
                df, account_balance, options_data
            )
            
            self.last_signal = signal
            self._cache_signal(signal)
            
            return signal
            
        except Exception as e:
            return {
                "error": str(e),
                "recommendation": "HOLD",
                "timestamp": datetime.now().isoformat()
            }
    
    def _cache_signal(self, signal: Dict):
        try:
            with open(self.signal_cache_file, 'w') as f:
                json.dump(signal, f, indent=2)
        except Exception:
            pass
    
    def get_cached_signal(self) -> Optional[Dict]:
        try:
            if os.path.exists(self.signal_cache_file):
                with open(self.signal_cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def format_signal_for_telegram(self, signal: Dict) -> str:
        recommendation = signal.get('recommendation', 'HOLD')
        score = signal.get('score', 0)
        confidence = signal.get('confidence', 0)
        
        emoji_map = {
            'STRONG_BUY': '🟢🟢',
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴',
            'STRONG_SELL': '🔴🔴'
        }
        
        emoji = emoji_map.get(recommendation, '⚪')
        
        message = f"""
🤖 AI Signal Update

{emoji} Recommendation: {recommendation}
📊 Score: {score}
🎯 Confidence: {confidence}%

"""
        
        if 'reasons' in signal:
            message += "📝 Reasons:\n"
            for reason in signal['reasons'][:3]:
                message += f"• {reason}\n"
        
        if 'position_size' in signal and signal['position_size'] > 0:
            message += f"\n💰 Position Size: ₹{signal['position_size']}"
            if 'stop_loss' in signal and signal['stop_loss']:
                message += f"\n🛡️ Stop Loss: ₹{signal['stop_loss']}"
            if 'take_profit' in signal and signal['take_profit']:
                message += f"\n🎯 Take Profit: ₹{signal['take_profit']}"
        
        message += f"\n\n⏰ {signal.get('timestamp', '')}"
        
        return message


def get_quick_signal(market_data: Dict) -> str:
    try:
        integration = AIIntegration()
        signal = integration.get_ai_signal(market_data)
        return integration.format_signal_for_telegram(signal)
    except Exception as e:
        return f"Error generating signal: {str(e)}"


if __name__ == "__main__":
    import numpy as np
    
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=60)
    base_price = 25000
    
    closes = []
    for i in range(60):
        closes.append(base_price + np.random.uniform(-200, 200))
        base_price += np.random.uniform(-100, 100)
    
    market_data = {
        'open': [c + np.random.uniform(-50, 50) for c in closes],
        'high': [c + np.random.uniform(0, 100) for c in closes],
        'low': [c - np.random.uniform(0, 100) for c in closes],
        'close': closes,
        'volume': [np.random.uniform(1000000, 5000000) for _ in range(60)]
    }
    
    integration = AIIntegration()
    signal = integration.get_ai_signal(market_data)
    
    print(integration.format_signal_for_telegram(signal))
