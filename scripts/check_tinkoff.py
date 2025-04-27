#!/usr/bin/env python
"""
Script to check connection to Tinkoff API
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настраиваем базовое логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Загружаем переменные окружения из .env файла
load_dotenv()

# Импортируем TinkoffAPI
from app.brokers.tinkoff import TinkoffAPI

def check_tinkoff_api():
    """
    Check connection to Tinkoff API and retrieve accounts
    """
    # Получаем токен из переменных окружения
    token = os.environ.get('TINKOFF_TOKEN')
    use_sandbox = os.environ.get('TINKOFF_SANDBOX', 'false').lower() == 'true'
    
    if not token:
        print("ERROR: TINKOFF_TOKEN environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        print("Example: TINKOFF_TOKEN=t.ABCDEF1234567890")
        return False
    
    print(f"Using Tinkoff API {'SANDBOX' if use_sandbox else 'PRODUCTION'} mode")
    print(f"Token prefix: {token[:4]}{'*' * 16}")
    
    try:
        # Инициализируем API клиент
        api = TinkoffAPI(token=token, use_sandbox=use_sandbox)
        
        # Получаем список счетов
        accounts = api.get_accounts()
        
        if accounts:
            print(f"SUCCESS: Found {len(accounts)} accounts:")
            for idx, account in enumerate(accounts):
                print(f"  {idx+1}. {account.get('brokerAccountType')}: {account.get('brokerAccountId')}")
            return True
        else:
            print("WARNING: No accounts found. Make sure you have granted access to your accounts when creating the token.")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to connect to Tinkoff API: {e}")
        return False
        
if __name__ == "__main__":
    print("Checking Tinkoff API connection...")
    success = check_tinkoff_api()
    sys.exit(0 if success else 1) 