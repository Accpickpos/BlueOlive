@echo off
REM Start all services for the BlueOlive POS system

echo.
echo ========================================
echo BlueOlive POS - Multi-Service Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    exit /b 1
)
echo [OK] Python found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    exit /b 1
)
echo [OK] Node.js found

REM Start POS FastAPI
echo.
echo Starting FastAPI POS System (Port 8001)...
cd backend\pos

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

start "FastAPI POS" uvicorn main:app --host 127.0.0.1 --port 8001
echo [OK] FastAPI POS started

cd ..\..

echo.
echo Service Status:
echo   - FastAPI POS: http://localhost:8001
echo   - Django Backend: http://localhost:8000
echo   - Next.js Frontend: http://localhost:3000
echo.
echo Documentation:
echo   - POS API Docs: http://localhost:8001/docs
echo   - Django Admin: http://localhost:8000/admin
echo.
echo To stop all services, close the terminal windows
echo.

pause
