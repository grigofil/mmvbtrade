"""
Module for interacting with BCS API
"""
import logging
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class BCSAPI:
    """
    Client for BCS API
    """
    
    API_URL = "https://api.bcs.ru"  # This is a placeholder, replace with actual API URL
    
    def __init__(self, client_id: str, client_secret: str, access_token: Optional[str] = None):
        """
        Initialize BCS API client
        
        Args:
            client_id: Client ID from BCS
            client_secret: Client secret from BCS
            access_token: Optional access token if already authenticated
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.session = requests.Session()
        
        if access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            })
        
    def authenticate(self) -> bool:
        """
        Authenticate with BCS API
        
        Returns:
            True if authentication was successful
        """
        try:
            auth_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            
            response = requests.post(f"{self.API_URL}/auth/token", json=auth_data)
            response.raise_for_status()
            
            auth_response = response.json()
            self.access_token = auth_response.get("access_token")
            
            if self.access_token:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                })
                return True
            return False
        
        except requests.exceptions.RequestException as e:
            logger.error(f"BCS authentication error: {e}")
            return False
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to BCS API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.API_URL}/{endpoint}"
        try:
            response = self.session.request(method=method, url=url, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"BCS API request error: {e}")
            # If the error is due to expired token, try to authenticate again
            if response.status_code == 401:
                logger.info("Trying to re-authenticate...")
                if self.authenticate():
                    return self._request(method, endpoint, params, data)
            raise
    
    def get_accounts(self) -> List[Dict]:
        """
        Get user accounts
        
        Returns:
            List of accounts
        """
        response = self._request("GET", "accounts")
        return response.get("accounts", [])
    
    def get_portfolio(self, account_id: str) -> Dict:
        """
        Get portfolio for specified account
        
        Args:
            account_id: Account identifier
            
        Returns:
            Portfolio data
        """
        response = self._request("GET", f"portfolio/{account_id}")
        return response
    
    def get_market_instruments(self, instrument_type: str = "shares") -> List[Dict]:
        """
        Get market instruments by type
        
        Args:
            instrument_type: Type of instrument (shares, bonds, etfs)
            
        Returns:
            List of instruments
        """
        response = self._request("GET", f"market/{instrument_type}")
        return response.get("instruments", [])
    
    def place_order(self, account_id: str, instrument_id: str, quantity: int,
                   direction: str, order_type: str = "limit", price: float = None) -> Dict:
        """
        Place a new order
        
        Args:
            account_id: Account identifier
            instrument_id: Instrument identifier
            quantity: Number of securities
            direction: Order direction (buy or sell)
            order_type: Order type (limit or market)
            price: Order price (required for limit orders)
            
        Returns:
            Order data
        """
        data = {
            "accountId": account_id,
            "instrumentId": instrument_id,
            "quantity": quantity,
            "direction": direction,
            "orderType": order_type
        }
        
        if order_type.lower() == "limit" and price is not None:
            data["price"] = price
        
        response = self._request("POST", "orders", data=data)
        return response
    
    def get_candles(self, instrument_id: str, from_date: datetime, to_date: datetime, 
                    interval: str = "1d") -> List[Dict]:
        """
        Get candles for instrument
        
        Args:
            instrument_id: Instrument identifier
            from_date: Start date
            to_date: End date
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)
            
        Returns:
            List of candles
        """
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "interval": interval
        }
        
        response = self._request("GET", f"market/candles/{instrument_id}", params=params)
        return response.get("candles", []) 