@echo off
REM Voice Assistant Setup Script
REM Place this file at: setup.bat (root level)

echo ==========================================
echo    Voice Assistant Setup
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✓ pip found
echo.

REM Create directory structure
echo Creating directory structure...
if not exist "config" mkdir config
if not exist "scripts" mkdir scripts
if not exist "scripts\audio" mkdir scripts\audio
if not exist "scripts\utility" mkdir scripts\utility
if not exist "scripts\coding" mkdir scripts\coding
if not exist "scripts\knowledge" mkdir scripts\knowledge
if not exist "scripts\productivity" mkdir scripts\productivity
if not exist "scripts\system" mkdir scripts\system
if not exist "scripts\streaming" mkdir scripts\streaming
if not exist "state" mkdir state
if not exist "logs" mkdir logs
echo ✓ Directories created

echo.
echo Installing Python dependencies...
echo ==========================================

REM Install requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some dependencies
    echo This might be due to:
    echo - Missing Visual C++ Build Tools (needed for some audio packages)
    echo - Network connection issues
    echo - Python version compatibility
    echo.
    echo Try installing dependencies manually:
    echo   pip install voicemeeter-api pyyaml
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ Dependencies installed successfully!
echo.

REM Check if config files exist
if not exist "config\commands.yaml" (
    echo WARNING: config\commands.yaml not found
    echo Please create this file using the provided template
    echo.
)

if not exist "dispatcher.py" (
    echo WARNING: dispatcher.py not found
    echo Please create this file using the provided code
    echo.
)

if not exist "main.py" (
    echo WARNING: main.py not found
    echo Please create this file using the provided code
    echo.
)

if not exist "scripts\audio\voicemeeter_control.py" (
    echo WARNING: scripts\audio\voicemeeter_control.py not found
    echo Please create this file using the provided code
    echo.
)

echo ==========================================
echo Setup complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure all Python files are in place:
echo    - dispatcher.py
echo    - main.py
echo    - config\commands.yaml
echo    - scripts\audio\voicemeeter_control.py
echo.
echo 2. Test the installation:
echo    python main.py
echo.
echo 3. For Voicemeeter integration, ensure Voicemeeter is installed
echo.
echo Press any key to exit...
pause >nul