@echo off
title HeartGarden
cd /d "%CD%"
echo ========================================
echo    HeartGarden - Starting Services
echo ========================================
echo.
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found
echo.
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.
echo [3/5] Preparing environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Ensuring Python dependencies...
pip install -r requirements.txt -q
echo.
echo [4/5] Verifying Python dependencies...
python -c "import flask, flask_cors, flask_limiter, openai, jwt" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing Python packages. Attempting reinstall...
    pip install -r requirements.txt
    python -c "import flask, flask_cors, flask_limiter, openai, jwt"
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please check requirements.txt
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies verified
echo.
echo [5/5] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd..
) else (
    echo [OK] Frontend dependencies found
)
echo.
echo ========================================
echo    Starting Backend (port 5000)...
echo ========================================
start "HeartGarden-Backend" cmd /k "cd /d %CD% && call venv\Scripts\activate.bat && python -m app.main"
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo    Starting Frontend (port 3001)...
echo ========================================
start "HeartGarden-Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo    Opening Browser...
echo ========================================
start http://localhost:3001
echo.
echo ========================================
echo    All services started!
echo    Backend:  http://localhost:5000
echo    Frontend: http://localhost:3001
echo ========================================
echo.
echo.