@echo off
title Claude Chat Application
color 0A
echo ================================
echo    Claude Chat Application
echo ================================
echo.

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY environment variable is not set!
    echo.
    echo Please set your Anthropic API key first:
    echo   1. Temporary session: set ANTHROPIC_API_KEY=your_api_key_here
    echo   2. Permanent: setx ANTHROPIC_API_KEY "your_api_key_here"
    echo.
    pause
    exit /b 1
)

echo API key found: %ANTHROPIC_API_KEY:~0,12%...
echo.

echo Starting Claude Chat Application...
echo.

echo [1/1] Starting Complete Application (Docker)...
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY% claude-chat-app

echo.
echo ================================
echo   Application Running!
echo ================================
echo.
echo Complete App:  http://localhost:8000
echo.
echo Available Claude 4 Models:
echo   - Claude 4 Sonnet (High Performance)
echo   - Claude 4 Opus (Maximum Intelligence)
echo.
echo Press Ctrl+C to stop the application
pause
echo Press any key to exit this window...
pause > nul
