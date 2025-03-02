@echo off
echo Installing required dependencies...

REM Ensure Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python first.
    pause
    exit /b
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required modules
echo Installing lxml...
python -m pip install lxml

REM Install tkinter (for Linux users, Windows usually has it pre-installed)
echo Checking if tkinter is installed...
python -c "import tkinter" 2>nul
if %errorlevel% neq 0 (
    echo tkinter is not installed. If you're on Linux, install it manually.
) else (
    echo tkinter is already installed.
)

echo All dependencies installed successfully!
pause
