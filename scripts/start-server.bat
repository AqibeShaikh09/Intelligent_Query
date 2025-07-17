@echo off
REM Startup script for PDF Q&A Server (Windows)

echo 🚀 Starting PDF Q&A Server...

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Please create one with your OpenRouter API key.
    echo You can copy .env.example to .env and fill in your API key.
    pause
    exit /b 1
)

REM Start the application
echo 🔧 Starting Docker containers...
docker-compose up -d

REM Wait for health check
echo ⏳ Waiting for application to be ready...
timeout /t 10 >nul

REM Check container status
docker-compose ps | findstr /C:"Up" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Server is running successfully!
    echo 🌐 Open your browser and go to: http://localhost:5000
    echo.
    echo 📋 Server Management Commands:
    echo   Stop server:    docker-compose down
    echo   View logs:      docker-compose logs -f
    echo   Restart:        docker-compose restart
) else (
    echo ⚠️  Server started but health check pending...
    echo 🌐 Try opening: http://localhost:5000
    echo 📋 Check logs with: docker-compose logs -f
)

echo.
echo Press any key to continue...
pause >nul
