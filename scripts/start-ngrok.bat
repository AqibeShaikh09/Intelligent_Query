@echo off
echo ====================================
echo    PDF Q&A App - Public Launch
echo ====================================
echo.

REM Change to the project directory
cd /d "c:\Users\siddh\Desktop\BJ"

echo 🔍 Checking Docker status...
docker-compose ps

echo.
echo 📦 Starting Docker container...
docker-compose up -d

echo.
echo ⏳ Waiting for container to be ready...
timeout /t 15 /nobreak

echo.
echo 🏥 Checking app health...
curl -s http://localhost:5000/status > nul
if %errorlevel% equ 0 (
    echo ✅ App is running locally on http://localhost:5000
) else (
    echo ⚠️  App might still be starting up...
)

echo.
echo 🌐 Creating public tunnel with ngrok...
echo.
echo ========================================
echo   Your app will be available at:
echo   The HTTPS URL shown below ⬇️
echo ========================================
echo.
echo 📱 Share this link with anyone!
echo 🔗 They can upload PDFs and ask questions
echo.

REM Start ngrok tunnel
ngrok http 5000

echo.
echo 🛑 Ngrok stopped. Cleaning up...
docker-compose down
echo 👋 Goodbye!
pause
