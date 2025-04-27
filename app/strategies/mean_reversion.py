"""
Mean Reversion trading strategy implementation
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

from app.strategies.base import Strategy

logger = logging.getLogger(__name__)

class MeanReversionStrategy(Strategy):
    """
    Mean Reversion trading strategy
    
    This strategy generates signals based on price deviations from a moving average,
    using RSI and Bollinger Bands to identify overbought and oversold conditions
    """
    
    def __init__(self, lookback_period: int = 20, std_dev: float = 2.0, 
                rsi_period: int = 14, oversold_threshold: float = 30.0, 
                overbought_threshold: float = 70.0):
        """
        Initialize the strategy
        
        Args:
            lookback_period: Period for the moving average (default: 20)
            std_dev: Number of standard deviations for Bollinger Bands (default: 2.0)
            rsi_period: Period for RSI calculation (default: 14)
            oversold_threshold: RSI threshold to consider market oversold (default: 30)
            overbought_threshold: RSI threshold to consider market overbought (default: 70)
        """
        super().__init__(
            name="Mean Reversion",
            description="Generates signals based on price deviations from moving average"
        )
        
        self.lookback_period = lookback_period
        self.std_dev = std_dev
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        
        logger.info(f"Initialized Mean Reversion strategy with lookback_period={lookback_period}, "
                  f"std_dev={std_dev}, rsi_period={rsi_period}")
    
    def calculate_indicators(self, candles: List[Dict]) -> pd.DataFrame:
        """
        Calculate indicators for the given candles
        
        Args:
            candles: List of candle data from broker API
            
        Returns:
            DataFrame with prices and indicators
        """
        # Convert candles to DataFrame
        df = pd.DataFrame(candles)
        
        # Extract datetime and closing prices
        df['datetime'] = pd.to_datetime(df['time'])
        df['close'] = df['c'].astype(float)
        df['open'] = df['o'].astype(float)
        df['high'] = df['h'].astype(float)
        df['low'] = df['l'].astype(float)
        df['volume'] = df['v'].astype(float)
        
        # Sort by datetime
        df = df.sort_values('datetime')
        
        # Calculate moving average
        df['ma'] = df['close'].rolling(window=self.lookback_period).mean()
        
        # Calculate Bollinger Bands
        df['std'] = df['close'].rolling(window=self.lookback_period).std()
        df['upper_band'] = df['ma'] + self.std_dev * df['std']
        df['lower_band'] = df['ma'] - self.std_dev * df['std']
        
        # Calculate BB width and %B
        df['bb_width'] = (df['upper_band'] - df['lower_band']) / df['ma']
        df['percent_b'] = (df['close'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])
        
        # Calculate RSI
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].apply(lambda x: max(x, 0))
        df['loss'] = df['price_change'].apply(lambda x: abs(min(x, 0)))
        
        avg_gain = df['gain'].rolling(window=self.rsi_period).mean()
        avg_loss = df['loss'].rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate distance from mean (z-score)
        df['z_score'] = (df['close'] - df['ma']) / df['std']
        
        # Calculate rate of change
        df['roc'] = df['close'].pct_change(periods=self.lookback_period) * 100
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on mean reversion principles
        
        Args:
            df: DataFrame with price data and indicators
            
        Returns:
            DataFrame with signal column added
        """
        # Initialize signal column
        df['signal'] = 0
        
        # Generate mean reversion signals
        # 1 for buy (price is below lower band and RSI is oversold)
        # -1 for sell (price is above upper band and RSI is overbought)
        
        # Buy signal: price below lower band and RSI oversold
        buy_condition = (df['close'] < df['lower_band']) & (df['rsi'] < self.oversold_threshold)
        df.loc[buy_condition, 'signal'] = 1
        
        # Sell signal: price above upper band and RSI overbought
        sell_condition = (df['close'] > df['upper_band']) & (df['rsi'] > self.overbought_threshold)
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
                'ma': df.iloc[-1]['ma'],
                'upper_band': df.iloc[-1]['upper_band'],
                'lower_band': df.iloc[-1]['lower_band'],
                'rsi': df.iloc[-1]['rsi'],
                'z_score': df.iloc[-1]['z_score'],
                'percent_b': df.iloc[-1]['percent_b'],
                'bb_width': df.iloc[-1]['bb_width']
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
        # Need enough candles for the lookback period plus some extra
        # to calculate indicators properly
        return max(self.lookback_period, self.rsi_period) + 10
    
    def get_recommended_timeframe(self) -> str:
        """
        Get the recommended timeframe for this strategy
        
        Returns:
            Recommended timeframe (e.g., "1m", "5m", "1h", "1d")
        """
        # Mean reversion works better on shorter timeframes
        if self.lookback_period <= 10:
            return "30m"
        elif self.lookback_period <= 20:
            return "1h"
        else:
            return "4h"
    
    def get_strategy_info(self) -> Dict:
        """
        Get strategy information and current parameters
        
        Returns:
            Dictionary with strategy information
        """
        info = super().get_strategy_info()
        info.update({
            "parameters": {
                "lookback_period": self.lookback_period,
                "std_dev": self.std_dev,
                "rsi_period": self.rsi_period,
                "oversold_threshold": self.oversold_threshold,
                "overbought_threshold": self.overbought_threshold
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
        lookback_periods = [10, 20, 30]
        std_devs = [1.5, 2.0, 2.5]
        rsi_thresholds = [(20, 80), (25, 75), (30, 70)]
        
        best_params = {
            "lookback_period": self.lookback_period,
            "std_dev": self.std_dev,
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
            "profit": 0
        }
        
        # Simple brute force optimization
        for lookback in lookback_periods:
            for std in std_devs:
                for oversold, overbought in rsi_thresholds:
                    # Create temporary strategy with these parameters
                    temp_strategy = MeanReversionStrategy(
                        lookback_period=lookback,
                        std_dev=std,
                        oversold_threshold=oversold,
                        overbought_threshold=overbought
                    )
                    
                    # Backtest the strategy
                    profit = self._backtest_strategy(temp_strategy, candles)
                    
                    if profit > best_params["profit"]:
                        best_params["lookback_period"] = lookback
                        best_params["std_dev"] = std
                        best_params["oversold_threshold"] = oversold
                        best_params["overbought_threshold"] = overbought
                        best_params["profit"] = profit
        
        logger.info(f"Optimization complete. Best parameters: Lookback: {best_params['lookback_period']}, "
                  f"StdDev: {best_params['std_dev']}, RSI Thresholds: ({best_params['oversold_threshold']}, "
                  f"{best_params['overbought_threshold']}), Profit: {best_params['profit']:.2f}%")
        
        # Update strategy parameters
        self.lookback_period = best_params["lookback_period"]
        self.std_dev = best_params["std_dev"]
        self.oversold_threshold = best_params["oversold_threshold"]
        self.overbought_threshold = best_params["overbought_threshold"]
        
        return best_params
    
    def _backtest_strategy(self, strategy: 'MeanReversionStrategy', candles: List[Dict]) -> float:
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