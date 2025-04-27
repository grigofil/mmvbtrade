"""
Base class for trading strategies
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Strategy(ABC):
    """
    Base abstract class for all trading strategies
    
    All strategy implementations should inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize strategy with basic information
        
        Args:
            name: Strategy name
            description: Strategy description
        """
        self.name = name
        self.description = description
        logger.info(f"Initialized strategy: {name}")
    
    @abstractmethod
    def analyze(self, candles: List[Dict]) -> Tuple[int, Optional[Dict]]:
        """
        Analyze price data and generate trading signals
        
        Args:
            candles: List of candle data from broker API
            
        Returns:
            Tuple of (signal, metadata) where:
            - signal: 1 for buy, -1 for sell, 0 for no action
            - metadata: Dictionary with additional signal information or None
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        Validate strategy parameters
        
        Returns:
            True if parameters are valid, False otherwise
        """
        return True
    
    def get_required_candles_count(self) -> int:
        """
        Get the minimum number of candles required for this strategy
        
        Returns:
            Minimum number of candles required
        """
        return 50  # Default value, should be overridden by specific strategies
    
    def get_recommended_timeframe(self) -> str:
        """
        Get the recommended timeframe for this strategy
        
        Returns:
            Recommended timeframe (e.g., "1m", "5m", "1h", "1d")
        """
        return "1d"  # Default value, should be overridden by specific strategies
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and current parameters
        
        Returns:
            Dictionary with strategy information
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_candles": self.get_required_candles_count(),
            "recommended_timeframe": self.get_recommended_timeframe()
        } 