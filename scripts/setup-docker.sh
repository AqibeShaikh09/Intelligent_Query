#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 PDF Q&A System - Docker Setup${NC}"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating a template...${NC}"
    cat > .env << EOL
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Application Settings
MAX_FILE_SIZE=16777216
EOL
    echo -e "${YELLOW}📝 Please update the .env file with your actual API keys before running the application.${NC}"
fi

# Create uploads directory
mkdir -p uploads

echo -e "${BLUE}🔨 Building Docker image...${NC}"

# Build the Docker image
if docker-compose build; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Starting the application...${NC}"

# Start the application
if docker-compose up -d; then
    echo -e "${GREEN}✅ Application started successfully${NC}"
    echo ""
    echo -e "${BLUE}📋 Application Details:${NC}"
    echo "  🌐 URL: http://localhost:5000"
    echo "  📊 Status: http://localhost:5000/status"
    echo ""
    echo -e "${BLUE}🛠️  Useful Commands:${NC}"
    echo "  📖 View logs: docker-compose logs -f"
    echo "  🔄 Restart: docker-compose restart"
    echo "  🛑 Stop: docker-compose down"
    echo "  🏗️  Rebuild: docker-compose up --build -d"
    echo ""
    echo -e "${GREEN}🎉 Setup complete! Your PDF Q&A system is running.${NC}"
else
    echo -e "${RED}❌ Failed to start the application${NC}"
    exit 1
fi
