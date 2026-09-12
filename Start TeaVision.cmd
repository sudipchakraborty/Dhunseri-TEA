@echo off
setlocal
cd /d "%~dp0EdgeNode"
if not exist ".venv\Scripts\python.exe" (
    echo TeaVision's Python environment is missing from EdgeNode\.venv.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo TeaVision could not start. Please review the error above.
    pause
    exit /b 1
)
