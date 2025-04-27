"""
Web server implementation for trading bot management interface
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory

logger = logging.getLogger(__name__)

class WebServer:
    """
    Web server for trading bot management interface
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000, 
                 template_folder: str = "templates", static_folder: str = "static"):
        """
        Initialize web server
        
        Args:
            host: Host address to bind to (default: "0.0.0.0")
            port: Port number to listen on (default: 5000)
            template_folder: Folder containing HTML templates (default: "templates")
            static_folder: Folder containing static assets (default: "static")
        """
        self.host = host
        self.port = port
        self.template_folder = template_folder
        self.static_folder = static_folder
        
        # Create Flask app
        self.app = Flask(
            __name__, 
            template_folder=template_folder,
            static_folder=static_folder
        )
        
        # Set up routes
        self._setup_routes()
        
        # Store references to components
        self.brokers = {}
        self.strategies = {}
        self.risk_manager = None
        self.trade_logger = None
        
        logger.info(f"Initialized WebServer on {host}:{port}")
    
    def _setup_routes(self):
        """Set up web server routes"""
        
        # Main dashboard
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # API endpoints for broker accounts
        @self.app.route('/api/accounts', methods=['GET'])
        def get_accounts():
            accounts = []
            for broker_name, broker in self.brokers.items():
                try:
                    broker_accounts = broker.get_accounts()
                    for account in broker_accounts:
                        account['broker'] = broker_name
                        accounts.append(account)
                except Exception as e:
                    logger.error(f"Error getting accounts from {broker_name}: {e}")
            
            return jsonify(accounts)
        
        # API endpoint for portfolio data
        @self.app.route('/api/portfolio/<broker>/<account_id>', methods=['GET'])
        def get_portfolio(broker, account_id):
            if broker not in self.brokers:
                return jsonify({"error": f"Broker {broker} not found"}), 404
            
            try:
                portfolio = self.brokers[broker].get_portfolio(account_id)
                return jsonify(portfolio)
            except Exception as e:
                logger.error(f"Error getting portfolio from {broker}: {e}")
                return jsonify({"error": str(e)}), 500
        
        # API endpoint for trade history
        @self.app.route('/api/trades', methods=['GET'])
        def get_trades():
            if not self.trade_logger:
                return jsonify({"error": "Trade logger not initialized"}), 500
            
            # Parse query parameters
            instrument_id = request.args.get('instrument_id')
            days = request.args.get('days')
            
            start_date = None
            if days:
                try:
                    days = int(days)
                    start_date = datetime.now() - timedelta(days=days)
                except ValueError:
                    pass
            
            trades = self.trade_logger.get_trades(
                instrument_id=instrument_id,
                start_date=start_date
            )
            
            return jsonify(trades)
        
        # API endpoint for portfolio history
        @self.app.route('/api/portfolio_history', methods=['GET'])
        def get_portfolio_history():
            if not self.trade_logger:
                return jsonify({"error": "Trade logger not initialized"}), 500
            
            # Parse query parameters
            broker = request.args.get('broker')
            account_id = request.args.get('account_id')
            days = request.args.get('days')
            
            start_date = None
            if days:
                try:
                    days = int(days)
                    start_date = datetime.now() - timedelta(days=days)
                except ValueError:
                    pass
            
            history = self.trade_logger.get_portfolio_history(
                broker=broker,
                account_id=account_id,
                start_date=start_date
            )
            
            return jsonify(history)
        
        # API endpoint for available strategies
        @self.app.route('/api/strategies', methods=['GET'])
        def get_strategies():
            strategy_list = []
            for name, strategy in self.strategies.items():
                strategy_list.append({
                    'name': name,
                    'type': strategy.__class__.__name__
                })
            
            return jsonify(strategy_list)
        
        # API endpoint for starting a trading session
        @self.app.route('/api/trading_session/start', methods=['POST'])
        def start_trading_session():
            data = request.json
            
            # Validate request
            required_fields = ['broker', 'account_id', 'strategy', 'instruments']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Check if broker and strategy exist
            if data['broker'] not in self.brokers:
                return jsonify({"error": f"Broker {data['broker']} not found"}), 404
            
            if data['strategy'] not in self.strategies:
                return jsonify({"error": f"Strategy {data['strategy']} not found"}), 404
            
            # This would actually start a trading session in a real implementation
            # For now, just return success
            return jsonify({"status": "success", "message": "Trading session started"})
        
        # API endpoint for stopping a trading session
        @self.app.route('/api/trading_session/stop', methods=['POST'])
        def stop_trading_session():
            data = request.json
            
            # Validate request
            required_fields = ['session_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # This would actually stop a trading session in a real implementation
            # For now, just return success
            return jsonify({"status": "success", "message": "Trading session stopped"})
    
    def register_broker(self, name: str, broker_instance: Any):
        """
        Register a broker instance
        
        Args:
            name: Broker name
            broker_instance: Broker API instance
        """
        self.brokers[name] = broker_instance
        logger.info(f"Registered broker: {name}")
    
    def register_strategy(self, name: str, strategy_instance: Any):
        """
        Register a strategy instance
        
        Args:
            name: Strategy name
            strategy_instance: Strategy instance
        """
        self.strategies[name] = strategy_instance
        logger.info(f"Registered strategy: {name}")
    
    def register_risk_manager(self, risk_manager: Any):
        """
        Register the risk manager
        
        Args:
            risk_manager: Risk manager instance
        """
        self.risk_manager = risk_manager
        logger.info("Registered risk manager")
    
    def register_trade_logger(self, trade_logger: Any):
        """
        Register the trade logger
        
        Args:
            trade_logger: Trade logger instance
        """
        self.trade_logger = trade_logger
        logger.info("Registered trade logger")
    
    def run(self, debug: bool = False):
        """
        Run the web server
        
        Args:
            debug: Enable debug mode (default: False)
        """
        logger.info(f"Starting web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug) 