#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p data

# Initialize logging
echo "Initializing logging..."
LOG_LEVEL=${LOG_LEVEL:-INFO}
LOG_DIR=${LOG_DIR:-logs}

# Check if we should run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -m app.database.migrations
fi

# Check which command to run
if [ "$1" = "api" ]; then
    echo "Starting API server..."
    exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WORKERS:-4} --timeout 120 app.web.app:app
elif [ "$1" = "worker" ]; then
    echo "Starting background worker..."
    exec python -m app.worker.main
elif [ "$1" = "backtest" ]; then
    echo "Running backtesting..."
    exec python -m app.strategies.backtest
elif [ "$1" = "scheduler" ]; then
    echo "Starting scheduler..."
    exec python -m app.scheduler.main
elif [ "$1" = "shell" ]; then
    echo "Starting interactive shell..."
    exec python -m app.cli.shell
else
    echo "Starting development server..."
    if [ "$DEBUG" = "true" ]; then
        exec flask --app app.web.app:app run --host=${HOST:-0.0.0.0} --port=${PORT:-5000} --debug
    else
        exec flask --app app.web.app:app run --host=${HOST:-0.0.0.0} --port=${PORT:-5000}
    fi
fi 