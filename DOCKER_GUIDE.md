# 🐳 Docker Deployment Guide

## Quick Start for Anyone

### 1. **Prerequisites**
- Docker installed on your system
- Docker Compose (usually comes with Docker)

### 2. **Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/AqibeShaikh09/Intelligent_Query.git
cd Intelligent_Query

# Create environment file
cp .env.example .env
```

### 3. **Configure API Key**
Edit the `.env` file and add your OpenRouter API key:
```bash
OPENROUTER_API_KEY=your_actual_api_key_here
```

### 4. **Run with Docker Compose (Recommended)**
```bash
# Build and start the container
docker-compose up -d

# Check if it's running
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. **Access the Application**
- Open your browser and go to: http://localhost:5000
- Upload a PDF and start chatting with it!

## Alternative Methods

### Method 1: Direct Docker Build
```bash
# Build the image
docker build -t pdf-qa-system .

# Run the container
docker run -d \
  --name pdf-qa-app \
  -p 5000:5000 \
  --env-file .env \
  pdf-qa-system
```

### Method 2: Using the Portable Runner
```bash
# If you have Python locally
python docker_run.py
```

## Troubleshooting

### Issue: Import Errors
**Solution**: The application now has smart import handling that works in all environments.

### Issue: Permission Denied
**Solution**: The Docker container runs as non-root user for security.

### Issue: API Key Not Working
**Solution**: 
1. Check your `.env` file has the correct API key
2. Restart the container: `docker-compose restart`

### Issue: Port Already in Use
**Solution**: Change the port in docker-compose.yml:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | Your OpenRouter API key |
| `SECRET_KEY` | No | auto-generated | Flask secret key |
| `FLASK_ENV` | No | production | Flask environment |
| `PORT` | No | 5000 | Application port |

## Container Features

- ✅ **Multi-stage import handling** - Works in any environment
- ✅ **Non-root user** - Secure by default
- ✅ **Health checks** - Automatic monitoring
- ✅ **Proper Python paths** - No import issues
- ✅ **Volume mounting** - Persistent uploads
- ✅ **Environment variables** - Easy configuration

## Docker Commands Reference

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Restart the application
docker-compose restart

# Rebuild the image
docker-compose build --no-cache

# Check container status
docker-compose ps

# Access container shell
docker-compose exec pdf-qa-app bash
```

## Making it Public

### Using ngrok (Temporary)
```bash
# Install ngrok first, then:
ngrok http 5000
```

### Using Cloud Platforms (Permanent)
- Deploy to Railway, Heroku, or DigitalOcean
- Use the same Docker setup
- Set environment variables in the platform's dashboard

## Performance Tips

1. **Allocate enough memory**: At least 2GB RAM
2. **Use SSD storage**: For faster PDF processing
3. **Monitor logs**: `docker-compose logs -f`
4. **Health checks**: Built-in monitoring at `/status`

## Security Notes

- The container runs as non-root user
- Only port 5000 is exposed
- Environment variables are properly isolated
- No sensitive data is logged

## Support

If you encounter any issues:
1. Check the logs: `docker-compose logs`
2. Ensure your `.env` file is properly configured
3. Try rebuilding: `docker-compose build --no-cache`
4. Open an issue on GitHub with error details
