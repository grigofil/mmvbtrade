"""
Example script for using the backtesting module
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from app.strategies.moving_average import MovingAverageStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.data.historical_data import HistoricalDataLoader
from app.backtest.backtest_runner import BacktestRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    """
    Run example backtests
    """
    logger.info("Starting example backtest script")
    
    # Initialize data loader
    data_loader = HistoricalDataLoader(data_dir="data/historical")
    
    # Set up sample data
    symbol = "BTCUSDT"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Download historical data (replace with your API key)
    api_key = "YOUR_API_KEY"  # Replace with your API key
    
    # Uncomment the following lines to download data from API
    # candles = data_loader.download_from_api(
    #     symbol=symbol,
    #     interval="1d",
    #     start_date=start_date,
    #     end_date=end_date,
    #     api_key=api_key,
    #     provider="binance"  # Or "alphavantage" if you have an API key
    # )
    
    # For the example, we'll create a sample data file
    # This would normally be downloaded from an API or loaded from a CSV/JSON file
    
    # Create a simple CSV file with sample data
    sample_data_dir = "data/historical"
    os.makedirs(sample_data_dir, exist_ok=True)
    
    sample_file = os.path.join(sample_data_dir, f"{symbol}_1d_sample.csv")
    
    # Check if sample file already exists
    if not os.path.exists(sample_file):
        logger.info(f"Creating sample data file: {sample_file}")
        
        # Generate sample data
        import pandas as pd
        import numpy as np
        
        # Generate 365 days of data
        dates = [datetime.now() - timedelta(days=i) for i in range(365)]
        dates.reverse()
        
        # Start price and generate random walk
        price = 40000.0
        prices = [price]
        
        # Generate a somewhat realistic price series
        for i in range(1, 365):
            # Random daily return, slightly positive bias
            daily_return = np.random.normal(0.0005, 0.02)
            price = price * (1 + daily_return)
            prices.append(price)
        
        # Create dataframe
        df = pd.DataFrame({
            'time': dates,
            'open': prices,
            'high': [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
            'low': [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
            'close': prices,
            'volume': [np.random.uniform(100, 1000) for _ in prices]
        })
        
        # Save to CSV
        df.to_csv(sample_file, index=False)
        logger.info(f"Created sample data with {len(df)} candles")
    
    # Initialize backtest runner
    runner = BacktestRunner(output_dir="results/backtests")
    
    # Create strategies to test
    ma_strategy = MovingAverageStrategy(
        fast_period=10,
        slow_period=30,
        signal_threshold=0.0,
        overbought_level=70,
        oversold_level=30
    )
    
    mr_strategy = MeanReversionStrategy(
        lookback_period=20,
        std_dev=2.0,
        rsi_period=14,
        oversold_threshold=30,
        overbought_threshold=70
    )
    
    # Run backtests
    logger.info("Running Moving Average strategy backtest")
    ma_results = runner.run_backtest(
        strategy=ma_strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe="1d",
        initial_capital=10000.0,
        commission_pct=0.001,
        data_source="csv",
        data_path=sample_file
    )
    
    logger.info("Running Mean Reversion strategy backtest")
    mr_results = runner.run_backtest(
        strategy=mr_strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe="1d",
        initial_capital=10000.0,
        commission_pct=0.001,
        data_source="csv",
        data_path=sample_file
    )
    
    # Generate reports
    ma_report = runner.generate_report(ma_results['backtest_id'])
    mr_report = runner.generate_report(mr_results['backtest_id'])
    
    logger.info(f"Moving Average strategy report: {ma_report}")
    logger.info(f"Mean Reversion strategy report: {mr_report}")
    
    # Compare strategies
    comparison = runner.compare_strategies([
        ma_results['backtest_id'],
        mr_results['backtest_id']
    ])
    
    logger.info("Strategy comparison:")
    for strategy in comparison['strategies']:
        logger.info(f"  {strategy['strategy']}: {strategy['total_return']:.2f}% ({strategy['trades_count']} trades)")
    
    # Optimize Moving Average strategy
    logger.info("Optimizing Moving Average strategy")
    optimization_results = runner.optimize_strategy(
        strategy_class=MovingAverageStrategy,
        param_ranges={
            'fast_period': [5, 10, 15, 20],
            'slow_period': [20, 30, 40, 50],
            'signal_threshold': [0.0, 0.5, 1.0]
        },
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe="1d",
        target_metric='sharpe_ratio',
        data_source="csv",
        data_path=sample_file
    )
    
    logger.info("Optimization results:")
    logger.info(f"Best parameters: {optimization_results['best_params']}")
    logger.info(f"Best value: {optimization_results['best_value']}")
    
    logger.info("Example backtest script completed")

if __name__ == "__main__":
    main() 