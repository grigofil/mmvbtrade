"""
Backtesting module for evaluating trading strategies
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import os

from app.strategies.base import Strategy

logger = logging.getLogger(__name__)

class Backtest:
    """
    Backtesting framework for evaluating trading strategies
    """
    
    def __init__(self, strategy: Strategy, initial_capital: float = 10000.0, 
                commission_pct: float = 0.001, slippage_pct: float = 0.0005):
        """
        Initialize backtester
        
        Args:
            strategy: Strategy instance to test
            initial_capital: Initial capital amount (default: 10000.0)
            commission_pct: Commission rate as percentage (default: 0.1%)
            slippage_pct: Slippage rate as percentage (default: 0.05%)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
        # Results
        self.positions = []
        self.trades = []
        self.equity_curve = None
        
        logger.info(f"Initialized Backtest for {strategy.__class__.__name__}")
    
    def run(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Run backtest on historical candles
        
        Args:
            candles: List of historical candle data
            
        Returns:
            Dictionary with backtest results
        """
        if len(candles) < self.strategy.get_required_candles_count():
            logger.error(f"Not enough candles for backtest. Need at least {self.strategy.get_required_candles_count()}, got {len(candles)}")
            return {"error": "Not enough candles for backtest"}
        
        logger.info(f"Starting backtest with {len(candles)} candles")
        
        # Reset state
        self.positions = []
        self.trades = []
        
        # Initialize backtest state
        equity = self.initial_capital
        cash = self.initial_capital
        position = 0
        position_size = 0
        entry_price = 0
        entry_time = None
        
        # Initialize equity curve
        dates = []
        equity_values = []
        cash_values = []
        position_values = []
        
        # Process each candle
        for i in range(self.strategy.get_required_candles_count(), len(candles)):
            # Get candles up to this point
            historical_candles = candles[:i]
            current_candle = candles[i]
            candle_time = datetime.fromisoformat(current_candle['time'].replace('Z', '+00:00'))
            
            # Get signal from strategy
            signal, metadata = self.strategy.analyze(historical_candles)
            
            # Current price (use close price for simplicity)
            current_price = float(current_candle['c'])
            
            # Update position value
            position_value = position * current_price
            
            # Update equity
            equity = cash + position_value
            
            # Save equity curve data
            dates.append(candle_time)
            equity_values.append(equity)
            cash_values.append(cash)
            position_values.append(position_value)
            
            # Execute trades based on signal
            if signal == 1 and position == 0:  # Buy signal
                # Calculate position size (use all available cash)
                position_size = cash
                
                # Calculate number of shares/tokens to buy
                buy_price = current_price * (1 + self.slippage_pct)  # Apply slippage
                position = (position_size - position_size * self.commission_pct) / buy_price
                
                # Update cash
                cash = 0
                
                # Record entry
                entry_price = buy_price
                entry_time = candle_time
                
                # Log trade
                trade = {
                    'type': 'buy',
                    'time': candle_time.isoformat(),
                    'price': buy_price,
                    'quantity': position,
                    'value': position_size,
                    'commission': position_size * self.commission_pct
                }
                
                self.trades.append(trade)
                logger.debug(f"BUY: {position} units at {buy_price}")
                
            elif signal == -1 and position > 0:  # Sell signal
                # Calculate sell value
                sell_price = current_price * (1 - self.slippage_pct)  # Apply slippage
                sell_value = position * sell_price
                
                # Update cash
                commission = sell_value * self.commission_pct
                cash += sell_value - commission
                
                # Calculate profit/loss
                profit_loss = sell_value - position_size
                profit_loss_pct = (sell_value / position_size - 1) * 100
                
                # Log trade
                trade = {
                    'type': 'sell',
                    'time': candle_time.isoformat(),
                    'price': sell_price,
                    'quantity': position,
                    'value': sell_value,
                    'commission': commission,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'holding_period': (candle_time - entry_time).total_seconds() / 86400  # in days
                }
                
                self.trades.append(trade)
                logger.debug(f"SELL: {position} units at {sell_price}, P/L: {profit_loss_pct:.2f}%")
                
                # Update position
                position = 0
                position_size = 0
                entry_price = 0
                entry_time = None
        
        # Close any open position at the end
        if position > 0:
            # Calculate sell value
            sell_price = candles[-1]['c'] * (1 - self.slippage_pct)  # Apply slippage
            sell_value = position * sell_price
            
            # Update cash
            commission = sell_value * self.commission_pct
            cash += sell_value - commission
            
            # Calculate profit/loss
            profit_loss = sell_value - position_size
            profit_loss_pct = (sell_value / position_size - 1) * 100
            
            # Log trade
            trade = {
                'type': 'sell',
                'time': dates[-1].isoformat(),
                'price': sell_price,
                'quantity': position,
                'value': sell_value,
                'commission': commission,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct,
                'holding_period': (dates[-1] - entry_time).total_seconds() / 86400  # in days
            }
            
            self.trades.append(trade)
            logger.debug(f"FINAL SELL: {position} units at {sell_price}, P/L: {profit_loss_pct:.2f}%")
            
            # Update position
            position = 0
        
        # Store equity curve
        self.equity_curve = pd.DataFrame({
            'date': dates,
            'equity': equity_values,
            'cash': cash_values,
            'position': position_values
        })
        
        # Calculate performance metrics
        metrics = self.calculate_performance_metrics()
        
        # Format results
        results = {
            'strategy': self.strategy.__class__.__name__,
            'parameters': self.strategy.get_strategy_info().get('parameters', {}),
            'initial_capital': self.initial_capital,
            'final_equity': equity,
            'total_return': (equity / self.initial_capital - 1) * 100,
            'metrics': metrics,
            'trades_count': len(self.trades),
            'trades': self.trades
        }
        
        logger.info(f"Backtest completed. Final equity: {equity:.2f}, Return: {results['total_return']:.2f}%")
        
        return results
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate performance metrics from backtest results
        
        Returns:
            Dictionary with performance metrics
        """
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return {}
        
        metrics = {}
        
        # Total return
        initial_equity = self.equity_curve['equity'].iloc[0]
        final_equity = self.equity_curve['equity'].iloc[-1]
        total_return = (final_equity / initial_equity - 1) * 100
        metrics['total_return'] = total_return
        
        # Annualized return
        days = (self.equity_curve['date'].iloc[-1] - self.equity_curve['date'].iloc[0]).total_seconds() / 86400
        years = days / 365.25
        metrics['annualized_return'] = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Calculate daily returns
        self.equity_curve['daily_return'] = self.equity_curve['equity'].pct_change() * 100
        
        # Volatility (annualized)
        daily_volatility = self.equity_curve['daily_return'].std()
        metrics['volatility'] = daily_volatility * np.sqrt(252)  # Annualized
        
        # Sharpe ratio (assuming risk-free rate of 0)
        metrics['sharpe_ratio'] = metrics['annualized_return'] / metrics['volatility'] if metrics['volatility'] > 0 else 0
        
        # Maximum drawdown
        self.equity_curve['cummax'] = self.equity_curve['equity'].cummax()
        self.equity_curve['drawdown'] = (self.equity_curve['equity'] / self.equity_curve['cummax'] - 1) * 100
        metrics['max_drawdown'] = abs(self.equity_curve['drawdown'].min())
        
        # Calmar ratio
        metrics['calmar_ratio'] = metrics['annualized_return'] / metrics['max_drawdown'] if metrics['max_drawdown'] > 0 else 0
        
        # Win rate
        if len(self.trades) > 0:
            winning_trades = [t for t in self.trades if t.get('profit_loss', 0) > 0]
            metrics['win_rate'] = len(winning_trades) / len(self.trades) * 100
            
            # Average profit/loss
            profits = [t.get('profit_loss_pct', 0) for t in self.trades if t.get('profit_loss', 0) > 0]
            losses = [t.get('profit_loss_pct', 0) for t in self.trades if t.get('profit_loss', 0) <= 0]
            
            metrics['avg_profit'] = np.mean(profits) if len(profits) > 0 else 0
            metrics['avg_loss'] = np.mean(losses) if len(losses) > 0 else 0
            
            # Profit factor
            total_profit = sum([t.get('profit_loss', 0) for t in self.trades if t.get('profit_loss', 0) > 0])
            total_loss = abs(sum([t.get('profit_loss', 0) for t in self.trades if t.get('profit_loss', 0) < 0]))
            metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return metrics
    
    def plot_results(self, output_file: Optional[str] = None) -> None:
        """
        Plot backtest results
        
        Args:
            output_file: Path to save the plot (if None, display the plot)
        """
        if self.equity_curve is None or len(self.equity_curve) == 0:
            logger.error("No backtest results to plot")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(self.equity_curve['date'], self.equity_curve['equity'], label='Equity')
        plt.title(f'Backtest Results - {self.strategy.__class__.__name__}')
        plt.ylabel('Equity ($)')
        plt.legend()
        plt.grid(True)
        
        # Plot drawdown
        plt.subplot(2, 1, 2)
        plt.fill_between(self.equity_curve['date'], self.equity_curve['drawdown'], 0, alpha=0.3, color='red')
        plt.plot(self.equity_curve['date'], self.equity_curve['drawdown'], color='red', label='Drawdown')
        plt.ylabel('Drawdown (%)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Backtest plot saved to {output_file}")
        else:
            plt.show()
    
    def optimize_strategy(self, candles: List[Dict], 
                         param_ranges: Dict[str, List[Any]], 
                         target_metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """
        Optimize strategy parameters through grid search
        
        Args:
            candles: List of historical candle data
            param_ranges: Dictionary mapping parameter names to lists of values to test
            target_metric: Metric to optimize for
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Starting strategy optimization with {len(param_ranges)} parameters")
        
        # Validate input
        if not param_ranges:
            return {
                "error": "No parameters specified for optimization",
                "best_params": {},
                "best_value": 0,
                "results": []
            }
        
        # Track best parameters and results
        best_params = {}
        best_value = -float('inf')
        all_results = []
        
        # Generate parameter combinations
        from itertools import product
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        total_combinations = 1
        for values in param_values:
            total_combinations *= len(values)
        
        logger.info(f"Testing {total_combinations} parameter combinations")
        
        # Perform grid search
        for i, combination in enumerate(product(*param_values)):
            params = dict(zip(param_names, combination))
            
            logger.debug(f"Testing combination {i+1}/{total_combinations}: {params}")
            
            # Create new strategy instance with these parameters
            strategy_class = self.strategy.__class__
            strategy = strategy_class(**params)
            
            # Create new backtest instance
            bt = Backtest(
                strategy=strategy,
                initial_capital=self.initial_capital,
                commission_pct=self.commission_pct,
                slippage_pct=self.slippage_pct
            )
            
            # Run backtest
            result = bt.run(candles)
            
            # Extract target metric
            if 'metrics' in result and target_metric in result['metrics']:
                metric_value = result['metrics'][target_metric]
            elif target_metric in result:
                metric_value = result[target_metric]
            else:
                metric_value = 0
            
            # Save results
            result_summary = {
                "parameters": params,
                "metrics": result.get('metrics', {}),
                "total_return": result.get('total_return', 0),
                "trades_count": result.get('trades_count', 0)
            }
            all_results.append(result_summary)
            
            # Update best parameters if better
            if metric_value > best_value:
                best_value = metric_value
                best_params = params
                logger.debug(f"New best: {target_metric}={best_value}, params={best_params}")
        
        # Sort results by target metric
        all_results.sort(key=lambda x: x['metrics'].get(target_metric, 0) if 'metrics' in x else 0, reverse=True)
        
        logger.info(f"Optimization complete. Best {target_metric}: {best_value}, params: {best_params}")
        
        # Update strategy with best parameters
        for param, value in best_params.items():
            setattr(self.strategy, param, value)
        
        return {
            "best_params": best_params,
            "best_value": best_value,
            "results": all_results[:10]  # Return top 10 results
        } 