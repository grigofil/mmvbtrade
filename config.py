import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """
    Configuration class for MMV Trading Bot
    Loads settings from environment variables with fallbacks to defaults
    """
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'MMV Trading Bot')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_change_in_production')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').lower()
    LOGS_DIR = os.getenv('LOGS_DIR', 'logs')
    
    # Server Settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    WORKERS = int(os.getenv('WORKERS', 4))
    
    # Database Settings
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    DB_PATH = os.getenv('DB_PATH', 'app/database/trading.db')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'mmvtrade')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Construct Database URI
    @property
    def DATABASE_URI(self):
        if self.DB_TYPE == 'sqlite':
            return f"sqlite:///{self.DB_PATH}"
        elif self.DB_TYPE == 'mysql':
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == 'postgresql':
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            raise ValueError(f"Unsupported database type: {self.DB_TYPE}")
    
    # Exchange API Keys
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() in ('true', '1', 't')
    
    COINBASE_API_KEY = os.getenv('COINBASE_API_KEY', '')
    COINBASE_API_SECRET = os.getenv('COINBASE_API_SECRET', '')
    COINBASE_PASSPHRASE = os.getenv('COINBASE_PASSPHRASE', '')
    
    # Default Trading Settings
    DEFAULT_TRADING_PAIR = os.getenv('DEFAULT_TRADING_PAIR', 'BTC-USDT')
    DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1h')
    DEFAULT_STRATEGY = os.getenv('DEFAULT_STRATEGY', 'moving_average')
    
    # Email Notifications
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() in ('true', '1', 't')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
    
    # Telegram Notifications
    ENABLE_TELEGRAM_NOTIFICATIONS = os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'False').lower() in ('true', '1', 't')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Redis Cache
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Backtesting Settings
    BACKTEST_START_DATE = os.getenv('BACKTEST_START_DATE', '2023-01-01')
    BACKTEST_END_DATE = os.getenv('BACKTEST_END_DATE', '2023-12-31')
    BACKTEST_INITIAL_CAPITAL = float(os.getenv('BACKTEST_INITIAL_CAPITAL', 10000))
    
    @classmethod
    def get_all_settings(cls):
        """Return all configuration settings as a dictionary"""
        settings = {}
        for key in dir(cls):
            if key.isupper() and not key.startswith('_'):
                value = getattr(cls, key)
                if not callable(value):
                    settings[key] = value
        return settings

    @classmethod
    def validate_config(cls):
        """Validate critical configuration settings"""
        errors = []
        
        # Check for required API keys if in production mode
        if not cls.DEBUG and not cls.BINANCE_TESTNET:
            if not cls.BINANCE_API_KEY or not cls.BINANCE_API_SECRET:
                errors.append("Missing Binance API credentials for production mode")
        
        # Check for secret key in production
        if not cls.DEBUG and cls.SECRET_KEY == 'default_secret_key_change_in_production':
            errors.append("Default SECRET_KEY used in production mode. Please change it.")
        
        # Check for notification settings
        if cls.ENABLE_EMAIL_NOTIFICATIONS:
            if not cls.SMTP_USERNAME or not cls.SMTP_PASSWORD or not cls.NOTIFICATION_EMAIL:
                errors.append("Email notifications enabled but credentials are missing")
        
        if cls.ENABLE_TELEGRAM_NOTIFICATIONS:
            if not cls.TELEGRAM_BOT_TOKEN or not cls.TELEGRAM_CHAT_ID:
                errors.append("Telegram notifications enabled but credentials are missing")
        
        # Report errors if any
        if errors:
            print("Configuration errors detected:", file=sys.stderr)
            for error in errors:
                print(f" - {error}", file=sys.stderr)
            print("Please fix these issues or set DEBUG=True for development mode.", file=sys.stderr)
            return False
            
        return True

# Create config instance
config = Config()

# Validate configuration when imported
if not config.validate_config() and not config.DEBUG:
    print("WARNING: Running with invalid configuration.", file=sys.stderr) 