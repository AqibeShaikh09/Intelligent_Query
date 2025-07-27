# 🐳 Docker Deployment Guide

This guide shows how to build, run, and deploy the Intelligent Query PDF Q&A System using Docker.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose (included with Docker Desktop)
- OpenRouter API key (get from https://openrouter.ai/keys)

## 🚀 Quick Start

### 1. Clone or Download the Project
```bash
git clone https://github.com/AqibeShaikh09/Intelligent_Query.git
cd Intelligent_Query
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your API key
# Replace 'your_openrouter_api_key_here' with your actual API key
```

### 3. Build and Run with Docker Compose
```bash
# Build and start the application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Application
- Open your browser and go to: http://localhost:5000
- Upload a PDF and start asking questions!

## 🔧 Manual Docker Commands

### Build the Image
```bash
docker build -t intelligent-query .
```

### Run the Container
```bash
docker run -d \
  --name intelligent-query-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  intelligent-query
```

### Stop and Remove
```bash
docker stop intelligent-query-app
docker rm intelligent-query-app
```

## 🌍 Publishing to Docker Hub

### 1. Tag the Image
```bash
docker tag intelligent-query your-dockerhub-username/intelligent-query:latest
```

### 2. Push to Docker Hub
```bash
docker login
docker push your-dockerhub-username/intelligent-query:latest
```

### 3. Pull and Run from Docker Hub
```bash
# Create .env file with your API key first
echo "OPENROUTER_API_KEY=your_actual_api_key" > .env

# Pull and run
docker run -d \
  --name intelligent-query \
  -p 5000:5000 \
  --env-file .env \
  your-dockerhub-username/intelligent-query:latest
```

## 🐛 Troubleshooting

### Check Container Status
```bash
docker-compose ps
docker-compose logs intelligent-query-app
```

### Access Container Shell
```bash
docker exec -it intelligent-query-app bash
```

### View Application Logs
```bash
docker-compose logs -f intelligent-query-app
```

### Test API Configuration
```bash
# Check if API key is configured
curl http://localhost:5000/test-api

# Check application status
curl http://localhost:5000/status
```

### Common Issues

#### 1. API Key Not Found
**Problem**: "No API key configured" error
**Solution**: 
- Ensure `.env` file exists with `OPENROUTER_API_KEY=your_key`
- Check that `.env` file is in the same directory as `docker-compose.yml`

#### 2. Port Already in Use
**Problem**: "Port 5000 is already allocated"
**Solution**: 
- Change the port mapping: `"5001:5000"` in docker-compose.yml
- Or stop the service using port 5000

#### 3. Permission Errors
**Problem**: File permission issues
**Solution**: 
- Ensure the `uploads` directory exists and is writable
- Try: `mkdir uploads && chmod 755 uploads`

#### 4. Import Errors
**Problem**: Module import failures
**Solution**: 
- The docker_run.py script handles import path issues automatically
- Check logs: `docker-compose logs -f`

## 📊 Health Monitoring

The application includes built-in health checks:

```bash
# Docker health check
docker inspect --format='{{.State.Health.Status}}' intelligent-query-app

# Application health endpoint
curl http://localhost:5000/status
```

## 🔒 Security Considerations

1. **API Key Security**: Never commit `.env` files to version control
2. **Non-root User**: Container runs as non-root user `appuser`
3. **File Permissions**: Uploads are contained within the container
4. **Network Isolation**: Uses custom Docker network for isolation

## 🚀 Production Deployment

### Environment Variables for Production
```env
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your_strong_secret_key
OPENROUTER_API_KEY=your_api_key
PORT=5000
```

### Docker Compose Production Setup
```yaml
services:
  pdf-qa-app:
    build: .
    restart: always
    ports:
      - "80:5000"  # Use port 80 for production
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 📈 Scaling

### Multiple Replicas
```bash
docker-compose up -d --scale pdf-qa-app=3
```

### Load Balancer Setup
Use nginx or traefik for load balancing multiple instances.

## 🔄 Updates and Maintenance

### Update the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Clean Up
```bash
# Remove unused images
docker image prune

# Remove all stopped containers
docker container prune

# Complete cleanup
docker system prune -a
```

## 📞 Support

If you encounter any issues:

1. Check the logs: `docker-compose logs -f`
2. Verify API configuration: `curl http://localhost:5000/test-api`
3. Open an issue on GitHub with logs and error details

---

**Happy querying! 🚀**
