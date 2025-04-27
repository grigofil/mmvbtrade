"""
Logging configuration for the trading bot.
"""
import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional, List, Union

# Create custom loggers
main_logger = logging.getLogger('main')
trade_logger = logging.getLogger('trades')
signal_logger = logging.getLogger('signals')
risk_logger = logging.getLogger('risk')
position_logger = logging.getLogger('positions')
portfolio_logger = logging.getLogger('portfolio')
error_logger = logging.getLogger('errors')

def setup_logging(console_level: str = 'INFO', log_dir: str = 'logs') -> None:
    """
    Configure logging for the trading bot application.
    
    Args:
        console_level: Logging level for console output (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up logging level mapping
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    console_log_level = level_map.get(console_level.upper(), logging.INFO)
    file_log_level = logging.DEBUG  # Always keep detailed logs in files
    
    # Create formatters
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    json_formatter = logging.Formatter('%(message)s')
    
    # Root logger configuration (terminal output)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler (for terminal output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Configure main application logger
    main_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    main_file_handler.setLevel(file_log_level)
    main_file_handler.setFormatter(file_formatter)
    main_logger.addHandler(main_file_handler)
    
    # Configure specialized loggers with both text and JSON formats
    _setup_specialized_logger(trade_logger, 'trades.log', 'trades.json', log_dir, file_log_level)
    _setup_specialized_logger(signal_logger, 'signals.log', 'signals.json', log_dir, file_log_level)
    _setup_specialized_logger(risk_logger, 'risk.log', 'risk.json', log_dir, file_log_level)
    _setup_specialized_logger(position_logger, 'positions.log', 'positions.json', log_dir, file_log_level)
    _setup_specialized_logger(portfolio_logger, 'portfolio.log', 'portfolio.json', log_dir, file_log_level)
    _setup_specialized_logger(error_logger, 'errors.log', 'errors.json', log_dir, file_log_level)
    
    main_logger.info("Logging initialized")

def _setup_specialized_logger(
    logger: logging.Logger,
    text_filename: str,
    json_filename: str,
    log_dir: str,
    level: int
) -> None:
    """Set up a specialized logger with both text and JSON handlers."""
    # Text log handler
    text_handler = RotatingFileHandler(
        os.path.join(log_dir, text_filename),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    text_handler.setLevel(level)
    text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(text_handler)
    
    # JSON log handler for structured data
    json_handler = RotatingFileHandler(
        os.path.join(log_dir, json_filename),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    json_handler.setLevel(level)
    json_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(json_handler)
    
    # Ensure the logger doesn't propagate to root
    logger.propagate = False
    logger.setLevel(level)

def log_trade(
    action: str,
    symbol: str,
    price: float,
    quantity: int,
    order_id: Optional[str] = None,
    broker: Optional[str] = None,
    strategy: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a trade action.
    
    Args:
        action: The trade action (BUY, SELL, etc.)
        symbol: The trading symbol/ticker
        price: The execution price
        quantity: The quantity traded
        order_id: Optional order identifier
        broker: Optional broker name
        strategy: Optional strategy name that generated the trade
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "TRADE",
        "action": action,
        "symbol": symbol,
        "price": price,
        "quantity": quantity,
        "order_id": order_id,
        "broker": broker,
        "strategy": strategy
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    trade_logger.info(
        f"Trade: {action} {quantity} {symbol} @ {price} "
        f"[Order: {order_id}, Broker: {broker}, Strategy: {strategy}]"
    )
    
    # Log as JSON
    trade_logger.info(json.dumps(log_data))

def log_signal(
    strategy: str,
    symbol: str, 
    signal_type: str,
    value: Union[float, str],
    timeframe: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a strategy signal.
    
    Args:
        strategy: The strategy name
        symbol: The trading symbol
        signal_type: Type of signal (e.g., "BUY", "SELL", "CROSSOVER")
        value: The signal value or strength
        timeframe: Optional timeframe of the signal
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "SIGNAL",
        "strategy": strategy,
        "symbol": symbol,
        "signal_type": signal_type,
        "value": value,
        "timeframe": timeframe
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    signal_logger.info(
        f"Signal: {strategy} generated {signal_type} for {symbol} "
        f"with value {value} [Timeframe: {timeframe}]"
    )
    
    # Log as JSON
    signal_logger.info(json.dumps(log_data))

def log_risk_event(
    event_type: str,
    symbol: Optional[str] = None,
    value: Optional[Union[float, str]] = None,
    threshold: Optional[float] = None,
    action_taken: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a risk management event.
    
    Args:
        event_type: Type of risk event (e.g., "STOP_LOSS", "MAX_DRAWDOWN", "EXPOSURE_LIMIT")
        symbol: Optional trading symbol related to the event
        value: Optional value that triggered the event
        threshold: Optional threshold that was exceeded
        action_taken: Optional action taken in response
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "RISK_EVENT",
        "event_type": event_type,
        "symbol": symbol,
        "value": value,
        "threshold": threshold,
        "action_taken": action_taken
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    risk_logger.info(
        f"Risk Event: {event_type} for {symbol or 'portfolio'} "
        f"with value {value} [Threshold: {threshold}, Action: {action_taken}]"
    )
    
    # Log as JSON
    risk_logger.info(json.dumps(log_data))

def log_position_change(
    symbol: str,
    old_position: int,
    new_position: int,
    reason: str,
    strategy: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a position change.
    
    Args:
        symbol: The trading symbol
        old_position: Previous position size
        new_position: New position size
        reason: Reason for the position change
        strategy: Optional strategy that caused the change
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "POSITION_CHANGE",
        "symbol": symbol,
        "old_position": old_position,
        "new_position": new_position,
        "change": new_position - old_position,
        "reason": reason,
        "strategy": strategy
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    position_logger.info(
        f"Position Change: {symbol} from {old_position} to {new_position} "
        f"(Δ: {new_position - old_position}) [Reason: {reason}, Strategy: {strategy}]"
    )
    
    # Log as JSON
    position_logger.info(json.dumps(log_data))

def log_portfolio(
    total_value: float,
    cash_balance: float,
    positions: Dict[str, Dict[str, Any]],
    unrealized_pnl: Optional[float] = None,
    realized_pnl: Optional[float] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log portfolio state.
    
    Args:
        total_value: Total portfolio value
        cash_balance: Available cash balance
        positions: Dictionary of current positions (symbol -> position details)
        unrealized_pnl: Optional unrealized profit/loss
        realized_pnl: Optional realized profit/loss
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "PORTFOLIO",
        "total_value": total_value,
        "cash_balance": cash_balance,
        "positions": positions,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    position_summary = ", ".join([f"{symbol}: {pos.get('quantity', 0)}" for symbol, pos in positions.items()])
    portfolio_logger.info(
        f"Portfolio: Total Value: {total_value}, Cash: {cash_balance}, "
        f"PnL (Unrealized/Realized): {unrealized_pnl}/{realized_pnl} [Positions: {position_summary}]"
    )
    
    # Log as JSON
    portfolio_logger.info(json.dumps(log_data))

def log_error(
    error_type: str,
    message: str,
    component: Optional[str] = None,
    exception: Optional[Exception] = None,
    stack_trace: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error or exception.
    
    Args:
        error_type: Type of error
        message: Error message
        component: Optional component where the error occurred
        exception: Optional exception object
        stack_trace: Optional stack trace
        additional_info: Any additional information to log
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "ERROR",
        "error_type": error_type,
        "message": message,
        "component": component
    }
    
    if exception:
        log_data["exception"] = str(exception)
    
    if stack_trace:
        log_data["stack_trace"] = stack_trace
    
    if additional_info:
        log_data.update(additional_info)
    
    # Log as text
    error_logger.error(
        f"Error: {error_type} in {component or 'unknown'}: {message}"
    )
    
    # Log as JSON
    error_logger.error(json.dumps(log_data)) 