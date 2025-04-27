"""
Performance metrics calculation for backtesting results
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import matplotlib.pyplot as plt
import os

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Class for calculating various performance metrics from backtest results
    """
    
    @staticmethod
    def calculate_metrics(equity_curve: pd.DataFrame, trades: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics from backtest results
        
        Args:
            equity_curve: DataFrame with equity curve data
            trades: List of trade dictionaries
            
        Returns:
            Dictionary with calculated metrics
        """
        if equity_curve is None or len(equity_curve) == 0:
            logger.warning("Empty equity curve provided, cannot calculate metrics")
            return {}
        
        metrics = {}
        
        # Basic return metrics
        initial_equity = equity_curve['equity'].iloc[0]
        final_equity = equity_curve['equity'].iloc[-1]
        total_return = (final_equity / initial_equity - 1) * 100
        metrics['total_return'] = total_return
        
        # Time-based metrics
        try:
            # Calculate time period covered
            start_date = equity_curve['date'].iloc[0]
            end_date = equity_curve['date'].iloc[-1]
            days = (end_date - start_date).total_seconds() / 86400
            
            # Annualized metrics
            years = days / 365.25
            metrics['days'] = days
            metrics['years'] = years
            metrics['annualized_return'] = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating time-based metrics: {e}")
            metrics['days'] = 0
            metrics['years'] = 0
            metrics['annualized_return'] = 0
        
        # Calculate returns and volatility
        try:
            # Daily returns
            equity_curve['daily_return'] = equity_curve['equity'].pct_change() * 100
            metrics['daily_returns_mean'] = equity_curve['daily_return'].mean()
            
            # Volatility (annualized)
            daily_volatility = equity_curve['daily_return'].std()
            metrics['daily_volatility'] = daily_volatility
            metrics['annualized_volatility'] = daily_volatility * np.sqrt(252)  # Annualized
            
            # Risk-adjusted return metrics
            metrics['sharpe_ratio'] = metrics['annualized_return'] / metrics['annualized_volatility'] if metrics['annualized_volatility'] > 0 else 0
            
            # Sortino ratio (only considers downside volatility)
            downside_returns = equity_curve.loc[equity_curve['daily_return'] < 0, 'daily_return']
            downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            metrics['sortino_ratio'] = metrics['annualized_return'] / downside_volatility if downside_volatility > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating return/volatility metrics: {e}")
            metrics['daily_returns_mean'] = 0
            metrics['daily_volatility'] = 0
            metrics['annualized_volatility'] = 0
            metrics['sharpe_ratio'] = 0
            metrics['sortino_ratio'] = 0
        
        # Drawdown metrics
        try:
            # Calculate running maximum
            equity_curve['cummax'] = equity_curve['equity'].cummax()
            
            # Calculate drawdown percentage
            equity_curve['drawdown'] = (equity_curve['equity'] / equity_curve['cummax'] - 1) * 100
            
            # Max drawdown
            metrics['max_drawdown'] = abs(equity_curve['drawdown'].min())
            
            # Average drawdown
            drawdowns = equity_curve.loc[equity_curve['drawdown'] < 0, 'drawdown']
            metrics['avg_drawdown'] = abs(drawdowns.mean()) if len(drawdowns) > 0 else 0
            
            # Calmar ratio (return / max drawdown)
            metrics['calmar_ratio'] = metrics['annualized_return'] / metrics['max_drawdown'] if metrics['max_drawdown'] > 0 else 0
            
            # Drawdown duration metrics
            if len(drawdowns) > 0:
                # Find drawdown periods
                is_drawdown = equity_curve['drawdown'] < 0
                drawdown_periods = []
                current_period = None
                
                for i, row in equity_curve.iterrows():
                    if is_drawdown.loc[i] and current_period is None:
                        # Start new drawdown period
                        current_period = {'start': i, 'start_date': row['date']}
                    elif not is_drawdown.loc[i] and current_period is not None:
                        # End drawdown period
                        current_period['end'] = i
                        current_period['end_date'] = row['date']
                        current_period['duration'] = (current_period['end_date'] - current_period['start_date']).total_seconds() / 86400
                        drawdown_periods.append(current_period)
                        current_period = None
                
                # Handle ongoing drawdown
                if current_period is not None:
                    current_period['end'] = equity_curve.index[-1]
                    current_period['end_date'] = equity_curve['date'].iloc[-1]
                    current_period['duration'] = (current_period['end_date'] - current_period['start_date']).total_seconds() / 86400
                    drawdown_periods.append(current_period)
                
                # Calculate drawdown duration metrics
                durations = [period['duration'] for period in drawdown_periods]
                metrics['max_drawdown_duration'] = max(durations) if durations else 0
                metrics['avg_drawdown_duration'] = np.mean(durations) if durations else 0
                metrics['drawdown_periods_count'] = len(drawdown_periods)
            else:
                metrics['max_drawdown_duration'] = 0
                metrics['avg_drawdown_duration'] = 0
                metrics['drawdown_periods_count'] = 0
                
        except Exception as e:
            logger.error(f"Error calculating drawdown metrics: {e}")
            metrics['max_drawdown'] = 0
            metrics['avg_drawdown'] = 0
            metrics['calmar_ratio'] = 0
            metrics['max_drawdown_duration'] = 0
            metrics['avg_drawdown_duration'] = 0
            metrics['drawdown_periods_count'] = 0
        
        # Trade metrics
        if trades and len(trades) > 0:
            metrics['trades_count'] = len(trades)
            
            # Winning/losing trades
            winning_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
            losing_trades = [t for t in trades if t.get('profit_loss', 0) <= 0]
            
            metrics['winning_trades_count'] = len(winning_trades)
            metrics['losing_trades_count'] = len(losing_trades)
            metrics['win_rate'] = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0
            
            # Profit/loss metrics
            profits = [t.get('profit_loss_pct', 0) for t in winning_trades]
            losses = [t.get('profit_loss_pct', 0) for t in losing_trades]
            
            metrics['avg_profit'] = np.mean(profits) if len(profits) > 0 else 0
            metrics['avg_loss'] = np.mean(losses) if len(losses) > 0 else 0
            metrics['largest_profit'] = max(profits) if len(profits) > 0 else 0
            metrics['largest_loss'] = min(losses) if len(losses) > 0 else 0
            
            # Profit factor (sum of profits / sum of losses)
            total_profit = sum([t.get('profit_loss', 0) for t in winning_trades])
            total_loss = abs(sum([t.get('profit_loss', 0) for t in losing_trades]))
            metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # Expected payoff
            metrics['expected_payoff'] = (metrics['win_rate'] / 100 * metrics['avg_profit']) + ((100 - metrics['win_rate']) / 100 * metrics['avg_loss'])
            
            # Holding period metrics
            holding_periods = [t.get('holding_period', 0) for t in trades]
            metrics['avg_holding_period'] = np.mean(holding_periods) if len(holding_periods) > 0 else 0
            metrics['max_holding_period'] = max(holding_periods) if len(holding_periods) > 0 else 0
            metrics['min_holding_period'] = min(holding_periods) if len(holding_periods) > 0 else 0
            
            # Consecutive wins/losses
            consecutive_wins = 0
            consecutive_losses = 0
            max_consecutive_wins = 0
            max_consecutive_losses = 0
            current_streak = 0
            
            for trade in trades:
                if trade.get('profit_loss', 0) > 0:
                    # Winning trade
                    if current_streak > 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                    max_consecutive_wins = max(max_consecutive_wins, current_streak)
                else:
                    # Losing trade
                    if current_streak < 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                    max_consecutive_losses = max(max_consecutive_losses, abs(current_streak))
            
            metrics['max_consecutive_wins'] = max_consecutive_wins
            metrics['max_consecutive_losses'] = max_consecutive_losses
            
            # Recovery factor
            metrics['recovery_factor'] = total_return / metrics['max_drawdown'] if metrics['max_drawdown'] > 0 else float('inf')
            
        else:
            logger.warning("No trades provided, cannot calculate trade metrics")
            metrics['trades_count'] = 0
            metrics['winning_trades_count'] = 0
            metrics['losing_trades_count'] = 0
            metrics['win_rate'] = 0
            metrics['avg_profit'] = 0
            metrics['avg_loss'] = 0
            metrics['largest_profit'] = 0
            metrics['largest_loss'] = 0
            metrics['profit_factor'] = 0
            metrics['expected_payoff'] = 0
            metrics['avg_holding_period'] = 0
            metrics['max_holding_period'] = 0
            metrics['min_holding_period'] = 0
            metrics['max_consecutive_wins'] = 0
            metrics['max_consecutive_losses'] = 0
            metrics['recovery_factor'] = 0
        
        return metrics
    
    @staticmethod
    def plot_equity_curve(equity_curve: pd.DataFrame, output_file: Optional[str] = None) -> None:
        """
        Plot equity curve and drawdown
        
        Args:
            equity_curve: DataFrame with equity curve data
            output_file: Path to save the plot (if None, display the plot)
        """
        if equity_curve is None or len(equity_curve) == 0:
            logger.error("Empty equity curve provided, cannot plot")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(equity_curve['date'], equity_curve['equity'], label='Equity')
        plt.title('Backtest Results - Equity Curve')
        plt.ylabel('Equity')
        plt.legend()
        plt.grid(True)
        
        # Calculate and plot drawdown
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] / equity_curve['cummax'] - 1) * 100
        
        plt.subplot(2, 1, 2)
        plt.fill_between(equity_curve['date'], equity_curve['drawdown'], 0, alpha=0.3, color='red')
        plt.plot(equity_curve['date'], equity_curve['drawdown'], color='red', label='Drawdown')
        plt.ylabel('Drawdown (%)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Equity curve plot saved to {output_file}")
        else:
            plt.show()
    
    @staticmethod
    def plot_monthly_returns(equity_curve: pd.DataFrame, output_file: Optional[str] = None) -> None:
        """
        Plot monthly returns heatmap
        
        Args:
            equity_curve: DataFrame with equity curve data
            output_file: Path to save the plot (if None, display the plot)
        """
        if equity_curve is None or len(equity_curve) == 0:
            logger.error("Empty equity curve provided, cannot plot monthly returns")
            return
        
        # Ensure we have datetime index
        equity_curve = equity_curve.copy()
        equity_curve['date'] = pd.to_datetime(equity_curve['date'])
        
        # Calculate daily returns
        equity_curve['return'] = equity_curve['equity'].pct_change()
        
        # Resample to monthly returns
        monthly_returns = equity_curve.set_index('date')['return'].resample('M').apply(
            lambda x: (1 + x).prod() - 1
        ) * 100  # Convert to percentage
        
        # Create a pivot table for the heatmap
        monthly_returns_table = monthly_returns.reset_index()
        monthly_returns_table['Year'] = monthly_returns_table['date'].dt.year
        monthly_returns_table['Month'] = monthly_returns_table['date'].dt.month
        pivot_table = monthly_returns_table.pivot_table(
            values='return', index='Year', columns='Month', aggfunc='sum'
        )
        
        # Plot heatmap
        plt.figure(figsize=(12, 8))
        
        # Define colormap with green for positive and red for negative
        cmap = plt.cm.RdYlGn  # Red-Yellow-Green colormap
        
        # Plot heatmap
        ax = plt.gca()
        im = ax.imshow(pivot_table.values, cmap=cmap, aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im)
        cbar.set_label('Monthly Return (%)')
        
        # Set labels
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticks(np.arange(len(month_names)))
        ax.set_xticklabels(month_names)
        ax.set_yticks(np.arange(len(pivot_table.index)))
        ax.set_yticklabels(pivot_table.index)
        
        # Add text annotations with return values
        for i in range(len(pivot_table.index)):
            for j in range(len(month_names)):
                if j < pivot_table.values.shape[1]:
                    value = pivot_table.values[i, j]
                    if not np.isnan(value):
                        text_color = 'black' if abs(value) < 10 else 'white'
                        ax.text(j, i, f'{value:.1f}%', ha='center', va='center', color=text_color)
        
        plt.title('Monthly Returns (%)')
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Monthly returns plot saved to {output_file}")
        else:
            plt.show()
    
    @staticmethod
    def plot_trade_distribution(trades: List[Dict], output_file: Optional[str] = None) -> None:
        """
        Plot trade profit/loss distribution
        
        Args:
            trades: List of trade dictionaries
            output_file: Path to save the plot (if None, display the plot)
        """
        if not trades or len(trades) == 0:
            logger.error("No trades provided, cannot plot trade distribution")
            return
        
        # Extract profit/loss percentages
        pnl_values = [t.get('profit_loss_pct', 0) for t in trades]
        
        plt.figure(figsize=(12, 6))
        
        # Plot histogram
        plt.hist(pnl_values, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
        
        # Add statistical annotations
        mean_pnl = np.mean(pnl_values)
        median_pnl = np.median(pnl_values)
        win_rate = len([p for p in pnl_values if p > 0]) / len(pnl_values) * 100
        
        plt.title(f'Trade P/L Distribution (Win Rate: {win_rate:.1f}%)')
        plt.xlabel('Profit/Loss (%)')
        plt.ylabel('Number of Trades')
        plt.grid(True, alpha=0.3)
        
        # Add statistical lines
        plt.axvline(x=mean_pnl, color='green', linestyle='-', linewidth=1, label=f'Mean: {mean_pnl:.2f}%')
        plt.axvline(x=median_pnl, color='blue', linestyle='-', linewidth=1, label=f'Median: {median_pnl:.2f}%')
        
        plt.legend()
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Trade distribution plot saved to {output_file}")
        else:
            plt.show()
    
    @staticmethod
    def generate_report(metrics: Dict[str, Any], equity_curve: pd.DataFrame, trades: List[Dict], 
                       output_dir: str, strategy_name: str) -> str:
        """
        Generate comprehensive HTML report with all metrics and plots
        
        Args:
            metrics: Dictionary with performance metrics
            equity_curve: DataFrame with equity curve data
            trades: List of trade dictionaries
            output_dir: Directory to save the report
            strategy_name: Name of the strategy for the report title
            
        Returns:
            Path to the generated HTML report
        """
        try:
            import jinja2
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Save plots to files
            plots_dir = os.path.join(output_dir, 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            equity_plot_path = os.path.join(plots_dir, 'equity_curve.png')
            PerformanceMetrics.plot_equity_curve(equity_curve, equity_plot_path)
            
            monthly_returns_path = os.path.join(plots_dir, 'monthly_returns.png')
            PerformanceMetrics.plot_monthly_returns(equity_curve, monthly_returns_path)
            
            trade_dist_path = os.path.join(plots_dir, 'trade_distribution.png')
            PerformanceMetrics.plot_trade_distribution(trades, trade_dist_path)
            
            # Create HTML template
            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ strategy_name }} - Backtest Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2 { color: #333; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .plot-container { margin: 20px 0; text-align: center; }
                    .plot { max-width: 100%; height: auto; }
                    .metrics-section { display: flex; flex-wrap: wrap; }
                    .metrics-column { flex: 1; min-width: 300px; margin-right: 20px; }
                    .good { color: green; }
                    .bad { color: red; }
                    .neutral { color: blue; }
                </style>
            </head>
            <body>
                <h1>{{ strategy_name }} - Backtest Report</h1>
                <p>Report generated on {{ generation_date }}</p>
                
                <h2>Summary</h2>
                <div class="metrics-section">
                    <div class="metrics-column">
                        <table>
                            <tr><th colspan="2">Return Metrics</th></tr>
                            <tr><td>Total Return</td><td class="{{ 'good' if metrics.total_return > 0 else 'bad' }}">{{ metrics.total_return|round(2) }}%</td></tr>
                            <tr><td>Annualized Return</td><td class="{{ 'good' if metrics.annualized_return > 0 else 'bad' }}">{{ metrics.annualized_return|round(2) }}%</td></tr>
                            <tr><td>Sharpe Ratio</td><td class="{{ 'good' if metrics.sharpe_ratio > 1 else 'neutral' if metrics.sharpe_ratio > 0 else 'bad' }}">{{ metrics.sharpe_ratio|round(2) }}</td></tr>
                            <tr><td>Sortino Ratio</td><td class="{{ 'good' if metrics.sortino_ratio > 1 else 'neutral' if metrics.sortino_ratio > 0 else 'bad' }}">{{ metrics.sortino_ratio|round(2) }}</td></tr>
                            <tr><td>Calmar Ratio</td><td class="{{ 'good' if metrics.calmar_ratio > 1 else 'neutral' if metrics.calmar_ratio > 0 else 'bad' }}">{{ metrics.calmar_ratio|round(2) }}</td></tr>
                        </table>
                    </div>
                    
                    <div class="metrics-column">
                        <table>
                            <tr><th colspan="2">Risk Metrics</th></tr>
                            <tr><td>Max Drawdown</td><td class="{{ 'bad' if metrics.max_drawdown > 20 else 'neutral' }}">{{ metrics.max_drawdown|round(2) }}%</td></tr>
                            <tr><td>Average Drawdown</td><td>{{ metrics.avg_drawdown|round(2) }}%</td></tr>
                            <tr><td>Max Drawdown Duration</td><td>{{ metrics.max_drawdown_duration|round(1) }} days</td></tr>
                            <tr><td>Volatility (Annualized)</td><td>{{ metrics.annualized_volatility|round(2) }}%</td></tr>
                            <tr><td>Recovery Factor</td><td>{{ metrics.recovery_factor|round(2) }}</td></tr>
                        </table>
                    </div>
                    
                    <div class="metrics-column">
                        <table>
                            <tr><th colspan="2">Trade Metrics</th></tr>
                            <tr><td>Total Trades</td><td>{{ metrics.trades_count }}</td></tr>
                            <tr><td>Win Rate</td><td class="{{ 'good' if metrics.win_rate > 50 else 'neutral' if metrics.win_rate > 40 else 'bad' }}">{{ metrics.win_rate|round(2) }}%</td></tr>
                            <tr><td>Profit Factor</td><td class="{{ 'good' if metrics.profit_factor > 1.5 else 'neutral' if metrics.profit_factor > 1 else 'bad' }}">{{ metrics.profit_factor|round(2) }}</td></tr>
                            <tr><td>Expected Payoff</td><td class="{{ 'good' if metrics.expected_payoff > 0 else 'bad' }}">{{ metrics.expected_payoff|round(2) }}%</td></tr>
                            <tr><td>Avg Holding Period</td><td>{{ metrics.avg_holding_period|round(1) }} days</td></tr>
                        </table>
                    </div>
                </div>
                
                <h2>Equity Curve and Drawdown</h2>
                <div class="plot-container">
                    <img src="plots/equity_curve.png" class="plot" alt="Equity Curve and Drawdown">
                </div>
                
                <h2>Monthly Returns</h2>
                <div class="plot-container">
                    <img src="plots/monthly_returns.png" class="plot" alt="Monthly Returns">
                </div>
                
                <h2>Trade Distribution</h2>
                <div class="plot-container">
                    <img src="plots/trade_distribution.png" class="plot" alt="Trade Distribution">
                </div>
                
                <h2>Detailed Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    {% for key, value in metrics.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value|round(2) if value is number else value }}</td>
                    </tr>
                    {% endfor %}
                </table>
                
                <h2>Trade List</h2>
                <table>
                    <tr>
                        <th>Type</th>
                        <th>Date</th>
                        <th>Price</th>
                        <th>Quantity</th>
                        <th>Value</th>
                        <th>P/L</th>
                        <th>P/L %</th>
                        <th>Holding Period</th>
                    </tr>
                    {% for trade in trades %}
                    <tr>
                        <td>{{ trade.type }}</td>
                        <td>{{ trade.time }}</td>
                        <td>{{ trade.price|round(2) }}</td>
                        <td>{{ trade.quantity|round(4) }}</td>
                        <td>{{ trade.value|round(2) }}</td>
                        <td class="{{ 'good' if trade.profit_loss > 0 else 'bad' if 'profit_loss' in trade else '' }}">
                            {{ trade.profit_loss|round(2) if 'profit_loss' in trade else '-' }}
                        </td>
                        <td class="{{ 'good' if trade.profit_loss_pct > 0 else 'bad' if 'profit_loss_pct' in trade else '' }}">
                            {{ trade.profit_loss_pct|round(2) if 'profit_loss_pct' in trade else '-' }}%
                        </td>
                        <td>{{ trade.holding_period|round(1) if 'holding_period' in trade else '-' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </body>
            </html>
            """
            
            # Create Jinja2 template and render
            template = jinja2.Template(template_str)
            html_content = template.render(
                strategy_name=strategy_name,
                metrics=metrics,
                trades=trades,
                generation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Write HTML report
            report_path = os.path.join(output_dir, f"{strategy_name.replace(' ', '_')}_report.html")
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Performance report generated at {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return "" 