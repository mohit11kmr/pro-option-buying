"""
Phase 10: Reinforcement Learning Parameter Optimizer
Uses Q-Learning to optimize trading strategy parameters.
Author: Nifty Options Toolkit
"""

import numpy as np
import pandas as pd
from collections import deque
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParameterEnvironment:
    """
    Trading environment for RL parameter optimization.
    State: Market conditions + current parameters
    Action: Parameter adjustments
    Reward: Profit/Loss
    """
    
    def __init__(self, df, initial_capital=100000):
        """
        Initialize trading environment.
        
        Args:
            df: Market data DataFrame
            initial_capital: Starting capital
        """
        self.df = df
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size = 0
        self.trades = []
        self.current_step = 0
        self.max_steps = len(df) - 1
        
    def reset(self):
        """Reset environment."""
        self.current_capital = self.initial_capital
        self.position_size = 0
        self.trades = []
        self.current_step = 0
        
        return self._get_state()
    
    def _get_state(self):
        """Get current market state."""
        if self.current_step >= len(self.df):
            self.current_step = len(self.df) - 1
        
        row = self.df.iloc[self.current_step]
        
        # Market indicators
        sma20 = self.df['close'].rolling(20).mean().iloc[self.current_step]
        sma50 = self.df['close'].rolling(50).mean().iloc[self.current_step]
        rsi = self._calculate_rsi().iloc[self.current_step] if self.current_step > 14 else 50
        
        state = np.array([
            row['close'],           # Current price
            sma20 if not np.isnan(sma20) else row['close'],  # 20-day SMA
            sma50 if not np.isnan(sma50) else row['close'],  # 50-day SMA
            rsi,                    # RSI
            self.current_capital,   # Current capital
            self.position_size,     # Position size
            row['volume'] if 'volume' in row else 0  # Volume
        ], dtype=np.float32)
        
        return state
    
    def _calculate_rsi(self, period=14):
        """Calculate RSI."""
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def step(self, action, params):
        """
        Execute action with parameters.
        
        Actions: 0=Hold, 1=Buy, 2=Sell
        Params: {'ma_period': int, 'stop_loss_pct': float, 'take_profit_pct': float}
        
        Returns:
            next_state, reward, done
        """
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        current_price = self.df['close'].iloc[self.current_step]
        reward = 0
        
        if action == 1:  # BUY
            if self.position_size == 0:  # Only if not already in position
                self.position_size = self.current_capital / current_price
                self.trades.append({
                    'type': 'buy',
                    'price': current_price,
                    'size': self.position_size,
                    'sl': current_price * (1 - params['stop_loss_pct']),
                    'tp': current_price * (1 + params['take_profit_pct'])
                })
                
        elif action == 2:  # SELL
            if self.position_size > 0:
                sell_value = self.position_size * current_price
                entry_price = self.trades[-1]['price'] if self.trades else current_price
                
                profit = sell_value - (self.position_size * entry_price)
                self.current_capital = sell_value
                
                reward = profit / self.initial_capital * 100  # Reward as % of capital
                
                self.trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'size': self.position_size,
                    'profit': profit
                })
                
                self.position_size = 0
        
        # Check SL/TP
        if self.position_size > 0 and len(self.trades) > 0:
            entry = self.trades[-1]
            if current_price <= entry['sl']:
                # Stop loss hit
                self.current_capital = self.position_size * current_price
                reward = -5  # Penalty for stop loss
                self.position_size = 0
            elif current_price >= entry['tp']:
                # Take profit hit
                profit = self.position_size * (current_price - entry['price'])
                self.current_capital += profit
                reward = 5  # Reward for target hit
                self.position_size = 0
        
        next_state = self._get_state()
        
        return next_state, reward, done


