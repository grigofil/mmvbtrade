#!/bin/bash
# Setup script for MMV Trading Bot

set -e

# ASCII art logo
echo "
##     ## ##     ## ##     ## ######## ########     ###    ########  ######## 
###   ### ###   ### ##     ##    ##    ##     ##   ## ##   ##     ## ##       
#### #### #### #### ##     ##    ##    ##     ##  ##   ##  ##     ## ##       
## ### ## ## ### ## ##     ##    ##    ########  ##     ## ##     ## ######   
##     ## ##     ##  ##   ##     ##    ##   ##   ######### ##     ## ##       
##     ## ##     ##   ## ##      ##    ##    ##  ##     ## ##     ## ##       
##     ## ##     ##    ###       ##    ##     ## ##     ## ########  ######## 
"
echo "MMV Trading Bot - Setup Script"
echo "============================="
echo

# Check for Python
echo "Checking Python installation..."
if command -v python3 &>/dev/null; then
    python_cmd=python3
elif command -v python &>/dev/null; then
    python_cmd=python
else
    echo "Error: Python not found. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $python_version"

# Minimum required Python version
required_version="3.8"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python $required_version or later is required."
    exit 1
fi

# Create virtual environment
echo
echo "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    $python_cmd -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p app/database

# Create .env file if it doesn't exist
echo
echo "Setting up configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ".env file created. Please edit it with your configuration."
    else
        echo "Warning: .env.example not found. Creating minimal .env file."
        cat > .env << EOL
# MMV Trading Bot - Configuration
APP_NAME=MMV Trading Bot
DEBUG=True
SECRET_KEY=development_key_change_in_production
LOG_LEVEL=info

# Database Settings
DB_TYPE=sqlite
DB_PATH=app/database/trading.db
EOL
        echo "Basic .env file created. Please edit it with your configuration."
    fi
else
    echo ".env file already exists."
fi

# Initialize database
echo
echo "Initializing database..."
$python_cmd -m app.database.migrations

# Set execute permissions for scripts
echo
echo "Setting execute permissions for scripts..."
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod +x scripts/*.sh
fi

# Final message
echo
echo "Setup complete!"
echo
echo "To start the development server, run:"
echo "  source venv/bin/activate  # Linux/Mac"
echo "  venv\\Scripts\\activate    # Windows"
echo "  python -m app.web.app"
echo
echo "To run in Docker:"
echo "  docker-compose up -d"
echo
echo "Happy trading!" 