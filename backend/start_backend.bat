@echo off
REM Start Backend Server with Python 3
echo Starting Backend Server...
echo.

REM Try different Python 3 commands
python3 main.py 2>nul
if errorlevel 1 (
    py -3 main.py 2>nul
    if errorlevel 1 (
        python main.py 2>nul
        if errorlevel 1 (
            echo ERROR: Could not find Python 3. Please ensure Python 3.7+ is installed.
            pause
            exit /b 1
        )
    )
)