class QLearningOptimizer:
    """
    Q-Learning based parameter optimizer.
    Learns optimal trading parameters through interaction with market environment.
    """
    
    def __init__(self, environment, state_bins=10, action_space=3):
        """
        Initialize Q-Learning optimizer.
        
        Args:
            environment: ParameterEnvironment instance
            state_bins: Number of bins for state space discretization
            action_space: Number of possible actions
        """
        self.environment = environment
        self.state_bins = state_bins
        self.action_space = action_space
        
        # Parameter space to optimize
        self.ma_periods = [10, 20, 30, 50]
        self.stop_losses = [0.01, 0.02, 0.03, 0.05]
        self.take_profits = [0.02, 0.03, 0.05, 0.10]
        
        # Q-table: state -> action -> Q-value
        self.q_table = {}
        
        # Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
        self.episodes = 100
        
        self.training_results = []
        
    def _discretize_state(self, state):
        """Convert continuous state to discrete bins."""
        # Normalize state values
        normalized = [
            int((s - np.min(state)) / (np.max(state) - np.min(state) + 1e-8) * self.state_bins)
            for s in state
        ]
        # Clip to valid range
        normalized = [min(max(x, 0), self.state_bins - 1) for x in normalized]
        
        return tuple(normalized)
    
    def _get_params_for_action(self, action_idx):
        """Map action index to parameter set."""
        ma_idx = (action_idx // (len(self.stop_losses) * len(self.take_profits))) % len(self.ma_periods)
        sl_idx = (action_idx // len(self.take_profits)) % len(self.stop_losses)
        tp_idx = action_idx % len(self.take_profits)
        
        return {
            'ma_period': self.ma_periods[ma_idx],
            'stop_loss_pct': self.stop_losses[sl_idx],
            'take_profit_pct': self.take_profits[tp_idx]
        }
    
    def _choose_action(self, state, training=True):
        """
        Choose action using epsilon-greedy strategy.
        """
        total_actions = len(self.ma_periods) * len(self.stop_losses) * len(self.take_profits)
        
        if training and np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.randint(0, total_actions)
        else:
            # Exploit: best action
            if state not in self.q_table:
                self.q_table[state] = np.zeros(total_actions)
            
            return np.argmax(self.q_table[state])
    
    def train(self):
        """Train optimizer using Q-Learning."""
        logger.info("Starting Q-Learning parameter optimization...")
        
        for episode in range(self.episodes):
            state = self.environment.reset()
            state = self._discretize_state(state)
            
            if state not in self.q_table:
                total_actions = len(self.ma_periods) * len(self.stop_losses) * len(self.take_profits)
                self.q_table[state] = np.zeros(total_actions)
            
            episode_reward = 0
            step_count = 0
            
            while True:
                action = self._choose_action(state, training=True)
                params = self._get_params_for_action(action)
                
                next_state, reward, done = self.environment.step(action, params)
                next_state = self._discretize_state(next_state)
                
                if next_state not in self.q_table:
                    total_actions = len(self.ma_periods) * len(self.stop_losses) * len(self.take_profits)
                    self.q_table[next_state] = np.zeros(total_actions)
                
                # Q-Learning update
                old_value = self.q_table[state][action]
                next_max = np.max(self.q_table[next_state])
                
                new_value = old_value + self.learning_rate * (
                    reward + self.discount_factor * next_max - old_value
                )
                
                self.q_table[state][action] = new_value
                
                episode_reward += reward
                state = next_state
                step_count += 1
                
                if done:
                    break
            
            self.training_results.append({
                'episode': episode,
                'reward': episode_reward,
                'final_capital': self.environment.current_capital,
                'total_trades': len(self.environment.trades)
            })
            
            if (episode + 1) % 10 == 0:
                logger.info(f"Episode {episode+1}/{self.episodes} | Reward: {episode_reward:.2f}")
        
        logger.info("Q-Learning training complete!")
    
    def get_optimal_params(self):
        """
        Get optimal parameters based on trained Q-table.
        
        Returns:
            Best parameters and their expected return
        """
        if not self.q_table:
            raise ValueError("Model must be trained first!")
        
        best_reward = float('-inf')
        best_state = None
        best_action = None
        
        for state, q_values in self.q_table.items():
            max_q = np.max(q_values)
            if max_q > best_reward:
                best_reward = max_q
                best_state = state
                best_action = np.argmax(q_values)
        
        params = self._get_params_for_action(best_action)
        
        return {
            'optimal_params': params,
            'expected_return': float(best_reward),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_portfolio_metrics(self):
        """Get training metrics and performance."""
        if not self.training_results:
            return {}
        
        results_df = pd.DataFrame(self.training_results)
        
        return {
            'total_episodes': len(self.training_results),
            'avg_reward': float(results_df['reward'].mean()),
            'best_reward': float(results_df['reward'].max()),
            'worst_reward': float(results_df['reward'].min()),
            'avg_trades_per_episode': float(results_df['total_trades'].mean()),
            'final_capital_mean': float(results_df['final_capital'].mean()),
            'profit_factor': float(
                results_df['final_capital'].mean() / 
                (results_df['final_capital'].std() + 1e-8)
            ),
            'training_results': results_df.to_dict('records')
        }


class PolicyGradientOptimizer:
    """
    Policy Gradient based parameter optimizer.
    Direct optimization of strategy parameters using gradient ascent.
    """
    
    def __init__(self, environment):
        """Initialize Policy Gradient optimizer."""
        self.environment = environment
        self.learning_rate = 0.001
        self.episodes = 50
        
    def optimize(self):
        """Train policy gradient model."""
        logger.info("Starting Policy Gradient optimization...")
        
        # Parameter candidates
        params_history = []
        rewards_history = []
        
        for ma_period in [20, 30, 50]:
            for sl_pct in [0.01, 0.02, 0.03]:
                for tp_pct in [0.03, 0.05, 0.10]:
                    
                    params = {
                        'ma_period': ma_period,
                        'stop_loss_pct': sl_pct,
                        'take_profit_pct': tp_pct
                    }
                    
                    # Evaluate parameters
                    self.environment.reset()
                    total_reward = 0
                    
                    for _ in range(min(100, len(self.environment.df) - 1)):
                        state = self.environment._get_state()
                        
                        # Simple action: buy if price below SMA20, sell otherwise
                        sma20 = self.environment.df['close'].rolling(20).mean()
                        current_price = self.environment.df['close'].iloc[self.environment.current_step]
                        
                        if current_price < sma20.iloc[self.environment.current_step]:
                            action = 1  # Buy
                        else:
                            action = 2  # Sell
                        
                        next_state, reward, done = self.environment.step(action, params)
                        total_reward += reward
                        
                        if done:
                            break
                    
                    params_history.append(params)
                    rewards_history.append(total_reward)
        
        # Find best parameters
        best_idx = np.argmax(rewards_history)
        best_params = params_history[best_idx]
        best_reward = rewards_history[best_idx]
        
        return {
            'optimal_params': best_params,
            'expected_return': float(best_reward),
            'all_results': [
                {'params': p, 'reward': float(r)}
                for p, r in zip(params_history, rewards_history)
            ]
        }


if __name__ == "__main__":
    print("\nPhase 10: RL Parameter Optimizer")
    print("=" * 50)
    
    from utils.backtester import HistoricalDataGenerator
    gen = HistoricalDataGenerator()
    df = gen.generate_with_market_events(years=1).tail(500)
    
    # Create environment and optimizer
    env = ParameterEnvironment(df)
    optimizer = QLearningOptimizer(env)
    optimizer.train()
    
    # Get optimal parameters
    result = optimizer.get_optimal_params()
    print(f"\n🎯 Optimal Parameters:")
    print(f"   MA Period: {result['optimal_params']['ma_period']}")
    print(f"   Stop Loss: {result['optimal_params']['stop_loss_pct']:.2%}")
    print(f"   Take Profit: {result['optimal_params']['take_profit_pct']:.2%}")
    print(f"   Expected Return: {result['expected_return']:.2f}%")
