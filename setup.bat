@echo off
echo Creating virtual environment for Subway Surfers Pose Detection...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or later.
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete! To run the application:
echo.
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 2. Run the application with one of these commands:
echo    python subway_surfers_pose_detection.py --test-image
echo    python subway_surfers_pose_detection.py --test-hands
echo    python subway_surfers_pose_detection.py --test-horizontal
echo    python subway_surfers_pose_detection.py --test-vertical
echo    python subway_surfers_pose_detection.py --play
echo.
echo 3. For help, run:
echo    python subway_surfers_pose_detection.py --help
echo.

pause