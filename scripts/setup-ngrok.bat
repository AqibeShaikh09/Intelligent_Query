@echo off
REM ====================================
REM     Quick Ngrok Setup Script
REM ====================================

echo 🔧 Setting up ngrok for PDF Q&A App...
echo.

REM Check if ngrok is installed
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ngrok not found! Please install ngrok first:
    echo    1. Go to: https://ngrok.com/download
    echo    2. Download and extract ngrok.exe
    echo    3. Add to your PATH or place in this folder
    echo.
    pause
    exit /b 1
)

echo ✅ Ngrok is installed
echo.

REM Check if auth token is configured
ngrok config check >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔑 Ngrok needs authentication setup
    echo.
    echo Please follow these steps:
    echo 1. Go to: https://dashboard.ngrok.com/signup
    echo 2. Sign up for free account
    echo 3. Copy your authtoken
    echo 4. Run: ngrok config add-authtoken YOUR_TOKEN
    echo.
    set /p token="Enter your ngrok authtoken (or press Enter to skip): "
    if not "!token!"=="" (
        ngrok config add-authtoken !token!
        echo ✅ Auth token configured!
    ) else (
        echo ⚠️  You can configure this later with:
        echo    ngrok config add-authtoken YOUR_TOKEN
    )
    echo.
)

echo 🎯 Setup complete! You can now run:
echo    start-ngrok.bat
echo.
echo This will:
echo   📦 Start your Docker container
echo   🌐 Create public tunnel
echo   🔗 Give you a shareable URL
echo.
pause
