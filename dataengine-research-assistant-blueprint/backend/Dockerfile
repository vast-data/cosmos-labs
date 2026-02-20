# Research Assistant API - Production Dockerfile
# Multi-stage build for smaller image size
# Build context should be the backend/ directory

FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Labels
LABEL maintainer="Research Assistant Team"
LABEL version="1.0.0"
LABEL description="Research Assistant API with RAG backend integration"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (no .env file - configuration via env vars)
COPY app.py config.py models.py ./
COPY services/ ./services/
COPY api/ ./api/
COPY lib/ ./lib/

# DO NOT COPY:
# - .env (secrets should be injected via K8s secrets/configmaps)
# - __pycache__/ (not needed)
# - venv/ (using builder stage venv)
# - tests/ (not needed in production)
# - *.md (documentation)

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# Set PYTHONPATH to include current directory
ENV PYTHONPATH=/app:$PYTHONPATH
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
