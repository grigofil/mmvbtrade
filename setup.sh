#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}    MMV Trading Bot - Development Setup    ${NC}"
echo -e "${BLUE}===============================================${NC}"

# Определение операционной системы
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    OS="unknown"
fi

echo -e "${YELLOW}Detected OS: $OS${NC}"

# Проверка Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

# Проверка минимальной версии Python
if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc) -eq 0 ]]; then
    echo -e "${RED}Python version must be 3.8 or higher. Please upgrade your Python.${NC}"
    exit 1
fi

# Создание виртуального окружения
echo -e "${YELLOW}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}Created virtual environment.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Активация виртуального окружения в зависимости от ОС
if [ "$OS" == "windows" ]; then
    echo -e "${YELLOW}Activating virtual environment on Windows...${NC}"
    source venv/Scripts/activate || . venv/Scripts/activate
else
    echo -e "${YELLOW}Activating virtual environment on Unix-like OS...${NC}"
    source venv/bin/activate || . venv/bin/activate
fi

# Обновление pip
echo -e "${YELLOW}Upgrading pip...${NC}"
$PYTHON_CMD -m pip install --upgrade pip

# Установка зависимостей
echo -e "${YELLOW}Installing dependencies...${NC}"
$PYTHON_CMD -m pip install -r requirements.txt

# Проверка наличия ta-lib (опционально)
echo -e "${YELLOW}Checking for ta-lib...${NC}"
if $PYTHON_CMD -c "import talib" &>/dev/null; then
    echo -e "${GREEN}ta-lib already installed.${NC}"
else
    echo -e "${YELLOW}TA-Lib not found. This is optional but recommended for technical analysis.${NC}"
    if [ "$OS" == "linux" ]; then
        echo -e "Install on Linux with: ${BLUE}sudo apt-get install build-essential ta-lib${NC}"
    elif [ "$OS" == "macos" ]; then
        echo -e "Install on macOS with: ${BLUE}brew install ta-lib${NC}"
    elif [ "$OS" == "windows" ]; then
        echo -e "For Windows, download from: ${BLUE}https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib${NC}"
    fi
    echo -e "After installing the system library, run: ${BLUE}pip install ta-lib${NC}"
fi

# Создание .env из примера, если не существует
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please update it with your API keys and settings.${NC}"
fi

# Создание структуры директорий
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p logs data app/database

# Финальные инструкции
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To activate the virtual environment:${NC}"
if [ "$OS" == "windows" ]; then
    echo -e "${BLUE}   source venv/Scripts/activate${NC} or ${BLUE}venv\\Scripts\\activate.bat${NC}"
else
    echo -e "${BLUE}   source venv/bin/activate${NC}"
fi
echo -e "${YELLOW}To run the application:${NC}"
echo -e "${BLUE}   python run.py${NC}"
echo -e "${YELLOW}Don't forget to update your .env file with broker API keys!${NC}"
echo -e "${BLUE}===============================================${NC}" 