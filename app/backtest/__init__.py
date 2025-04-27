"""
Backtesting module

This module provides tools for backtesting trading strategies on historical data,
including performance metrics calculation and visualization.
"""

from app.backtest.backtest_runner import BacktestRunner
from app.backtest.performance_metrics import PerformanceMetrics

__all__ = [
    'BacktestRunner',
    'PerformanceMetrics'
] 