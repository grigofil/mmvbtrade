"""
Backtest runner for executing strategy backtests
"""
import logging
import pandas as pd
import numpy as np
import os
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import json

from app.strategies.base import Strategy
from app.strategies.backtest import Backtest
from app.data.historical_data import HistoricalDataLoader
from app.backtest.performance_metrics import PerformanceMetrics

logger = logging.getLogger(__name__)

class BacktestRunner:
    """
    Runner class for orchestrating backtesting processes
    """
    
    def __init__(self, output_dir: str = "results/backtests"):
        """
        Initialize backtest runner
        
        Args:
            output_dir: Directory to store backtest results
        """
        self.output_dir = output_dir
        self.data_loader = HistoricalDataLoader()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Initialized BacktestRunner with output directory: {output_dir}")
    
    def run_backtest(self, strategy: Strategy, symbol: str, 
                   start_date: str, end_date: str,
                   timeframe: str = "1d",
                   initial_capital: float = 10000.0,
                   commission_pct: float = 0.001,
                   slippage_pct: float = 0.0005,
                   data_source: str = "csv",
                   data_path: Optional[str] = None,
                   **data_kwargs) -> Dict[str, Any]:
        """
        Run a backtest for the given strategy and parameters
        
        Args:
            strategy: Strategy instance to test
            symbol: Trading symbol
            start_date: Start date in ISO format
            end_date: End date in ISO format
            timeframe: Candlestick timeframe
            initial_capital: Initial capital
            commission_pct: Commission percentage
            slippage_pct: Slippage percentage
            data_source: Source of historical data ('csv', 'json', 'api')
            data_path: Path to data file (for 'csv' and 'json' sources)
            **data_kwargs: Additional arguments for data loading
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest for {strategy.__class__.__name__} on {symbol} " 
                   f"from {start_date} to {end_date} ({timeframe})")
        
        # Start time for performance measurement
        start_time = time.time()
        
        # Load historical data
        candles = self._load_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            data_source=data_source,
            data_path=data_path,
            **data_kwargs
        )
        
        if not candles:
            logger.error("Failed to load historical data")
            return {"error": "Failed to load historical data"}
        
        logger.info(f"Loaded {len(candles)} candles for {symbol}")
        
        # Create backtest instance
        backtest = Backtest(
            strategy=strategy,
            initial_capital=initial_capital,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct
        )
        
        # Run backtest
        results = backtest.run(candles)
        
        # Add additional metadata to results
        results['symbol'] = symbol
        results['timeframe'] = timeframe
        results['start_date'] = start_date
        results['end_date'] = end_date
        results['execution_time'] = time.time() - start_time
        
        # Save results
        backtest_id = f"{symbol}_{timeframe}_{strategy.__class__.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results['backtest_id'] = backtest_id
        self._save_results(results, backtest_id)
        
        logger.info(f"Backtest completed in {results['execution_time']:.2f} seconds. "
                   f"Return: {results['total_return']:.2f}%, Trades: {results['trades_count']}")
        
        return results
    
    def _load_historical_data(self, symbol: str, start_date: str, end_date: str,
                             timeframe: str, data_source: str, data_path: Optional[str] = None,
                             **kwargs) -> List[Dict]:
        """
        Load historical data based on source
        """
        if data_source == "csv" and data_path:
            return self.data_loader.load_from_csv(
                file_path=data_path,
                date_format=kwargs.get('date_format', "%Y-%m-%d %H:%M:%S"),
                date_column=kwargs.get('date_column', "time")
            )
        elif data_source == "json" and data_path:
            return self.data_loader.load_from_json(file_path=data_path)
        elif data_source == "api":
            provider = kwargs.get('provider', 'alphavantage')
            api_key = kwargs.get('api_key')
            return self.data_loader.download_from_api(
                symbol=symbol,
                interval=timeframe,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key,
                provider=provider
            )
        else:
            logger.error(f"Unsupported data source: {data_source}")
            return []
    
    def _save_results(self, results: Dict[str, Any], backtest_id: str) -> None:
        """
        Save backtest results to file
        """
        # Create directory for this backtest
        backtest_dir = os.path.join(self.output_dir, backtest_id)
        os.makedirs(backtest_dir, exist_ok=True)
        
        # Save results as JSON
        results_file = os.path.join(backtest_dir, "results.json")
        
        # Create a copy without the equity_curve (will be saved separately)
        results_copy = {k: v for k, v in results.items() if k != 'equity_curve'}
        
        with open(results_file, 'w') as f:
            json.dump(results_copy, f, indent=4, default=str)
        
        # Save equity curve
        if 'equity_curve' in results and results['equity_curve'] is not None:
            equity_file = os.path.join(backtest_dir, "equity_curve.csv")
            results['equity_curve'].to_csv(equity_file, index=False)
        
        # Save trades
        if 'trades' in results and results['trades']:
            trades_file = os.path.join(backtest_dir, "trades.csv")
            pd.DataFrame(results['trades']).to_csv(trades_file, index=False)
        
        logger.info(f"Saved backtest results to {backtest_dir}")
    
    def generate_report(self, backtest_id: str) -> str:
        """
        Generate HTML report for a backtest
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Path to the generated report
        """
        # Load results
        backtest_dir = os.path.join(self.output_dir, backtest_id)
        results_file = os.path.join(backtest_dir, "results.json")
        
        if not os.path.exists(results_file):
            logger.error(f"Results file not found: {results_file}")
            return ""
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Load equity curve
        equity_file = os.path.join(backtest_dir, "equity_curve.csv")
        if os.path.exists(equity_file):
            equity_curve = pd.read_csv(equity_file)
        else:
            logger.error(f"Equity curve file not found: {equity_file}")
            return ""
        
        # Load trades
        trades_file = os.path.join(backtest_dir, "trades.csv")
        if os.path.exists(trades_file):
            trades_df = pd.read_csv(trades_file)
            trades = trades_df.to_dict('records')
        else:
            logger.warning(f"Trades file not found: {trades_file}")
            trades = []
        
        # Generate report
        strategy_name = results.get('strategy', 'Unknown')
        symbol = results.get('symbol', 'Unknown')
        timeframe = results.get('timeframe', 'Unknown')
        report_title = f"{strategy_name} - {symbol} ({timeframe})"
        
        return PerformanceMetrics.generate_report(
            metrics=results.get('metrics', {}),
            equity_curve=equity_curve,
            trades=trades,
            output_dir=backtest_dir,
            strategy_name=report_title
        )
    
    def compare_strategies(self, backtest_ids: List[str]) -> Dict[str, Any]:
        """
        Compare results of multiple backtests
        
        Args:
            backtest_ids: List of backtest IDs to compare
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "strategies": [],
            "metrics": {}
        }
        
        # Load results for each backtest
        for backtest_id in backtest_ids:
            backtest_dir = os.path.join(self.output_dir, backtest_id)
            results_file = os.path.join(backtest_dir, "results.json")
            
            if not os.path.exists(results_file):
                logger.warning(f"Results file not found: {results_file}")
                continue
            
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            strategy_info = {
                "backtest_id": backtest_id,
                "strategy": results.get('strategy', 'Unknown'),
                "symbol": results.get('symbol', 'Unknown'),
                "timeframe": results.get('timeframe', 'Unknown'),
                "start_date": results.get('start_date', 'Unknown'),
                "end_date": results.get('end_date', 'Unknown'),
                "total_return": results.get('total_return', 0),
                "trades_count": results.get('trades_count', 0)
            }
            
            # Add metrics
            metrics = results.get('metrics', {})
            for metric, value in metrics.items():
                if metric not in comparison["metrics"]:
                    comparison["metrics"][metric] = []
                
                comparison["metrics"][metric].append({
                    "strategy": strategy_info["strategy"],
                    "value": value
                })
            
            comparison["strategies"].append(strategy_info)
        
        # Sort strategies by total return
        comparison["strategies"] = sorted(
            comparison["strategies"], 
            key=lambda x: x.get('total_return', 0), 
            reverse=True
        )
        
        return comparison
    
    def optimize_strategy(self, strategy_class, param_ranges: Dict[str, List[Any]], symbol: str,
                         start_date: str, end_date: str, timeframe: str,
                         initial_capital: float = 10000.0, target_metric: str = 'sharpe_ratio',
                         data_source: str = "csv", data_path: Optional[str] = None,
                         **data_kwargs) -> Dict[str, Any]:
        """
        Optimize strategy parameters using grid search
        
        Args:
            strategy_class: Strategy class to optimize
            param_ranges: Dictionary mapping parameter names to lists of values to test
            symbol: Trading symbol
            start_date: Start date in ISO format
            end_date: End date in ISO format
            timeframe: Candlestick timeframe
            initial_capital: Initial capital
            target_metric: Metric to optimize
            data_source: Source of historical data
            data_path: Path to data file
            **data_kwargs: Additional arguments for data loading
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Starting optimization for {strategy_class.__name__} on {symbol}")
        
        # Load historical data (just once for all backtests)
        candles = self._load_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            data_source=data_source,
            data_path=data_path,
            **data_kwargs
        )
        
        if not candles:
            logger.error("Failed to load historical data")
            return {"error": "Failed to load historical data"}
        
        logger.info(f"Loaded {len(candles)} candles for optimization")
        
        # Create a default strategy instance for the backtest template
        default_params = {param: values[0] for param, values in param_ranges.items()}
        strategy = strategy_class(**default_params)
        
        # Create backtest template
        backtest = Backtest(
            strategy=strategy,
            initial_capital=initial_capital
        )
        
        # Run optimization
        optimization_results = backtest.optimize_strategy(
            candles=candles,
            param_ranges=param_ranges,
            target_metric=target_metric
        )
        
        # Add additional information to results
        optimization_results["symbol"] = symbol
        optimization_results["timeframe"] = timeframe
        optimization_results["start_date"] = start_date
        optimization_results["end_date"] = end_date
        optimization_results["strategy_class"] = strategy_class.__name__
        
        # Save optimization results
        optimization_id = f"optimize_{symbol}_{timeframe}_{strategy_class.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        optimization_dir = os.path.join(self.output_dir, optimization_id)
        os.makedirs(optimization_dir, exist_ok=True)
        
        with open(os.path.join(optimization_dir, "optimization_results.json"), 'w') as f:
            json.dump(optimization_results, f, indent=4, default=str)
        
        logger.info(f"Optimization completed. Best {target_metric}: {optimization_results['best_value']}")
        
        return optimization_results 