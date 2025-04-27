"""
Base class for trading strategies
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from app.risk_management import RiskManager

logger = logging.getLogger(__name__)

class Strategy(ABC):
    """
    Base abstract class for all trading strategies
    
    All strategy implementations should inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, name: str, description: str, risk_manager: Optional[RiskManager] = None):
        """
        Initialize strategy with basic information
        
        Args:
            name: Strategy name
            description: Strategy description
            risk_manager: RiskManager instance for risk control (optional)
        """
        self.name = name
        self.description = description
        self.risk_manager = risk_manager or RiskManager()  # Use default risk manager if none provided
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
            "recommended_timeframe": self.get_recommended_timeframe(),
            "risk_management": {
                "stop_loss_pct": self.risk_manager.stop_loss_pct,
                "take_profit_pct": self.risk_manager.take_profit_pct,
                "max_position_size_pct": self.risk_manager.max_position_size_pct,
                "max_drawdown_pct": self.risk_manager.max_drawdown_pct,
                "daily_loss_limit_pct": self.risk_manager.daily_loss_limit_pct
            }
        }
        
    def check_risk_before_trade(self, portfolio_value: float, instrument_price: float, 
                               direction: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check risk management rules before placing a trade
        
        Args:
            portfolio_value: Current portfolio value
            instrument_price: Current price of the instrument
            direction: Trade direction ("long" or "short")
            
        Returns:
            Tuple of (allowed, details) where:
            - allowed: True if trade is allowed, False otherwise
            - details: Dictionary with details about the decision
        """
        # Check if new positions can be opened
        can_open = self.risk_manager.can_open_position(portfolio_value)
        if not can_open["allowed"]:
            return False, can_open
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(portfolio_value, instrument_price)
        
        return True, {
            "allowed": True,
            "max_position_size": position_size,
            "reason": "Trade allowed within risk parameters"
        }
        
    def check_stop_loss_take_profit(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """
        Check if position should be closed based on stop loss or take profit
        
        Args:
            position_id: Position identifier
            current_price: Current price of the instrument
            
        Returns:
            Dictionary with decision and reason
        """
        return self.risk_manager.should_close_position(position_id, current_price) 