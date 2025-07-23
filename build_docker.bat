@echo off
echo ========================================
echo   Building Claude Chat Docker Image
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo Building Docker image...
docker build -t claude-chat-app .

if %errorlevel% neq 0 (
    echo ERROR: Docker build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Docker Image Built Successfully!
echo ========================================
echo.
echo To run the application:
echo   docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_api_key_here claude-chat-app
echo.
echo Or create a .env file and run:
echo   docker run -p 8000:8000 --env-file .env claude-chat-app
echo.
echo Then open: http://localhost:8000
echo.
pause
