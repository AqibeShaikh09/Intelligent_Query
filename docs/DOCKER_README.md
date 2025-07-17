# 🐳 Docker Setup for PDF Q&A System

This guide will help you set up and run the PDF Q&A system using Docker.

## Prerequisites

- **Docker Desktop** installed on your system
  - Windows: [Download Docker Desktop](https://docs.docker.com/desktop/windows/)
  - macOS: [Download Docker Desktop](https://docs.docker.com/desktop/mac/)
  - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)

## Quick Setup

### Windows Users
```bash
# Run the setup script
setup-docker.bat
```

### Linux/macOS Users
```bash
# Make the script executable
chmod +x setup-docker.sh

# Run the setup script
./setup-docker.sh
```

### Manual Setup

1. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

## Configuration

### Environment Variables (.env)
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Flask Configuration  
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Application Settings
MAX_FILE_SIZE=16777216
```

## Docker Commands

### Basic Operations
```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Development
```bash
# Rebuild and start
docker-compose up --build -d

# Run in development mode (with logs)
docker-compose up --build

# Access container shell
docker-compose exec pdf-qa-app bash
```

### Maintenance
```bash
# View container status
docker-compose ps

# Check resource usage
docker stats

# Clean up unused images
docker system prune -f
```

## Application URLs

- **Main Application**: http://localhost:5000
- **Health Check**: http://localhost:5000/status

## File Structure

```
BJ/
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Multi-container setup
├── .dockerignore           # Files to exclude from Docker build
├── requirements.txt        # Python dependencies
├── setup-docker.sh         # Linux/macOS setup script
├── setup-docker.bat        # Windows setup script
├── .env                    # Environment variables (create from template)
├── web_app.py              # Main Flask application
├── app.py                  # Core PDF processing logic
└── uploads/                # PDF upload directory
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 5000
   netstat -tulpn | grep 5000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **API Key not working**
   - Verify your OpenRouter API key in `.env`
   - Check API key permissions and credits

3. **Memory issues**
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Recommended: 4GB+ for AI models
   ```

4. **Build failures**
   ```bash
   # Clean build cache
   docker-compose build --no-cache
   
   # Remove old images
   docker image prune -f
   ```

### Logs and Debugging

```bash
# View application logs
docker-compose logs pdf-qa-app

# Follow logs in real-time
docker-compose logs -f pdf-qa-app

# Check container health
docker-compose ps
```

## Performance Tuning

### Resource Allocation
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- **Storage**: 2GB+ free space for models and uploads

### Production Deployment
```bash
# Use production environment
FLASK_ENV=production docker-compose up -d

# Enable health checks
# (Already configured in docker-compose.yml)
```

## Security Notes

- Change default `SECRET_KEY` in production
- Use environment variables for sensitive data
- Restrict file upload sizes (configured as 16MB)
- Run containers as non-root user in production

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure Docker has sufficient resources
4. Check network connectivity for API calls
