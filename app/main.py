"""
Main entry point for the trading bot application
"""
import argparse
import os
import logging
from datetime import datetime

# Добавляем импорт для работы с .env
from dotenv import load_dotenv

from app.brokers.tinkoff import TinkoffAPI
from app.brokers.bcs import BCSAPI
from app.strategies.factory import StrategyFactory
from app.risk_management.risk_manager import RiskManager
from app.logging import setup_logging
from app.web.server import WebServer

# Безопасная загрузка .env файла
def safe_load_dotenv():
    """
    Safely load environment variables from .env file,
    handling potential encoding issues
    """
    try:
        # Пробуем стандартный метод
        load_dotenv()
    except UnicodeDecodeError:
        # Если файл в неверной кодировке, выводим предупреждение
        print("WARNING: Could not load .env file due to encoding issues.")
        print("Create a new .env file with UTF-8 encoding using a text editor.")
        print("Using default environment variables instead.")

def main():
    """
    Main entry point for the trading bot
    """
    # Безопасно загружаем переменные окружения
    safe_load_dotenv()
    
    parser = argparse.ArgumentParser(description='Trading Bot')
    
    # Logging arguments
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set the logging level')
    
    # Server arguments
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the web server on')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server on')
    
    # Tinkoff API arguments
    parser.add_argument('--tinkoff-token', type=str, help='Tinkoff API token')
    parser.add_argument('--tinkoff-account', type=str, help='Tinkoff account ID')
    
    # BCS API arguments
    parser.add_argument('--bcs-token', type=str, help='BCS API token')
    parser.add_argument('--bcs-account', type=str, help='BCS account ID')
    
    args = parser.parse_args()
    
    # Setup logging
    # Обновленный вызов функции setup_logging с новой сигнатурой
    setup_logging(console_level=args.log_level, log_dir='logs')
    
    logger = logging.getLogger(__name__)
    logger.info("Starting trading bot...")
    
    # Initialize broker APIs
    broker_apis = {}
    
    if args.tinkoff_token and args.tinkoff_account:
        logger.info("Initializing Tinkoff API...")
        tinkoff_api = TinkoffAPI(token=args.tinkoff_token, account_id=args.tinkoff_account)
        broker_apis['tinkoff'] = tinkoff_api
    
    if args.bcs_token and args.bcs_account:
        logger.info("Initializing BCS API...")
        bcs_api = BCSAPI(token=args.bcs_token, account_id=args.bcs_account)
        broker_apis['bcs'] = bcs_api
    
    if not broker_apis:
        logger.warning("No broker APIs configured. Trading functionality will be limited.")
    
    # Initialize strategy factory
    logger.info("Initializing strategy factory...")
    strategy_factory = StrategyFactory()
    
    # Initialize risk manager
    logger.info("Initializing risk manager...")
    risk_manager = RiskManager()
    
    # Initialize web server
    logger.info(f"Starting web server on {args.host}:{args.port}...")
    server = WebServer(
        host=args.host,
        port=args.port
    )
    
    # Регистрация компонентов через соответствующие методы
    for broker_name, broker_api in broker_apis.items():
        server.register_broker(broker_name, broker_api)
    
    server.register_risk_manager(risk_manager)
    
    try:
        # Отключаем автоматическую загрузку .env внутри Flask (это уже сделано выше)
        os.environ['FLASK_SKIP_DOTENV'] = '1'
        server.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.exception("Unexpected error occurred")
    finally:
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    main() 