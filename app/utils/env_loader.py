import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from app.utils.logger import Logger

logger = Logger(name="env_loader")

def load_env_file(env_path=None):
    """
    Load environment variables from .env file
    
    Args:
        env_path (str, optional): Path to .env file
        
    Returns:
        bool: True if .env file was loaded, False otherwise
    """
    # If no path specified, look for .env in current directory and parent directories
    if env_path is None:
        current_dir = Path.cwd()
        
        # Look in current directory
        env_path = current_dir / '.env'
        if env_path.exists():
            logger.info(f"Loading .env from {env_path}")
            load_dotenv(dotenv_path=env_path)
            return True
        
        # Look in parent directory
        env_path = current_dir.parent / '.env'
        if env_path.exists():
            logger.info(f"Loading .env from {env_path}")
            load_dotenv(dotenv_path=env_path)
            return True
        
        # Look in app directory
        env_path = current_dir / 'app' / '.env'
        if env_path.exists():
            logger.info(f"Loading .env from {env_path}")
            load_dotenv(dotenv_path=env_path)
            return True
            
        logger.warning("No .env file found. Using default environment variables.")
        return False
    else:
        # Load from specified path
        env_path = Path(env_path)
        if env_path.exists():
            logger.info(f"Loading .env from {env_path}")
            load_dotenv(dotenv_path=env_path)
            return True
        else:
            logger.error(f"Specified .env file not found: {env_path}")
            return False

def get_env_var(name, default=None, required=False):
    """
    Get environment variable with fallback to default
    
    Args:
        name (str): Environment variable name
        default (any, optional): Default value if not found
        required (bool, optional): If True, exit if variable not found
        
    Returns:
        str: Value of environment variable or default
    """
    value = os.environ.get(name, default)
    
    if value is None and required:
        logger.critical(f"Required environment variable {name} not set!")
        sys.exit(1)
        
    return value

def get_env_var_bool(name, default=False):
    """
    Get boolean environment variable
    
    Args:
        name (str): Environment variable name
        default (bool, optional): Default value if not found
        
    Returns:
        bool: Boolean value of environment variable
    """
    value = os.environ.get(name, str(default)).lower()
    return value in ('true', '1', 't', 'yes', 'y')

def get_env_var_int(name, default=0):
    """
    Get integer environment variable
    
    Args:
        name (str): Environment variable name
        default (int, optional): Default value if not found
        
    Returns:
        int: Integer value of environment variable
    """
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        logger.error(f"Environment variable {name} must be an integer, using default: {default}")
        return default

def get_env_var_float(name, default=0.0):
    """
    Get float environment variable
    
    Args:
        name (str): Environment variable name
        default (float, optional): Default value if not found
        
    Returns:
        float: Float value of environment variable
    """
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        logger.error(f"Environment variable {name} must be a float, using default: {default}")
        return default

def get_env_var_list(name, default=None, separator=','):
    """
    Get list environment variable (comma-separated by default)
    
    Args:
        name (str): Environment variable name
        default (list, optional): Default value if not found
        separator (str, optional): List item separator
        
    Returns:
        list: List from environment variable
    """
    if default is None:
        default = []
        
    value = os.environ.get(name)
    if value is None:
        return default
        
    return [item.strip() for item in value.split(separator)]

def check_required_vars(required_vars):
    """
    Check if all required environment variables are set
    
    Args:
        required_vars (list): List of required variable names
        
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    missing_vars = []
    
    for var in required_vars:
        if os.environ.get(var) is None:
            missing_vars.append(var)
            
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    return True

def print_env_summary(vars_to_show, hide_secrets=True):
    """
    Print a summary of environment variables
    
    Args:
        vars_to_show (list): List of variable names to show
        hide_secrets (bool, optional): Hide secret values
    """
    logger.info("Environment Variables Summary:")
    
    for var in vars_to_show:
        value = os.environ.get(var, '[NOT SET]')
        
        # Hide secret values
        if hide_secrets and any(secret in var.lower() for secret in ['key', 'token', 'secret', 'password', 'passphrase']):
            if value != '[NOT SET]':
                value = '********'
                
        logger.info(f"  {var}: {value}") 