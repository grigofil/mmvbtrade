"""
Trading strategies module

This module provides implementations of various trading strategies and a factory
for creating and managing them.
"""

from app.strategies.base import Strategy
from app.strategies.moving_average import MovingAverageStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.factory import StrategyFactory
from app.strategies.backtest import Backtest

__all__ = [
    'Strategy',
    'MovingAverageStrategy',
    'MeanReversionStrategy',
    'StrategyFactory',
    'Backtest'
] 