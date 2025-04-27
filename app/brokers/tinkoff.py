"""
Module for interacting with Tinkoff Investments API
"""
import logging
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class TinkoffAPI:
    """
    Client for Tinkoff Investments API
    """
    
    API_URL = "https://api-invest.tinkoff.ru/openapi"
    SANDBOX_URL = "https://api-invest.tinkoff.ru/openapi/sandbox"
    
    def __init__(self, token: str, use_sandbox: bool = False):
        """
        Initialize Tinkoff API client
        
        Args:
            token: API token from Tinkoff Investments
            use_sandbox: Whether to use sandbox environment
        """
        self.token = token
        self.use_sandbox = use_sandbox
        self.base_url = self.SANDBOX_URL if use_sandbox else self.API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
        logger.info(f"Initialized Tinkoff API client (Sandbox: {use_sandbox})")
        
        # Проверяем соединение сразу при инициализации
        self.check_connection()
    
    def check_connection(self) -> bool:
        """
        Check connection to Tinkoff API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            accounts = self.get_accounts()
            logger.info(f"Connection to Tinkoff API successful. Found {len(accounts)} accounts.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Tinkoff API: {e}")
            logger.debug(f"API URL: {self.base_url}, Sandbox mode: {self.use_sandbox}")
            logger.debug(f"Token prefix: {self.token[:4]}{'*' * 16}")
            return False
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to Tinkoff API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method=method, url=url, params=params, json=data)
            
            if response.status_code != 200:
                logger.error(f"API request error: {response.status_code} - {response.text}")
                
            response.raise_for_status()
            result = response.json()
            
            # Проверяем ответ API на наличие ошибок
            if result.get("status") == "Error":
                error_msg = result.get("payload", {}).get("message", "Unknown API error")
                logger.error(f"API returned error: {error_msg}")
                raise Exception(f"Tinkoff API error: {error_msg}")
                
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            # Добавляем больше информации для отладки
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response code: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            raise
    
    def get_accounts(self) -> List[Dict]:
        """
        Get user accounts
        
        Returns:
            List of accounts
        """
        try:
            response = self._request("GET", "user/accounts")
            accounts = response.get("payload", {}).get("accounts", [])
            logger.info(f"Retrieved {len(accounts)} accounts from Tinkoff API")
            return accounts
        except Exception as e:
            logger.error(f"Error retrieving accounts: {e}")
            return []
    
    def get_portfolio(self, account_id: str) -> Dict:
        """
        Get portfolio for specified account
        
        Args:
            account_id: Account identifier
            
        Returns:
            Portfolio data
        """
        response = self._request("GET", f"portfolio?brokerAccountId={account_id}")
        return response.get("payload", {})
    
    def get_market_instruments(self, instrument_type: str = "Stock") -> List[Dict]:
        """
        Get market instruments by type
        
        Args:
            instrument_type: Type of instrument (Stock, Bond, ETF, Currency)
            
        Returns:
            List of instruments
        """
        response = self._request("GET", f"market/{instrument_type}s")
        return response.get("payload", {}).get("instruments", [])
    
    def place_order(self, account_id: str, figi: str, lots: int, 
                   operation: str, order_type: str = "Limit", price: float = None) -> Dict:
        """
        Place a new order
        
        Args:
            account_id: Account identifier
            figi: Instrument FIGI
            lots: Number of lots
            operation: Operation type (Buy or Sell)
            order_type: Order type (Limit or Market)
            price: Order price (required for Limit orders)
            
        Returns:
            Order data
        """
        data = {
            "lots": lots,
            "operation": operation,
            "type": order_type
        }
        
        if order_type == "Limit" and price is not None:
            data["price"] = price
        
        response = self._request(
            "POST", 
            f"orders/limit-order?figi={figi}&brokerAccountId={account_id}",
            data=data
        )
        return response.get("payload", {})
    
    def get_candles(self, figi: str, from_date: datetime, to_date: datetime, interval: str) -> List[Dict]:
        """
        Get candles for instrument
        
        Args:
            figi: Instrument FIGI
            from_date: Start date
            to_date: End date
            interval: Candle interval (1min, 2min, 3min, 5min, 10min, 15min, 30min, hour, day, week, month)
            
        Returns:
            List of candles
        """
        params = {
            "figi": figi,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "interval": interval
        }
        
        response = self._request("GET", "market/candles", params=params)
        return response.get("payload", {}).get("candles", []) 