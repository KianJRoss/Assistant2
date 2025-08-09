@echo off
REM Voice Assistant Launcher
REM Place this file at: run.bat (root level)

echo ==========================================
echo    Starting Voice Assistant
echo ==========================================
echo.

REM Check if main files exist
if not exist "dispatcher.py" (
    echo ERROR: dispatcher.py not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

if not exist "config\commands.yaml" (
    echo ERROR: config\commands.yaml not found
    echo Please create this configuration file
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

echo ✓ All checks passed
echo.
echo Starting Voice Assistant...
echo (Press Ctrl+C to stop)
echo.

REM Run the assistant
python main.py

echo.
echo Voice Assistant stopped.
pause