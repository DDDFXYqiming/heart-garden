@echo off
echo Stopping HeartGarden services...
taskkill /FI "WindowTitle eq HeartGarden-Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq HeartGarden-Frontend*" /T /F >nul 2>&1
echo Done!
timeout /t 2 /nobreak >nul