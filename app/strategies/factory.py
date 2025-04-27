"""
Strategy factory for creating and managing trading strategies
"""
import logging
from typing import Dict, List, Optional, Any, Type

from app.strategies.base import Strategy
from app.strategies.moving_average import MovingAverageStrategy
from app.strategies.mean_reversion import MeanReversionStrategy

logger = logging.getLogger(__name__)

class StrategyFactory:
    """
    Factory for creating and managing trading strategy instances
    """
    
    # Registry of available strategies
    STRATEGY_REGISTRY = {
        "moving_average": MovingAverageStrategy,
        "mean_reversion": MeanReversionStrategy
    }
    
    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, str]]:
        """
        Get list of available strategies
        
        Returns:
            List of dictionaries with strategy information
        """
        strategies = []
        for strategy_id, strategy_class in cls.STRATEGY_REGISTRY.items():
            strategies.append({
                "id": strategy_id,
                "name": strategy_class.__name__,
                "description": strategy_class.__doc__.strip().split('\n')[0] if strategy_class.__doc__ else ""
            })
        return strategies
    
    @classmethod
    def create_strategy(cls, strategy_id: str, **kwargs) -> Optional[Strategy]:
        """
        Create a strategy instance by ID
        
        Args:
            strategy_id: Strategy identifier
            **kwargs: Strategy parameters
            
        Returns:
            Strategy instance or None if strategy_id is not found
        """
        if strategy_id not in cls.STRATEGY_REGISTRY:
            logger.error(f"Unknown strategy ID: {strategy_id}")
            return None
        
        strategy_class = cls.STRATEGY_REGISTRY[strategy_id]
        
        try:
            strategy = strategy_class(**kwargs)
            logger.info(f"Created strategy: {strategy_id} with parameters: {kwargs}")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_id}: {e}")
            return None
    
    @classmethod
    def register_strategy(cls, strategy_id: str, strategy_class: Type[Strategy]) -> bool:
        """
        Register a new strategy class
        
        Args:
            strategy_id: Strategy identifier
            strategy_class: Strategy class (must be a subclass of Strategy)
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not issubclass(strategy_class, Strategy):
            logger.error(f"Cannot register {strategy_class.__name__}: not a subclass of Strategy")
            return False
        
        if strategy_id in cls.STRATEGY_REGISTRY:
            logger.warning(f"Overriding existing strategy for ID: {strategy_id}")
        
        cls.STRATEGY_REGISTRY[strategy_id] = strategy_class
        logger.info(f"Registered strategy: {strategy_id} -> {strategy_class.__name__}")
        return True
    
    @classmethod
    def get_strategy_parameters(cls, strategy_id: str) -> Dict[str, Any]:
        """
        Get parameter information for a strategy
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Dictionary with parameter information
        """
        if strategy_id not in cls.STRATEGY_REGISTRY:
            logger.error(f"Unknown strategy ID: {strategy_id}")
            return {}
        
        strategy_class = cls.STRATEGY_REGISTRY[strategy_id]
        
        # Initialize with default parameters
        default_instance = strategy_class()
        
        # Get parameters from get_strategy_info()
        strategy_info = default_instance.get_strategy_info()
        parameters = strategy_info.get("parameters", {})
        
        return parameters 