@echo off
title HeartGarden
cd /d "%CD%"
echo ========================================
echo    HeartGarden - Starting Services
echo ========================================
echo.
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found
echo.
echo [2/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.
echo [3/3] Preparing environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing Python dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd..
)
echo.
echo ========================================
echo    Starting Backend (port 5000)...
echo ========================================
start "HeartGarden-Backend" cmd /k "cd /d %CD% && call venv\Scripts\activate.bat && python -m app.main"
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo    Starting Frontend (port 3000)...
echo ========================================
start "HeartGarden-Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo    Opening Browser...
echo ========================================
start http://localhost:3000
echo.
echo All services started!
echo.