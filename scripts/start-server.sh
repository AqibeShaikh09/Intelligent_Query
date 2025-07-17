#!/bin/bash
# Startup script for PDF Q&A Server

echo "🚀 Starting PDF Q&A Server..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one with your OpenRouter API key."
    echo "You can copy .env.example to .env and fill in your API key."
    exit 1
fi

# Start the application
echo "🔧 Starting Docker containers..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for application to be ready..."
sleep 10

# Check if container is healthy
if docker-compose ps | grep -q "healthy"; then
    echo "✅ Server is running successfully!"
    echo "🌐 Open your browser and go to: http://localhost:5000"
    echo ""
    echo "📋 Server Management Commands:"
    echo "  Stop server:    docker-compose down"
    echo "  View logs:      docker-compose logs -f"
    echo "  Restart:        docker-compose restart"
else
    echo "⚠️  Server started but health check pending..."
    echo "🌐 Try opening: http://localhost:5000"
    echo "📋 Check logs with: docker-compose logs -f"
fi
