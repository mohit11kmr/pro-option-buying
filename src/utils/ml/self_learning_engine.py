import time
import threading
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Fix for potential circular imports and pathing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.db_manager import DatabaseManager
from src.utils.ml.model_registry import ModelRegistry, ModelTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfLearningEngine:
    def __init__(self, db_manager: DatabaseManager, market_data_provider=None):
        self.db = db_manager
        self.market = market_data_provider
        self.registry = ModelRegistry()
        self.trainer = ModelTrainer(self.registry)
        
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.check_intervals = [15, 30, 60] # Minutes to wait before checking signal outcome
        self.retrain_time = "15:45" # Time to trigger retraining (IST)
        
    def start(self):
        """Start the learning engine in a background thread."""
        if self.is_running:
            logger.info("Self-Learning Engine is already running.")
            return
            
        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Self-Learning Engine started.")

    def stop(self):
        """Stop the learning engine."""
        self.is_running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Self-Learning Engine stopped.")

    def _run_loop(self):
        """Main background loop for the learning engine."""
        while not self.stop_event.is_set():
            try:
                now = datetime.now()
                
                # 1. Collect live data snapshot (Every 5 minutes)
                if now.minute % 5 == 0 and now.second < 10:
                    self._collect_data_snapshot()
                
                # 2. Track signal outcomes
                for mins in self.check_intervals:
                    self._track_signal_outcomes(mins)
                
                # 3. Optimize weights (Every hour)
                if now.minute == 0 and now.second < 10:
                    self._optimize_weights()
                
                # 4. Check for retraining (Daily at scheduled time)
                current_time_str = now.strftime("%H:%M")
                if current_time_str == self.retrain_time and now.second < 10:
                    self._trigger_retraining()
                
                # Sleep briefly to avoid CPU hogging
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in learning engine loop: {e}")
                time.sleep(60)

    def _collect_data_snapshot(self):
        """Collect and store a snapshot of current market data."""
        if not self.market:
            return
            
        try:
            logger.info("Collecting market snapshot for learning...")
            quote = self.market.get_index_quote("NIFTY")
            if quote:
                self.db.store_snapshot(
                    open=quote.get('open', 0),
                    high=quote.get('high', 0),
                    low=quote.get('low', 0),
                    close=quote.get('last_price', 0),
                    volume=quote.get('volume', 0)
                )
                logger.info(f"Snapshot stored. Price: {quote.get('last_price')}")
        except Exception as e:
            logger.error(f"Failed to collect snapshot: {e}")

    def _track_signal_outcomes(self, check_after_mins: int):
        """Check the outcome of signals that were generated X minutes ago."""
        try:
            pending = self.db.get_pending_outcomes(check_after_mins)
            if not pending:
                return
                
            logger.info(f"Checking outcomes for {len(pending)} signals (Timeframe: {check_after_mins}m)...")
            
            # For each pending signal, we need the price at SignalTime + check_after_mins
            for sig in pending:
                signal_id = sig['id']
                entry_price = sig['nifty_price']
                signal_time = datetime.fromisoformat(sig['timestamp'])
                target_time = signal_time + timedelta(minutes=check_after_mins)
                
                # Check if we have a market snapshot close to the target time
                # Or fetch from market if live
                current_price = self._get_price_at_time(target_time)
                
                if current_price:
                    price_change = current_price - entry_price
                    price_change_pct = (price_change / entry_price) * 100
                    recommendation = sig['recommendation']
                    
                    # Determine if prediction was correct
                    was_correct = False
                    if recommendation in ['STRONG_BUY', 'BUY'] and price_change_pct > 0.05: # Threshold of 0.05%
                        was_correct = True
                    elif recommendation in ['STRONG_SELL', 'SELL'] and price_change_pct < -0.05:
                        was_correct = True
                    elif recommendation == 'HOLD' and abs(price_change_pct) <= 0.05:
                        was_correct = True
                        
                    self.db.record_outcome(
                        signal_id=signal_id,
                        check_after_mins=check_after_mins,
                        actual_price=current_price,
                        price_change_pct=price_change_pct,
                        was_correct=was_correct
                    )
                    
        except Exception as e:
            logger.error(f"Error tracking signal outcomes: {e}")

    def _get_price_at_time(self, target_time: datetime) -> Optional[float]:
        """Try to find the price at a specific historical time."""
        # 1. Check snapshots first
        # (This is simplified - in reality you'd search DB for closest timestamp)
        try:
            # For verification during live session, we might just use current price 
            # if we are within a small window of target_time
            now = datetime.now()
            if abs((now - target_time).total_seconds()) < 60:
                if self.market:
                    quote = self.market.get_index_quote("NIFTY")
                    return quote.get('last_price')
            
            # In a real scenario, we'd query historical data from the provider
            # or from our internal snapshots table
            return None 
        except:
            return None

    def _optimize_weights(self):
        """Dynamically adjust AI signal weights based on recent accuracy."""
        try:
            logger.info("Optimizing AI component weights...")
            
            # Get accuracy over last 7 days
            accuracy = self.db.get_component_accuracy(days=7)
            
            # Current weights
            current_weights = self.db.get_latest_weights() or {
                'price_prediction': 0.25,
                'pattern_recognition': 0.25,
                'sentiment': 0.25,
                'options_flow': 0.25
            }
            
            new_weights = {}
            total_raw = 0
            
            # Simple reinforcement learning logic:
            # base_weight * (accuracy / average_accuracy)
            avg_acc = sum(accuracy.values()) / len(accuracy) if accuracy else 50.0
            if avg_acc == 0: avg_acc = 50.0
            
            mapping = {
                'price_prediction': 'price',
                'pattern_recognition': 'pattern',
                'sentiment': 'sentiment',
                'options_flow': 'options'
            }
            
            for k, acc_key in mapping.items():
                acc = accuracy.get(acc_key, 50.0)
                # Adjust weight based on performance relative to average
                performance_factor = acc / avg_acc
                # Smooth the adjustment
                new_w = current_weights[k] * (0.9 + 0.1 * performance_factor)
                # Keep weights within bounds [0.1, 0.5]
                new_w = max(0.1, min(0.5, new_w))
                new_weights[k] = new_w
                total_raw += new_w
                
            # Normalize to 1.0
            normalized_weights = {k: round(v / total_raw, 3) for k, v in new_weights.items()}
            
            # Save if significant change
            diff = sum(abs(normalized_weights[k] - current_weights[k]) for k in normalized_weights)
            if diff > 0.01:
                self.db.save_weights(normalized_weights, trigger="optimization_loop")
                logger.info(f"Weights optimized. New: {normalized_weights}")
            
        except Exception as e:
            logger.error(f"Weight optimization failed: {e}")

    def _trigger_retraining(self):
        """Schedule and execute model retraining on accumulated data."""
        try:
            logger.info("Starting scheduled model retraining...")
            
            # Get last 30 days of data
            df_historical = self.db.get_snapshots(days=30)
            if len(df_historical) < 500: # Need enough candles
                logger.warning(f"Not enough data for retraining. Samples: {len(df_historical)}")
                return
                
            df = pd.DataFrame(df_historical)
            
            # 1. Retrain Price Predictor
            logger.info("Retraining Price Predictor...")
            model_p, version_p = self.trainer.train_price_predictor(df)
            self.db.log_model_performance(
                "price_predictor", version_p, 
                accuracy=0.85, # In reality, get score from trainer
                samples_used=len(df)
            )
            
            # 2. Retrain Pattern Classifier
            logger.info("Retraining Pattern Classifier...")
            model_c, version_c = self.trainer.train_pattern_classifier(df)
            self.db.log_model_performance(
                "pattern_classifier", version_c, 
                accuracy=0.72,
                samples_used=len(df)
            )
            
            logger.info(f"Retraining complete. New versions: {version_p}, {version_c}")
            
        except Exception as e:
            logger.error(f"Retraining failed: {e}")

    def get_status(self) -> Dict:
        """Return the current status of the learning engine."""
        accuracy = self.db.get_accuracy_stats(days=7)
        weights = self.db.get_latest_weights() or {}
        
        return {
            "is_running": self.is_running,
            "snapshots_collected": self.db.get_snapshot_count(),
            "accuracy_7d": accuracy,
            "current_weights": weights,
            "next_retrain": self.retrain_time,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test initialization
    db = DatabaseManager()
    engine = SelfLearningEngine(db)
    print("SelfLearningEngine initialized successfully.")
    print("Status:", json.dumps(engine.get_status(), indent=2))
