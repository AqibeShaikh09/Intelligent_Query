
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Devsidd2006"
LABEL description="Intelligent Query PDF Q&A System - AI-powered document analysis"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Copy application code
COPY src/ ./src/

# Create uploads directory with proper permissions
RUN mkdir -p uploads && \
    mkdir -p logs && \
    chmod 755 uploads logs


# Set environment variables with proper Python path
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI port
EXPOSE 3000


# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start FastAPI server for HackRx endpoint
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "3000"]


