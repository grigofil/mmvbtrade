# Docker Setup for mmvbtrade

This document describes how to use Docker to run the trading bot application.

## Prerequisites

- Docker installed on your machine. [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose installed on your machine. [Install Docker Compose](https://docs.docker.com/compose/install/)

## Configuration

Before running the application, you need to set up your configuration:

1. Create a `.env` file in the root of the project with your API credentials and configuration:

```
# Broker API credentials
TINKOFF_TOKEN=your_tinkoff_token
TINKOFF_ACCOUNT=your_tinkoff_account
BCS_TOKEN=your_bcs_token
BCS_ACCOUNT=your_bcs_account

# Database configuration
DATABASE_URL=sqlite:///data/trading.db

# Web interface configuration
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# Redis configuration (default values for docker-compose setup)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
```

2. Optionally, you can modify `config.py` for additional settings.

## Building and Running with Docker

### Build the Docker Image

```bash
docker build -t mmvtrade:latest .
```

### Run the Application with Docker Compose

The simplest way to run the entire application:

```bash
docker-compose up -d
```

This will start all services:
- API server (web interface)
- Worker (background processing)
- Scheduler (periodic tasks)
- Redis (message broker and caching)

### Check the Logs

```bash
# Check logs for a specific service
docker-compose logs -f api

# Check logs for all services
docker-compose logs -f
```

### Stop the Application

```bash
docker-compose down
```

## Running Individual Services

If you prefer to run specific services independently:

### API Server Only

```bash
docker run -d --name mmvtrade-api \
  -p 5000:5000 \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  mmvtrade:latest api
```

### Worker Only

```bash
docker run -d --name mmvtrade-worker \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  mmvtrade:latest worker
```

### Run a Backtest

```bash
docker run --rm \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  mmvtrade:latest backtest
```

## Development Mode

For development, you can run the application with hot reloading:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This requires creating a `docker-compose.dev.yml` file with appropriate development settings.

## Volume Management

The application uses the following volumes:

- `./logs`: Contains all application logs
- `./data`: Stores databases, cached data, and other persistent data
- `redis_data`: Persists Redis data between container restarts

You can access these directly from your host machine.

## Environment Variables

All configuration is done through environment variables. The most important ones are:

| Variable | Description | Default |
|----------|-------------|---------|
| TINKOFF_TOKEN | API token for Tinkoff broker | |
| BCS_TOKEN | API token for BCS broker | |
| DATABASE_URL | Database connection URL | sqlite:///data/trading.db |
| LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| REDIS_HOST | Redis hostname | redis |
| REDIS_PORT | Redis port | 6379 |

## Troubleshooting

### Cannot Connect to Broker API

If you have connection issues with broker APIs:
1. Check if your API tokens are valid
2. Ensure your network allows connections to the broker services
3. Check the logs for more detailed error messages

### Container Won't Start

1. Check if the required environment variables are set
2. Ensure the ports are not already in use
3. Verify the volumes have proper permissions

### Out of Memory Errors

If your container runs out of memory, you can limit resource usage:

```bash
docker-compose up -d --memory=2g api worker scheduler
```

## Security Considerations

- Never hardcode API tokens in the Dockerfile or source code
- Always use environment variables or mounted config files for sensitive information
- Run containers with the least privileges necessary
- Regularly update the base images to get security patches 