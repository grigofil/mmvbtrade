"""
Main entry point for the trading bot application
"""
import os
import logging
import argparse
from datetime import datetime

from app.brokers.tinkoff import TinkoffAPI
from app.brokers.bcs import BCSAPI
from app.strategies import StrategyFactory
from app.risk_management.risk_manager import RiskManager
from app.logging.trade_logger import TradeLogger
from app.web.server import WebServer

# Configure logging
def configure_logging(log_level="INFO"):
    """Configure logging for the application"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = log_level_map.get(log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels for some noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level {log_level}")

def main():
    """Main entry point for the application"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Trading Bot for BCS and Tinkoff')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind web server to')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port for web server')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode for web server')
    
    # Add broker API credentials as command-line arguments
    parser.add_argument('--tinkoff-token', type=str, default=os.environ.get('TINKOFF_TOKEN', ''),
                        help='Tinkoff Investments API token')
    parser.add_argument('--bcs-client-id', type=str, default=os.environ.get('BCS_CLIENT_ID', ''),
                        help='BCS API client ID')
    parser.add_argument('--bcs-client-secret', type=str, default=os.environ.get('BCS_CLIENT_SECRET', ''),
                        help='BCS API client secret')
    
    # Add strategy configuration
    parser.add_argument('--strategy', type=str, default='moving_average',
                        choices=list(StrategyFactory.STRATEGY_REGISTRY.keys()),
                        help='Trading strategy to use')
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting trading bot application")
    
    # Initialize broker API clients
    brokers = {}
    if args.tinkoff_token:
        try:
            tinkoff_api = TinkoffAPI(token=args.tinkoff_token)
            brokers['tinkoff'] = tinkoff_api
            logger.info("Initialized Tinkoff API client")
        except Exception as e:
            logger.error(f"Failed to initialize Tinkoff API client: {e}")
    else:
        logger.warning("Tinkoff API token not provided, Tinkoff broker will not be available")
    
    if args.bcs_client_id and args.bcs_client_secret:
        try:
            bcs_api = BCSAPI(client_id=args.bcs_client_id, client_secret=args.bcs_client_secret)
            # Authenticate
            if bcs_api.authenticate():
                brokers['bcs'] = bcs_api
                logger.info("Initialized BCS API client")
            else:
                logger.error("Failed to authenticate with BCS API")
        except Exception as e:
            logger.error(f"Failed to initialize BCS API client: {e}")
    else:
        logger.warning("BCS API credentials not provided, BCS broker will not be available")
    
    # Initialize strategies using factory
    strategies = {}
    
    # Add moving average strategy
    moving_avg_strategy = StrategyFactory.create_strategy('moving_average', 
                                                        fast_period=10, 
                                                        slow_period=30)
    if moving_avg_strategy:
        strategies['moving_average'] = moving_avg_strategy
    
    # Add mean reversion strategy
    mean_reversion_strategy = StrategyFactory.create_strategy('mean_reversion',
                                                            lookback_period=20,
                                                            std_dev=2.0,
                                                            rsi_period=14)
    if mean_reversion_strategy:
        strategies['mean_reversion'] = mean_reversion_strategy
    
    # Initialize risk manager
    risk_manager = RiskManager(
        max_position_size_pct=0.05,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        max_drawdown_pct=0.1,
        daily_loss_limit_pct=0.03
    )
    
    # Initialize trade logger
    trade_logger = TradeLogger(log_dir="logs")
    
    # Initialize web server
    web_server = WebServer(
        host=args.host,
        port=args.port,
        template_folder="app/web/templates",
        static_folder="app/web/static"
    )
    
    # Register components with web server
    for name, broker in brokers.items():
        web_server.register_broker(name, broker)
    
    for name, strategy in strategies.items():
        web_server.register_strategy(name, strategy)
    
    web_server.register_risk_manager(risk_manager)
    web_server.register_trade_logger(trade_logger)
    
    # Log available strategies
    available_strategies = StrategyFactory.get_available_strategies()
    logger.info(f"Available strategies: {len(available_strategies)}")
    for strategy in available_strategies:
        logger.info(f"  - {strategy['id']}: {strategy['name']} - {strategy['description']}")
    
    # Run web server
    logger.info(f"Starting web server on {args.host}:{args.port}")
    web_server.run(debug=args.debug)

if __name__ == "__main__":
    main() 