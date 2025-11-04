@echo off
REM Start Backend Server with Python 3
echo ========================================
echo Starting Medical Scheduler Backend
echo ========================================
echo.

cd backend

REM Try Python 3 commands in order
python3 main.py
if errorlevel 1 (
    py -3 main.py
    if errorlevel 1 (
        python main.py
        if errorlevel 1 (
            echo.
            echo ERROR: Could not find Python 3!
            echo Please install Python 3.8+ or ensure it's in your PATH
            echo.
            pause
            exit /b 1
        )
    )
)

