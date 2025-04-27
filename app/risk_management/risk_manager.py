"""
Risk management implementation for trading bot
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk manager for trading decisions
    
    Implements various risk management strategies:
    - Maximum position size
    - Stop loss
    - Take profit
    - Maximum drawdown
    - Daily loss limit
    """
    
    def __init__(self, 
                max_position_size_pct: float = 0.05,
                stop_loss_pct: float = 0.02,
                take_profit_pct: float = 0.04,
                max_drawdown_pct: float = 0.1,
                daily_loss_limit_pct: float = 0.03):
        """
        Initialize risk manager
        
        Args:
            max_position_size_pct: Maximum position size as percentage of portfolio (default: 5%)
            stop_loss_pct: Stop loss percentage per position (default: 2%)
            take_profit_pct: Take profit percentage per position (default: 4%)
            max_drawdown_pct: Maximum drawdown allowed (default: 10%)
            daily_loss_limit_pct: Maximum daily loss allowed (default: 3%)
        """
        self.max_position_size_pct = max_position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        
        # Track performance
        self.initial_portfolio_value = 0
        self.max_portfolio_value = 0
        self.daily_starting_value = 0
        self.daily_losses = 0
        self.positions = {}
        
        logger.info(f"Initialized RiskManager with max_position_size={max_position_size_pct}, "
                  f"stop_loss={stop_loss_pct}, take_profit={take_profit_pct}")
    
    def initialize_portfolio(self, portfolio_value: float):
        """
        Initialize tracking with current portfolio value
        
        Args:
            portfolio_value: Current portfolio value
        """
        self.initial_portfolio_value = portfolio_value
        self.max_portfolio_value = portfolio_value
        self.daily_starting_value = portfolio_value
        self.daily_losses = 0
        logger.info(f"Initialized portfolio tracking with value: {portfolio_value}")
    
    def reset_daily_tracking(self, portfolio_value: float):
        """
        Reset daily tracking (call at start of trading day)
        
        Args:
            portfolio_value: Current portfolio value
        """
        self.daily_starting_value = portfolio_value
        self.daily_losses = 0
        logger.info(f"Reset daily tracking with value: {portfolio_value}")
    
    def update_portfolio_value(self, portfolio_value: float):
        """
        Update portfolio value for tracking
        
        Args:
            portfolio_value: Current portfolio value
        """
        if portfolio_value > self.max_portfolio_value:
            self.max_portfolio_value = portfolio_value
        
        # Calculate daily PnL
        daily_pnl = portfolio_value - self.daily_starting_value
        if daily_pnl < 0:
            self.daily_losses = abs(daily_pnl)
        
        logger.debug(f"Updated portfolio value: {portfolio_value}, daily PnL: {daily_pnl}")
    
    def calculate_position_size(self, portfolio_value: float, instrument_price: float) -> int:
        """
        Calculate the maximum position size for a trade
        
        Args:
            portfolio_value: Current portfolio value
            instrument_price: Current price of the instrument
            
        Returns:
            Maximum quantity to trade
        """
        max_position_value = portfolio_value * self.max_position_size_pct
        max_quantity = int(max_position_value / instrument_price)
        
        logger.info(f"Calculated max position: {max_quantity} units at {instrument_price} per unit")
        return max_quantity
    
    def register_position(self, position_id: str, entry_price: float, quantity: int, direction: str):
        """
        Register a new position for risk management
        
        Args:
            position_id: Unique ID for the position
            entry_price: Entry price
            quantity: Quantity
            direction: "long" or "short"
        """
        stop_loss = entry_price * (1 - self.stop_loss_pct) if direction == "long" else entry_price * (1 + self.stop_loss_pct)
        take_profit = entry_price * (1 + self.take_profit_pct) if direction == "long" else entry_price * (1 - self.take_profit_pct)
        
        self.positions[position_id] = {
            "entry_price": entry_price,
            "quantity": quantity,
            "direction": direction,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "created_at": datetime.now()
        }
        
        logger.info(f"Registered position {position_id}: {direction}, {quantity} units at {entry_price}, "
                  f"SL: {stop_loss}, TP: {take_profit}")
    
    def should_close_position(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """
        Check if a position should be closed based on risk management rules
        
        Args:
            position_id: Position ID
            current_price: Current price
            
        Returns:
            Dict with decision and reason
        """
        if position_id not in self.positions:
            return {"close": False, "reason": "Position not found"}
        
        position = self.positions[position_id]
        
        # Check stop loss
        if position["direction"] == "long" and current_price <= position["stop_loss"]:
            return {"close": True, "reason": "Stop loss triggered"}
        
        if position["direction"] == "short" and current_price >= position["stop_loss"]:
            return {"close": True, "reason": "Stop loss triggered"}
        
        # Check take profit
        if position["direction"] == "long" and current_price >= position["take_profit"]:
            return {"close": True, "reason": "Take profit triggered"}
        
        if position["direction"] == "short" and current_price <= position["take_profit"]:
            return {"close": True, "reason": "Take profit triggered"}
        
        return {"close": False, "reason": "Within risk parameters"}
    
    def can_open_position(self, portfolio_value: float) -> Dict[str, Any]:
        """
        Check if new positions can be opened based on risk limits
        
        Args:
            portfolio_value: Current portfolio value
            
        Returns:
            Dict with decision and reason
        """
        # Check drawdown limit
        current_drawdown = (self.max_portfolio_value - portfolio_value) / self.max_portfolio_value
        if current_drawdown >= self.max_drawdown_pct:
            return {
                "allowed": False, 
                "reason": f"Max drawdown exceeded: {current_drawdown:.2%} >= {self.max_drawdown_pct:.2%}"
            }
        
        # Check daily loss limit
        daily_loss_pct = self.daily_losses / self.daily_starting_value
        if daily_loss_pct >= self.daily_loss_limit_pct:
            return {
                "allowed": False, 
                "reason": f"Daily loss limit exceeded: {daily_loss_pct:.2%} >= {self.daily_loss_limit_pct:.2%}"
            }
        
        return {"allowed": True, "reason": "Within risk limits"} 