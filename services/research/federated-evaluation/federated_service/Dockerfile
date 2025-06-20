FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY research/federated-evaluation/federated_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory from services level
COPY shared/ ./shared/

# Copy application code
COPY research/federated-evaluation/federated_service/app/ ./app/

# Set Python path to include shared modules
ENV PYTHONPATH=/app/services/shared:/app:$PYTHONPATH

# Expose port for federated evaluation service
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006", "--reload"]
