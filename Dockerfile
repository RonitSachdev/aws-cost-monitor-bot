FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=1h --timeout=30s --start-period=60s --retries=3 \
    CMD python main.py --test || exit 1

# Default command
CMD ["python", "main.py", "--daemon"] 