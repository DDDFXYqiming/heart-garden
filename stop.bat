@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    HeartGarden - Stopping Services
echo ========================================
echo.

echo [1/3] Stopping Backend (port 5000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo   Killed PID %%a
)
echo.

echo [2/3] Stopping Frontend (port 3001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo   Killed PID %%a
)
echo.

echo [3/3] Cleaning up stray node/python processes...
taskkill /FI "WINDOWTITLE eq HeartGarden-Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq HeartGarden-Frontend*" /T /F >nul 2>&1
echo.

echo ========================================
echo    All HeartGarden services stopped!
echo ========================================
timeout /t 2 /nobreak >nul
