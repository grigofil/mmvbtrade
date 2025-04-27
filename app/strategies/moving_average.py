"""
Moving Average trading strategy implementation
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

from app.strategies.base import Strategy

logger = logging.getLogger(__name__)

class MovingAverageStrategy(Strategy):
    """
    Moving Average Crossover trading strategy
    
    This strategy generates signals based on crossovers between
    a fast moving average and a slow moving average
    """
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30, 
                signal_threshold: float = 0.0, overbought_level: float = 70.0,
                oversold_level: float = 30.0):
        """
        Initialize the strategy
        
        Args:
            fast_period: Period for fast moving average (default: 10)
            slow_period: Period for slow moving average (default: 30)
            signal_threshold: Minimum difference between fast and slow MA to generate a signal (%)
            overbought_level: Level to consider market overbought (for RSI filter)
            oversold_level: Level to consider market oversold (for RSI filter)
        """
        super().__init__(
            name="Moving Average Crossover",
            description="Generates signals based on crossovers between fast and slow moving averages"
        )
        
        if fast_period >= slow_period:
            raise ValueError("Fast period must be smaller than slow period")
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_threshold = signal_threshold
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        
        logger.info(f"Initialized Moving Average strategy with fast_period={fast_period}, slow_period={slow_period}")
    
    def calculate_indicators(self, candles: List[Dict]) -> pd.DataFrame:
        """
        Calculate moving averages and additional indicators for the given candles
        
        Args:
            candles: List of candle data from broker API
            
        Returns:
            DataFrame with prices and indicators
        """
        # Convert candles to DataFrame
        df = pd.DataFrame(candles)
        
        # Extract datetime and closing prices
        # Note: Adjust these field names based on the actual API response format
        df['datetime'] = pd.to_datetime(df['time'])
        df['close'] = df['c'].astype(float)
        df['open'] = df['o'].astype(float)
        df['high'] = df['h'].astype(float)
        df['low'] = df['l'].astype(float)
        df['volume'] = df['v'].astype(float)
        
        # Sort by datetime
        df = df.sort_values('datetime')
        
        # Calculate moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
        # Calculate MA difference in percentage
        df['ma_diff_pct'] = ((df['fast_ma'] - df['slow_ma']) / df['slow_ma']) * 100
        
        # Calculate RSI for additional filtering
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].apply(lambda x: max(x, 0))
        df['loss'] = df['price_change'].apply(lambda x: abs(min(x, 0)))
        
        # Calculate average gain and loss over the past 14 periods
        avg_gain = df['gain'].rolling(window=14).mean()
        avg_loss = df['loss'].rolling(window=14).mean()
        
        # Calculate RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Calculate Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        # Calculate trend strength
        df['trend_strength'] = abs(df['ma_diff_pct'])
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on moving average crossovers
        
        Args:
            df: DataFrame with price data and moving averages
            
        Returns:
            DataFrame with signal column added
        """
        # Initialize signal column
        df['signal'] = 0
        
        # Generate crossover signals
        # 1 for buy (fast MA crosses above slow MA)
        # -1 for sell (fast MA crosses below slow MA)
        df['prev_fast'] = df['fast_ma'].shift(1)
        df['prev_slow'] = df['slow_ma'].shift(1)
        
        # Buy signal: fast MA crosses above slow MA
        buy_condition = (df['fast_ma'] > df['slow_ma']) & (df['prev_fast'] <= df['prev_slow'])
        
        # Add threshold filter
        if self.signal_threshold > 0:
            buy_condition = buy_condition & (df['ma_diff_pct'] > self.signal_threshold)
        
        # Add RSI oversold filter for buy signals (optional)
        buy_condition = buy_condition & (df['rsi'] < self.overbought_level)
        
        df.loc[buy_condition, 'signal'] = 1
        
        # Sell signal: fast MA crosses below slow MA
        sell_condition = (df['fast_ma'] < df['slow_ma']) & (df['prev_fast'] >= df['prev_slow'])
        
        # Add threshold filter
        if self.signal_threshold > 0:
            sell_condition = sell_condition & (df['ma_diff_pct'] < -self.signal_threshold)
        
        # Add RSI overbought filter for sell signals (optional)
        sell_condition = sell_condition & (df['rsi'] > self.oversold_level)
        
        df.loc[sell_condition, 'signal'] = -1
        
        return df
    
    def analyze(self, candles: List[Dict]) -> Tuple[int, Optional[Dict]]:
        """
        Analyze candle data and generate trading signal
        
        Args:
            candles: List of candle data from broker API
            
        Returns:
            Tuple of (signal, metadata) where:
            - signal: 1 for buy, -1 for sell, 0 for no action
            - metadata: Dictionary with additional signal information or None
        """
        if len(candles) < self.get_required_candles_count():
            logger.warning(f"Not enough candles for analysis. Need at least {self.get_required_candles_count()}, got {len(candles)}")
            return 0, None
        
        # Calculate indicators
        df = self.calculate_indicators(candles)
        
        # Generate signals
        df = self.generate_signals(df)
        
        # Get the latest signal
        latest_signal = df.iloc[-1]['signal']
        
        if latest_signal != 0:
            # Return signal with metadata
            metadata = {
                'timestamp': df.iloc[-1]['datetime'].isoformat(),
                'price': df.iloc[-1]['close'],
                'fast_ma': df.iloc[-1]['fast_ma'],
                'slow_ma': df.iloc[-1]['slow_ma'],
                'ma_diff_pct': df.iloc[-1]['ma_diff_pct'],
                'rsi': df.iloc[-1]['rsi'],
                'macd': df.iloc[-1]['macd'],
                'macd_signal': df.iloc[-1]['macd_signal'],
                'bb_upper': df.iloc[-1]['bb_upper'],
                'bb_middle': df.iloc[-1]['bb_middle'],
                'bb_lower': df.iloc[-1]['bb_lower'],
                'trend_strength': df.iloc[-1]['trend_strength']
            }
            
            logger.info(f"Generated {'BUY' if latest_signal == 1 else 'SELL'} signal at {metadata['price']}")
            return int(latest_signal), metadata
        
        return 0, None
    
    def get_required_candles_count(self) -> int:
        """
        Get the minimum number of candles required for this strategy
        
        Returns:
            Minimum number of candles required
        """
        # Need enough candles for the slow moving average calculation
        # plus a few more for the indicators to stabilize
        return self.slow_period + 30
    
    def get_recommended_timeframe(self) -> str:
        """
        Get the recommended timeframe for this strategy
        
        Returns:
            Recommended timeframe (e.g., "1m", "5m", "1h", "1d")
        """
        if self.slow_period <= 20:
            return "1h"
        elif self.slow_period <= 50:
            return "4h"
        else:
            return "1d"
    
    def get_strategy_info(self) -> Dict:
        """
        Get strategy information and current parameters
        
        Returns:
            Dictionary with strategy information
        """
        info = super().get_strategy_info()
        info.update({
            "parameters": {
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "signal_threshold": self.signal_threshold,
                "overbought_level": self.overbought_level,
                "oversold_level": self.oversold_level
            }
        })
        return info
    
    def optimize(self, candles: List[Dict], target_metric: str = "profit") -> Dict:
        """
        Optimize strategy parameters based on historical data
        
        Args:
            candles: List of historical candle data
            target_metric: Metric to optimize for ("profit", "sharpe", "drawdown")
            
        Returns:
            Dictionary with optimized parameters
        """
        logger.info("Starting strategy optimization...")
        
        # Define parameter ranges to test
        fast_periods = range(5, 21, 5)
        slow_periods = range(20, 51, 10)
        
        best_params = {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "profit": 0
        }
        
        # Simple brute force optimization
        for fast in fast_periods:
            for slow in slow_periods:
                if fast >= slow:
                    continue
                    
                # Create temporary strategy with these parameters
                temp_strategy = MovingAverageStrategy(fast_period=fast, slow_period=slow)
                
                # Backtest the strategy
                profit = self._backtest_strategy(temp_strategy, candles)
                
                if profit > best_params["profit"]:
                    best_params["fast_period"] = fast
                    best_params["slow_period"] = slow
                    best_params["profit"] = profit
        
        logger.info(f"Optimization complete. Best parameters: Fast MA: {best_params['fast_period']}, "
                  f"Slow MA: {best_params['slow_period']}, Profit: {best_params['profit']:.2f}%")
        
        # Update strategy parameters
        self.fast_period = best_params["fast_period"]
        self.slow_period = best_params["slow_period"]
        
        return best_params
    
    def _backtest_strategy(self, strategy: 'MovingAverageStrategy', candles: List[Dict]) -> float:
        """
        Simple backtest implementation to evaluate strategy performance
        
        Args:
            strategy: Strategy instance to test
            candles: Historical candle data
            
        Returns:
            Profit percentage
        """
        initial_balance = 10000
        balance = initial_balance
        position = 0
        entry_price = 0
        
        for i in range(strategy.get_required_candles_count(), len(candles)):
            # Get candles up to this point
            historical_candles = candles[:i]
            
            # Get signal
            signal, _ = strategy.analyze(historical_candles)
            
            current_price = candles[i]["c"]
            
            # Execute trade based on signal
            if signal == 1 and position == 0:  # Buy signal
                position = balance / current_price
                entry_price = current_price
                balance = 0
            elif signal == -1 and position > 0:  # Sell signal
                balance = position * current_price
                position = 0
        
        # Close any open position at the end
        if position > 0:
            balance = position * candles[-1]["c"]
        
        # Calculate profit
        profit_pct = (balance / initial_balance - 1) * 100
        
        return profit_pct 