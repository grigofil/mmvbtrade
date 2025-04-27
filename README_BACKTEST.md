# Backtesting Module

This module provides tools for backtesting trading strategies on historical price data, evaluating performance metrics, and optimizing strategy parameters.

## Features

- Load historical data from various sources (CSV, JSON, APIs)
- Run backtests with customizable parameters
- Calculate comprehensive performance metrics
- Generate visual reports
- Compare different strategies
- Optimize strategy parameters

## Directory Structure

```
app/
├── backtest/
│   ├── __init__.py         # Module initialization
│   ├── backtest_runner.py  # Main orchestration class
│   ├── performance_metrics.py  # Metrics calculation and reporting
│   └── examples/           # Example scripts
│       └── example_backtest.py  # Example usage
├── data/
│   ├── __init__.py         # Data module initialization  
│   └── historical_data.py  # Historical data loading
├── strategies/
│   ├── __init__.py         # Strategy module initialization
│   ├── base.py             # Base strategy class
│   ├── backtest.py         # Backtest implementation
│   └── ...                 # Strategy implementations
```

## Core Components

### 1. HistoricalDataLoader (app/data/historical_data.py)

Handles loading price data from various sources:
- CSV files
- JSON files
- External APIs (Alpha Vantage, Binance)

Also supports:
- Data caching
- Resampling (changing timeframes)
- Data conversion and export

### 2. Backtest (app/strategies/backtest.py)

Core backtesting engine:
- Processes candle by candle
- Calculates equity curve
- Tracks trades and positions
- Simulates slippage and commissions

### 3. BacktestRunner (app/backtest/backtest_runner.py)

Orchestrates the backtesting process:
- Initializes data, strategy, and backtest
- Saves and loads results
- Generates reports
- Compares strategies
- Optimizes strategy parameters

### 4. PerformanceMetrics (app/backtest/performance_metrics.py)

Calculates and visualizes performance metrics:
- Return metrics (total, annualized)
- Risk metrics (drawdown, volatility)
- Risk-adjusted metrics (Sharpe, Sortino, Calmar)
- Trade metrics (win rate, profit factor)
- Visualization and reporting

## Usage Example

```python
from app.strategies.moving_average import MovingAverageStrategy
from app.backtest.backtest_runner import BacktestRunner

# Initialize backtest runner
runner = BacktestRunner(output_dir="results/backtests")

# Create strategy
ma_strategy = MovingAverageStrategy(
    fast_period=10,
    slow_period=30
)

# Run backtest
results = runner.run_backtest(
    strategy=ma_strategy,
    symbol="BTCUSDT",
    start_date="2022-01-01",
    end_date="2022-12-31",
    timeframe="1d",
    initial_capital=10000.0,
    data_source="csv",
    data_path="data/BTCUSDT_1d.csv"
)

# Generate report
report_path = runner.generate_report(results['backtest_id'])

# Optimize strategy
optimization_results = runner.optimize_strategy(
    strategy_class=MovingAverageStrategy,
    param_ranges={
        'fast_period': [5, 10, 15],
        'slow_period': [20, 30, 40]
    },
    symbol="BTCUSDT",
    start_date="2022-01-01",
    end_date="2022-12-31",
    timeframe="1d",
    target_metric='sharpe_ratio',
    data_source="csv",
    data_path="data/BTCUSDT_1d.csv"
)
```

## Running the Example

The module includes an example script that demonstrates the basic usage:

```bash
python -m app.backtest.examples.example_backtest
```

This will:
1. Create sample data (if it doesn't exist)
2. Run backtests on two different strategies
3. Generate performance reports
4. Compare strategies
5. Optimize strategy parameters

## Generated Reports

The HTML reports include:
- Performance summary (returns, risk metrics, trade statistics)
- Equity curve and drawdown chart
- Monthly returns heatmap
- Trade distribution
- Detailed metrics and trade list

Reports are saved in the specified output directory, organized by backtest ID.

## Data Format

The backtesting engine expects historical price data in the following format:

```
[
  {
    'time': '2022-01-01T00:00:00',  # ISO format timestamp
    'o': 46000.0,                    # Open price
    'h': 47500.0,                    # High price
    'l': 45800.0,                    # Low price
    'c': 47000.0,                    # Close price
    'v': 1250.5                      # Volume
  },
  ...
]
```

CSV files should have columns: 'time', 'open', 'high', 'low', 'close', 'volume'.

## Adding New Strategies

To create a new strategy for backtesting:

1. Create a new strategy class that inherits from `app.strategies.base.Strategy`
2. Implement the required methods, especially `analyze()`
3. Use the backtesting module to test and optimize your strategy 