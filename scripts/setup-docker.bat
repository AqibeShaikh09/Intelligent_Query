@echo off
setlocal enabledelayedexpansion

echo 🐳 PDF Q&A System - Docker Setup
echo ==================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

echo ✅ Docker is installed

REM Check for .env file
if not exist ".env" (
    echo ⚠️  .env file not found. Creating a template...
    (
        echo # OpenRouter API Configuration
        echo OPENROUTER_API_KEY=your_openrouter_api_key_here
        echo.
        echo # Flask Configuration
        echo SECRET_KEY=your-secret-key-here
        echo FLASK_ENV=production
        echo.
        echo # Application Settings
        echo MAX_FILE_SIZE=16777216
    ) > .env
    echo 📝 Please update the .env file with your actual API keys before running the application.
)

REM Create uploads directory
if not exist "uploads" mkdir uploads

echo 🔨 Building Docker image...

REM Build the Docker image
docker-compose build
if errorlevel 1 (
    echo ❌ Failed to build Docker image
    pause
    exit /b 1
)

echo ✅ Docker image built successfully

echo 🚀 Starting the application...

REM Start the application
docker-compose up -d
if errorlevel 1 (
    echo ❌ Failed to start the application
    pause
    exit /b 1
)

echo ✅ Application started successfully
echo.
echo 📋 Application Details:
echo   🌐 URL: http://localhost:5000
echo   📊 Status: http://localhost:5000/status
echo.
echo 🛠️  Useful Commands:
echo   📖 View logs: docker-compose logs -f
echo   🔄 Restart: docker-compose restart
echo   🛑 Stop: docker-compose down
echo   🏗️  Rebuild: docker-compose up --build -d
echo.
echo 🎉 Setup complete! Your PDF Q&A system is running.
pause
