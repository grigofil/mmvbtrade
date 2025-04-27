"""
Moving Average trading strategy implementation
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MovingAverageStrategy:
    """
    Moving Average Crossover trading strategy
    
    This strategy generates signals based on crossovers between
    a fast moving average and a slow moving average
    """
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        """
        Initialize the strategy
        
        Args:
            fast_period: Period for fast moving average (default: 10)
            slow_period: Period for slow moving average (default: 30)
        """
        if fast_period >= slow_period:
            raise ValueError("Fast period must be smaller than slow period")
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        logger.info(f"Initialized Moving Average strategy with fast_period={fast_period}, slow_period={slow_period}")
    
    def calculate_indicators(self, candles: List[Dict]) -> pd.DataFrame:
        """
        Calculate moving averages for the given candles
        
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
        
        # Sort by datetime
        df = df.sort_values('datetime')
        
        # Calculate moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
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
        df.loc[buy_condition, 'signal'] = 1
        
        # Sell signal: fast MA crosses below slow MA
        sell_condition = (df['fast_ma'] < df['slow_ma']) & (df['prev_fast'] >= df['prev_slow'])
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
        if len(candles) < self.slow_period + 1:
            logger.warning(f"Not enough candles for analysis. Need at least {self.slow_period + 1}, got {len(candles)}")
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
                'slow_ma': df.iloc[-1]['slow_ma']
            }
            
            logger.info(f"Generated {'BUY' if latest_signal == 1 else 'SELL'} signal at {metadata['price']}")
            return int(latest_signal), metadata
        
        return 0, None 