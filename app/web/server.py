"""
Web server implementation for trading bot management interface
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory

from app.strategies import StrategyFactory, Backtest

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
        
        # Store active trading sessions
        self.active_sessions = {}
        self.next_session_id = 1
        
        logger.info(f"Initialized WebServer on {host}:{port}")
    
    def _setup_routes(self):
        """Set up web server routes"""
        
        # Main dashboard
        @self.app.route('/')
        def index():
            return render_template('index.html')
            
        # Dashboard page
        @self.app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html', 
                                  portfolio_value=10000,
                                  portfolio_change=2.5,
                                  active_sessions=2,
                                  total_sessions=5,
                                  trades_today=12,
                                  last_trade_time="2 hours ago",
                                  profit_percentage=15.8,
                                  profit_amount=1580,
                                  period="This Month")
                                  
        # Trading sessions page
        @self.app.route('/sessions')
        def sessions():
            return render_template('dashboard.html')  # Placeholder - create sessions.html
            
        # Strategies page
        @self.app.route('/strategies')
        def strategies():
            return render_template('dashboard.html')  # Placeholder - create strategies.html
            
        # Backtesting page
        @self.app.route('/backtest')
        def backtest():
            return render_template('backtest.html')
            
        # Markets page
        @self.app.route('/markets')
        def markets():
            return render_template('dashboard.html')  # Placeholder - create markets.html
            
        # Reports page
        @self.app.route('/reports')
        def reports():
            return render_template('dashboard.html')  # Placeholder - create reports.html
            
        # Settings page
        @self.app.route('/settings')
        def settings():
            return render_template('dashboard.html')  # Placeholder - create settings.html
        
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
            # Use the StrategyFactory to get available strategies
            available_strategies = StrategyFactory.get_available_strategies()
            
            # Add additional information from registered strategies
            for strategy_info in available_strategies:
                strategy_id = strategy_info['id']
                if strategy_id in self.strategies:
                    strategy = self.strategies[strategy_id]
                    strategy_info.update({
                        'parameters': strategy.get_strategy_info().get('parameters', {}),
                        'active': True
                    })
                else:
                    # Get default parameters from factory
                    strategy_info['parameters'] = StrategyFactory.get_strategy_parameters(strategy_id)
                    strategy_info['active'] = False
            
            return jsonify(available_strategies)
        
        # API endpoint for strategy details
        @self.app.route('/api/strategies/<strategy_id>', methods=['GET'])
        def get_strategy_details(strategy_id):
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
                return jsonify(strategy.get_strategy_info())
            elif strategy_id in StrategyFactory.STRATEGY_REGISTRY:
                # Create a temporary instance to get info
                temp_strategy = StrategyFactory.create_strategy(strategy_id)
                if temp_strategy:
                    return jsonify(temp_strategy.get_strategy_info())
            
            return jsonify({"error": f"Strategy {strategy_id} not found"}), 404
        
        # API endpoint for market instruments
        @self.app.route('/api/instruments', methods=['GET'])
        def get_instruments():
            # Get broker parameter (optional)
            broker_name = request.args.get('broker')
            
            instruments = []
            if broker_name and broker_name in self.brokers:
                # Get instruments from specific broker
                try:
                    broker = self.brokers[broker_name]
                    for instrument_type in ['Stock', 'Bond', 'ETF', 'Currency']:
                        instruments.extend(broker.get_market_instruments(instrument_type))
                except Exception as e:
                    logger.error(f"Error getting instruments from {broker_name}: {e}")
            else:
                # Get instruments from all brokers
                for broker_name, broker in self.brokers.items():
                    try:
                        for instrument_type in ['Stock', 'Bond', 'ETF', 'Currency']:
                            broker_instruments = broker.get_market_instruments(instrument_type)
                            for instrument in broker_instruments:
                                instrument['broker'] = broker_name
                                instruments.append(instrument)
                    except Exception as e:
                        logger.error(f"Error getting instruments from {broker_name}: {e}")
            
            return jsonify(instruments)
            
        # API endpoint for running backtest
        @self.app.route('/api/backtest/run', methods=['POST'])
        def run_backtest():
            data = request.json
            
            # Validate request
            required_fields = ['strategy_id', 'instrument_id', 'start_date', 'end_date', 'timeframe']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Parse dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            # Create strategy
            strategy_id = data['strategy_id']
            strategy_params = data.get('strategy_params', {})
            risk_params = data.get('risk_params', {})
            
            strategy = StrategyFactory.create_strategy(
                strategy_id=strategy_id,
                risk_params=risk_params,
                **strategy_params
            )
            
            if not strategy:
                return jsonify({"error": f"Failed to create strategy: {strategy_id}"}), 400
            
            # Get historical data for the specified instrument
            instrument_id = data['instrument_id']
            timeframe = data['timeframe']
            
            # Find broker that has this instrument
            broker = None
            instrument_data = None
            
            for broker_name, broker_instance in self.brokers.items():
                try:
                    # Try to get instrument details
                    instruments = broker_instance.get_market_instruments()
                    for instr in instruments:
                        if instr.get('figi') == instrument_id or instr.get('id') == instrument_id:
                            broker = broker_instance
                            instrument_data = instr
                            break
                except Exception as e:
                    logger.warning(f"Error checking instrument in {broker_name}: {e}")
                
                if broker:
                    break
            
            if not broker or not instrument_data:
                return jsonify({"error": f"Instrument {instrument_id} not found in any broker"}), 404
            
            try:
                # Get historical candles
                candles = broker.get_candles(
                    figi=instrument_id,
                    from_date=start_date,
                    to_date=end_date,
                    interval=timeframe
                )
                
                if not candles or len(candles) < strategy.get_required_candles_count():
                    return jsonify({
                        "error": f"Not enough historical data. Need at least {strategy.get_required_candles_count()} candles, got {len(candles) if candles else 0}"
                    }), 400
                
                # Create backtest instance
                initial_capital = data.get('initial_capital', 10000.0)
                commission_pct = data.get('commission_pct', 0.001)
                slippage_pct = data.get('slippage_pct', 0.0005)
                
                backtest = Backtest(
                    strategy=strategy,
                    initial_capital=initial_capital,
                    commission_pct=commission_pct,
                    slippage_pct=slippage_pct
                )
                
                # Run backtest
                backtest_results = backtest.run(candles)
                
                # Check if optimization is requested
                if data.get('optimize', False):
                    # Define parameter ranges for optimization
                    param_ranges = {}
                    
                    if 'fast_period' in strategy_params:
                        param_ranges['fast_period'] = list(range(5, 31, 5))
                    
                    if 'slow_period' in strategy_params:
                        param_ranges['slow_period'] = list(range(20, 101, 10))
                    
                    if param_ranges:
                        # Run optimization
                        optimization_results = backtest.optimize_strategy(
                            candles=candles,
                            param_ranges=param_ranges,
                            target_metric='sharpe_ratio'
                        )
                        
                        # Add optimization results to backtest results
                        backtest_results['optimization'] = optimization_results
                
                # Calculate performance metrics
                metrics = backtest.calculate_performance_metrics()
                backtest_results.update(metrics)
                
                return jsonify(backtest_results)
                
            except Exception as e:
                logger.error(f"Error running backtest: {e}")
                return jsonify({"error": f"Error running backtest: {str(e)}"}), 500
        
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
            
            strategy_id = data['strategy']
            
            # Get or create strategy
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
            else:
                # Create new strategy instance
                strategy_params = data.get('strategy_params', {})
                risk_params = data.get('risk_params', {})
                
                strategy = StrategyFactory.create_strategy(
                    strategy_id=strategy_id,
                    risk_params=risk_params,
                    **strategy_params
                )
                
                if not strategy:
                    return jsonify({"error": f"Failed to create strategy: {strategy_id}"}), 400
            
            # Create new session
            session_id = str(self.next_session_id)
            self.next_session_id += 1
            
            session = {
                'id': session_id,
                'broker': data['broker'],
                'account_id': data['account_id'],
                'strategy': strategy_id,
                'instruments': data['instruments'],
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.active_sessions[session_id] = session
            
            # TODO: Start actual trading thread/process for this session
            
            return jsonify({
                'session_id': session_id,
                'status': 'active',
                'message': 'Trading session started successfully'
            })
        
        # API endpoint for stopping a trading session
        @self.app.route('/api/trading_session/stop', methods=['POST'])
        def stop_trading_session():
            data = request.json
            
            if 'session_id' not in data:
                return jsonify({"error": "Missing session_id parameter"}), 400
            
            session_id = data['session_id']
            
            if session_id not in self.active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            # Update session status
            self.active_sessions[session_id]['status'] = 'stopped'
            self.active_sessions[session_id]['updated_at'] = datetime.now().isoformat()
            
            # TODO: Stop actual trading thread/process for this session
            
            return jsonify({
                'session_id': session_id,
                'status': 'stopped',
                'message': 'Trading session stopped successfully'
            })
        
        # API endpoint for active trading sessions
        @self.app.route('/api/trading_sessions', methods=['GET'])
        def get_trading_sessions():
            # Convert sessions dict to list
            sessions = list(self.active_sessions.values())
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x['created_at'], reverse=True)
            
            return jsonify(sessions)
    
    def register_broker(self, name: str, broker_instance: Any):
        """
        Register a broker instance
        
        Args:
            name: Broker name
            broker_instance: Broker instance
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
        Register a risk manager instance
        
        Args:
            risk_manager: Risk manager instance
        """
        self.risk_manager = risk_manager
        logger.info(f"Registered risk manager")
    
    def register_trade_logger(self, trade_logger: Any):
        """
        Register a trade logger instance
        
        Args:
            trade_logger: Trade logger instance
        """
        self.trade_logger = trade_logger
        logger.info(f"Registered trade logger")
    
    def run(self, debug: bool = False):
        """
        Run the web server
        
        Args:
            debug: Enable debug mode
        """
        logger.info(f"Starting web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug) 