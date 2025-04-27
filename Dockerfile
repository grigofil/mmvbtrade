FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Set permissions
RUN chmod +x /app/scripts/*.sh

# Run as non-root user
RUN useradd -m mmvbot
RUN chown -R mmvbot:mmvbot /app
USER mmvbot

# Expose port
EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"] 