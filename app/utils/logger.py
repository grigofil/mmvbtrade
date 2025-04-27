import os
import logging
from logging.handlers import RotatingFileHandler
import datetime
import sys

class Logger:
    """
    Logger utility for MMV Trading Bot
    Handles logging to both console and file with different log levels
    """
    
    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    def __init__(self, name="mmvbot", log_level="info", log_dir="logs"):
        """
        Initialize logger with name, level and directory
        
        Args:
            name (str): Logger name
            log_level (str): Log level (debug, info, warning, error, critical)
            log_dir (str): Directory to store log files
        """
        self.name = name
        self.log_level = self.LOG_LEVELS.get(log_level.lower(), logging.INFO)
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Set up logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        self.logger.handlers = []  # Clear existing handlers
        
        # Log format
        self.log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler
        self._setup_console_handler()
        
        # Add file handlers
        self._setup_file_handlers()
    
    def _setup_console_handler(self):
        """Set up console handler for logging"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.log_format)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handlers(self):
        """Set up file handlers for different log levels"""
        # Common log file for all levels
        common_log_file = os.path.join(self.log_dir, f"{self.name}.log")
        common_handler = RotatingFileHandler(
            common_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        common_handler.setLevel(self.log_level)
        common_handler.setFormatter(self.log_format)
        self.logger.addHandler(common_handler)
        
        # Error log file (error and critical only)
        error_log_file = os.path.join(self.log_dir, f"{self.name}_error.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.log_format)
        self.logger.addHandler(error_handler)
        
        # Daily log file with date in name
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        daily_log_file = os.path.join(self.log_dir, f"{self.name}_{today}.log")
        daily_handler = logging.FileHandler(daily_log_file)
        daily_handler.setLevel(self.log_level)
        daily_handler.setFormatter(self.log_format)
        self.logger.addHandler(daily_handler)
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=True):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def exception(self, message):
        """Log exception message"""
        self.logger.exception(message)

# Create a default logger instance
default_logger = Logger()

# Helper functions to use default logger
def debug(message):
    default_logger.debug(message)

def info(message):
    default_logger.info(message)

def warning(message):
    default_logger.warning(message)

def error(message, exc_info=False):
    default_logger.error(message, exc_info=exc_info)

def critical(message, exc_info=True):
    default_logger.critical(message, exc_info=exc_info)

def exception(message):
    default_logger.exception(message)

def get_logger(name="mmvbot", log_level="info", log_dir="logs"):
    """Get a configured logger instance"""
    return Logger(name, log_level, log_dir).logger 