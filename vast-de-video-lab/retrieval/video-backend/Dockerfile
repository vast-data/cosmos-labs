# Video Reasoning Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Copy ADBC driver (assumes libadbc_driver_vastdb.so is in build context)
RUN mkdir -p /opt/adbc-driver
COPY libadbc_driver_vastdb.so /opt/adbc-driver/libadbc_driver_vastdb.so
RUN chmod 755 /opt/adbc-driver/libadbc_driver_vastdb.so

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

