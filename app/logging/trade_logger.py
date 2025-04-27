"""
Trade logger for recording trading activities
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TradeLogger:
    """
    Logger for trading activities
    
    Records trades, signals, and portfolio changes to a log file
    and provides methods to analyze trading history
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize trade logger
        
        Args:
            log_dir: Directory to store log files (default: "logs")
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create log files
        self.trade_log_file = os.path.join(log_dir, "trades.json")
        self.signal_log_file = os.path.join(log_dir, "signals.json")
        self.portfolio_log_file = os.path.join(log_dir, "portfolio.json")
        
        # Initialize log files if they don't exist
        for log_file in [self.trade_log_file, self.signal_log_file, self.portfolio_log_file]:
            if not os.path.exists(log_file):
                with open(log_file, "w") as f:
                    json.dump([], f)
        
        logger.info(f"Initialized TradeLogger with log directory: {log_dir}")
    
    def _append_to_log(self, log_file: str, data: Dict[str, Any]):
        """
        Append data to a log file
        
        Args:
            log_file: Path to log file
            data: Data to append
        """
        try:
            # Read existing log
            with open(log_file, "r") as f:
                log_data = json.load(f)
            
            # Append new data
            log_data.append(data)
            
            # Write updated log
            with open(log_file, "w") as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to append to log {log_file}: {e}")
    
    def log_signal(self, instrument_id: str, signal: int, price: float, 
                  strategy: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a trading signal
        
        Args:
            instrument_id: Instrument identifier
            signal: Signal value (1 for buy, -1 for sell)
            price: Current price when signal was generated
            strategy: Strategy that generated the signal
            metadata: Additional signal data
        """
        signal_data = {
            "timestamp": datetime.now().isoformat(),
            "instrument_id": instrument_id,
            "signal": signal,
            "price": price,
            "strategy": strategy
        }
        
        if metadata:
            signal_data["metadata"] = metadata
            
        self._append_to_log(self.signal_log_file, signal_data)
        logger.info(f"Logged signal: {signal} for {instrument_id} at {price}")
    
    def log_trade(self, instrument_id: str, direction: str, quantity: int, 
                 price: float, order_id: str, broker: str, account_id: str):
        """
        Log an executed trade
        
        Args:
            instrument_id: Instrument identifier
            direction: Trade direction (buy or sell)
            quantity: Quantity traded
            price: Execution price
            order_id: Order ID from broker
            broker: Broker name
            account_id: Account ID
        """
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "instrument_id": instrument_id,
            "direction": direction,
            "quantity": quantity,
            "price": price,
            "order_id": order_id,
            "broker": broker,
            "account_id": account_id,
            "total_value": price * quantity
        }
        
        self._append_to_log(self.trade_log_file, trade_data)
        logger.info(f"Logged trade: {direction} {quantity} {instrument_id} at {price}")
    
    def log_portfolio(self, broker: str, account_id: str, total_value: float, 
                     cash: float, positions: Dict[str, Any]):
        """
        Log portfolio state
        
        Args:
            broker: Broker name
            account_id: Account ID
            total_value: Total portfolio value
            cash: Available cash
            positions: Current positions
        """
        portfolio_data = {
            "timestamp": datetime.now().isoformat(),
            "broker": broker,
            "account_id": account_id,
            "total_value": total_value,
            "cash": cash,
            "positions": positions
        }
        
        self._append_to_log(self.portfolio_log_file, portfolio_data)
        logger.info(f"Logged portfolio: total_value={total_value}, cash={cash}")
    
    def get_trades(self, instrument_id: Optional[str] = None, 
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None) -> list:
        """
        Get trades from log
        
        Args:
            instrument_id: Filter by instrument (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            
        Returns:
            List of trades matching criteria
        """
        try:
            with open(self.trade_log_file, "r") as f:
                trades = json.load(f)
            
            filtered_trades = []
            for trade in trades:
                include = True
                
                # Filter by instrument
                if instrument_id and trade.get("instrument_id") != instrument_id:
                    include = False
                
                # Filter by date range
                trade_date = datetime.fromisoformat(trade.get("timestamp"))
                if start_date and trade_date < start_date:
                    include = False
                if end_date and trade_date > end_date:
                    include = False
                
                if include:
                    filtered_trades.append(trade)
            
            return filtered_trades
            
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return []
    
    def get_portfolio_history(self, broker: Optional[str] = None,
                            account_id: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> list:
        """
        Get portfolio history from log
        
        Args:
            broker: Filter by broker (optional)
            account_id: Filter by account ID (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            
        Returns:
            List of portfolio snapshots matching criteria
        """
        try:
            with open(self.portfolio_log_file, "r") as f:
                portfolio_history = json.load(f)
            
            filtered_history = []
            for snapshot in portfolio_history:
                include = True
                
                # Filter by broker
                if broker and snapshot.get("broker") != broker:
                    include = False
                
                # Filter by account
                if account_id and snapshot.get("account_id") != account_id:
                    include = False
                
                # Filter by date range
                snapshot_date = datetime.fromisoformat(snapshot.get("timestamp"))
                if start_date and snapshot_date < start_date:
                    include = False
                if end_date and snapshot_date > end_date:
                    include = False
                
                if include:
                    filtered_history.append(snapshot)
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return [] 