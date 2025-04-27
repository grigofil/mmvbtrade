"""
Historical data loading and management for backtesting
"""
import logging
import pandas as pd
import numpy as np
import os
import json
import csv
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime, timedelta
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class HistoricalDataLoader:
    """
    Class for loading and managing historical price data from various sources
    for backtesting trading strategies.
    """
    
    def __init__(self, data_dir: str = "data/historical"):
        """
        Initialize the historical data loader
        
        Args:
            data_dir: Directory to store/cache historical data
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Initialized HistoricalDataLoader with data directory: {data_dir}")
    
    def load_from_csv(self, file_path: str, 
                     date_format: str = "%Y-%m-%d %H:%M:%S",
                     date_column: str = "time") -> List[Dict]:
        """
        Load historical data from a CSV file
        
        Args:
            file_path: Path to the CSV file
            date_format: Format string for date parsing
            date_column: Name of the column containing dates
            
        Returns:
            List of candle dictionaries in the format required by backtest
        """
        logger.info(f"Loading historical data from CSV: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Parse dates
            df[date_column] = pd.to_datetime(df[date_column], format=date_format)
            
            # Sort by date
            df = df.sort_values(by=date_column)
            
            # Convert to candle format
            candles = []
            for _, row in df.iterrows():
                candle = {
                    'time': row[date_column].isoformat(),
                    'o': float(row['open']),
                    'h': float(row['high']),
                    'l': float(row['low']),
                    'c': float(row['close']),
                    'v': float(row['volume']) if 'volume' in row else 0
                }
                candles.append(candle)
            
            logger.info(f"Loaded {len(candles)} candles from {file_path}")
            return candles
            
        except Exception as e:
            logger.error(f"Error loading data from CSV: {e}")
            return []
    
    def load_from_json(self, file_path: str) -> List[Dict]:
        """
        Load historical data from a JSON file
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of candle dictionaries
        """
        logger.info(f"Loading historical data from JSON: {file_path}")
        
        try:
            # Read JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Ensure data is in correct format
            if isinstance(data, list):
                candles = data
            elif isinstance(data, dict) and 'candles' in data:
                candles = data['candles']
            else:
                logger.error(f"Unexpected JSON format in {file_path}")
                return []
            
            # Sort by date
            candles = sorted(candles, key=lambda x: x['time'])
            
            logger.info(f"Loaded {len(candles)} candles from {file_path}")
            return candles
            
        except Exception as e:
            logger.error(f"Error loading data from JSON: {e}")
            return []
    
    def download_from_api(self, symbol: str, interval: str, 
                         start_date: str, end_date: str,
                         api_key: Optional[str] = None,
                         provider: str = "alphavantage") -> List[Dict]:
        """
        Download historical data from a third-party API
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Candle interval (e.g., "1d", "1h", "15m")
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            api_key: API key for the data provider
            provider: Data provider name ("alphavantage", "binance", etc.)
            
        Returns:
            List of candle dictionaries
        """
        logger.info(f"Downloading {symbol} {interval} data from {provider} ({start_date} to {end_date})")
        
        # Create cache file path
        cache_file = os.path.join(self.data_dir, f"{symbol}_{interval}_{start_date}_{end_date}.json")
        
        # Check if cached data exists
        if os.path.exists(cache_file):
            logger.info(f"Loading cached data from {cache_file}")
            return self.load_from_json(cache_file)
        
        # Download based on provider
        candles = []
        
        try:
            if provider == "alphavantage":
                candles = self._download_from_alphavantage(symbol, interval, start_date, end_date, api_key)
            elif provider == "binance":
                candles = self._download_from_binance(symbol, interval, start_date, end_date)
            else:
                logger.error(f"Unsupported provider: {provider}")
                return []
            
            # Cache the data
            if candles:
                with open(cache_file, 'w') as f:
                    json.dump(candles, f)
                logger.info(f"Cached {len(candles)} candles to {cache_file}")
            
            return candles
            
        except Exception as e:
            logger.error(f"Error downloading data: {e}")
            return []
    
    def _download_from_alphavantage(self, symbol: str, interval: str, 
                                   start_date: str, end_date: str,
                                   api_key: Optional[str]) -> List[Dict]:
        """
        Download data from Alpha Vantage API
        """
        if not api_key:
            logger.error("Alpha Vantage API key is required")
            return []
        
        # Map intervals to Alpha Vantage format
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "60min",
            "1d": "daily"
        }
        
        av_interval = interval_map.get(interval, "daily")
        
        # Construct API URL
        function = "TIME_SERIES_INTRADAY" if av_interval != "daily" else "TIME_SERIES_DAILY"
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={av_interval}&apikey={api_key}&outputsize=full"
        
        # Make request
        response = requests.get(url)
        data = response.json()
        
        # Parse response
        time_series_key = f"Time Series ({av_interval})" if av_interval != "daily" else "Time Series (Daily)"
        
        if time_series_key not in data:
            logger.error(f"Error in Alpha Vantage response: {data}")
            return []
        
        time_series = data[time_series_key]
        
        # Convert to candles format
        candles = []
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S" if av_interval != "daily" else "%Y-%m-%d")
            
            if start_datetime <= date <= end_datetime:
                candle = {
                    'time': date.isoformat(),
                    'o': float(values['1. open']),
                    'h': float(values['2. high']),
                    'l': float(values['3. low']),
                    'c': float(values['4. close']),
                    'v': float(values['5. volume'])
                }
                candles.append(candle)
        
        # Sort by date
        candles = sorted(candles, key=lambda x: x['time'])
        
        return candles
    
    def _download_from_binance(self, symbol: str, interval: str, 
                             start_date: str, end_date: str) -> List[Dict]:
        """
        Download data from Binance API
        """
        # Binance API endpoint
        url = "https://api.binance.com/api/v3/klines"
        
        # Convert dates to milliseconds
        start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        end_ts = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        
        # Map intervals to Binance format
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        
        binance_interval = interval_map.get(interval, "1d")
        
        # Make request (Binance API has a limit of 1000 candles per request)
        all_candles = []
        current_start = start_ts
        
        while current_start < end_ts:
            params = {
                "symbol": symbol,
                "interval": binance_interval,
                "startTime": current_start,
                "endTime": end_ts,
                "limit": 1000
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if not isinstance(data, list):
                logger.error(f"Error in Binance response: {data}")
                break
                
            if not data:
                break
                
            # Convert to candles format
            for kline in data:
                candle = {
                    'time': datetime.fromtimestamp(kline[0] / 1000).isoformat(),
                    'o': float(kline[1]),
                    'h': float(kline[2]),
                    'l': float(kline[3]),
                    'c': float(kline[4]),
                    'v': float(kline[5])
                }
                all_candles.append(candle)
            
            # Update start time for next request
            current_start = data[-1][0] + 1
        
        # Sort by date
        all_candles = sorted(all_candles, key=lambda x: x['time'])
        
        return all_candles
    
    def resample_data(self, candles: List[Dict], target_interval: str) -> List[Dict]:
        """
        Resample candles to a different time interval
        
        Args:
            candles: List of candle data
            target_interval: Target interval (e.g., "1h", "1d")
            
        Returns:
            Resampled candles
        """
        logger.info(f"Resampling data to {target_interval} interval")
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['datetime'] = pd.to_datetime(df['time'])
        df = df.set_index('datetime')
        
        # Map target interval to pandas format
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D"
        }
        
        resample_rule = interval_map.get(target_interval, "1D")
        
        # Resample
        resampled = df.resample(resample_rule).agg({
            'o': 'first',
            'h': 'max',
            'l': 'min',
            'c': 'last',
            'v': 'sum'
        })
        
        # Reset index and convert back to candles format
        resampled = resampled.reset_index()
        
        result = []
        for _, row in resampled.iterrows():
            if pd.notna(row['o']) and pd.notna(row['c']):  # Skip incomplete candles
                candle = {
                    'time': row['datetime'].isoformat(),
                    'o': float(row['o']),
                    'h': float(row['h']),
                    'l': float(row['l']),
                    'c': float(row['c']),
                    'v': float(row['v'])
                }
                result.append(candle)
        
        logger.info(f"Resampled {len(candles)} candles to {len(result)} {target_interval} candles")
        return result
    
    def save_to_csv(self, candles: List[Dict], file_path: str) -> bool:
        """
        Save candles to a CSV file
        
        Args:
            candles: List of candle data
            file_path: Path to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            # Rename columns for clarity
            column_map = {
                'time': 'time',
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            }
            
            # Rename columns that exist
            for old, new in column_map.items():
                if old in df.columns:
                    df = df.rename(columns={old: new})
            
            # Write to CSV
            df.to_csv(file_path, index=False)
            logger.info(f"Saved {len(candles)} candles to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {e}")
            return False
    
    def save_to_json(self, candles: List[Dict], file_path: str) -> bool:
        """
        Save candles to a JSON file
        
        Args:
            candles: List of candle data
            file_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Write to JSON
            with open(file_path, 'w') as f:
                json.dump(candles, f, indent=4)
            
            logger.info(f"Saved {len(candles)} candles to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
            return False 