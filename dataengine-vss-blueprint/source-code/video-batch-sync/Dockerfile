FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files from src directory
COPY src/ ./

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "web_service.py"]

