FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
# Don't create .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Don't buffer stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${PYTHONPATH}:/app"
# Set timezone to UTC
ENV TZ=UTC

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        # Add tzdata for proper timezone handling
        tzdata \
        # For potential TA-Lib support (uncomment if needed)
        # build-essential \
        # wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Uncomment the following block if you need TA-Lib
# Install TA-Lib
# RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
#     && tar -xzf ta-lib-0.4.0-src.tar.gz \
#     && cd ta-lib/ \
#     && ./configure --prefix=/usr \
#     && make \
#     && make install \
#     && cd .. \
#     && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p logs data

# Copy scripts first for better layer caching
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh

# Copy project
COPY . .

# Run as non-root user for better security
RUN useradd -m mmvbot
RUN chown -R mmvbot:mmvbot /app
USER mmvbot

# Expose port for the web interface
EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command (can be overridden in docker-compose or docker run)
CMD ["api"] 