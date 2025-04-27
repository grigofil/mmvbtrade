#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p data

# Check if we should run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -m app.database.migrations
fi

# Check which command to run
if [ "$1" = "api" ]; then
    echo "Starting API server..."
    exec gunicorn --bind 0.0.0.0:5000 --workers ${WORKERS:-4} --timeout 120 app.web.app:app
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
    exec flask --app app.web.app:app run --host=0.0.0.0 --port=5000 --debug
fi 