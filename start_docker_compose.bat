@echo off
echo ========================================
echo   Claude Chat - Docker Compose
echo ========================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY environment variable is not set!
    echo.
    echo Please run: setx ANTHROPIC_API_KEY "your_api_key_here"
    echo Then restart this terminal and try again.
    pause
    exit /b 1
)

REM Set default database password if not provided
if "%DB_PASSWORD%"=="" (
    set DB_PASSWORD=claude_secure_2024
    echo Using default database password. For production, set DB_PASSWORD environment variable.
    echo.
)

echo Building and starting Claude Chat with PostgreSQL...
echo Database: PostgreSQL (user: claude_user, db: claude_chat)
echo.

docker-compose up --build

echo.
echo To stop the application, press Ctrl+C
echo To run in background: docker-compose up -d --build
echo To stop background: docker-compose down
pause
