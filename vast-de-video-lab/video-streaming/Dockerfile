FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install yt-dlp
RUN pip install --no-cache-dir yt-dlp

# Copy application files from src directory
COPY src/ ./

# Create recordings directory
RUN mkdir -p recordings

# Make scripts executable
RUN chmod +x *.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "web_service.py"]
