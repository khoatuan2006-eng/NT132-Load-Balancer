@echo off
title Load Balancer - Start All
echo ========================================
echo   KHOI DONG HE THONG LOAD BALANCER
echo ========================================
echo.

:: Lay duong dan thu muc chua file .bat nay
cd /d "%~dp0"

:: Cai psutil neu chua co (can cho /metrics endpoint)
echo [0/3] Kiem tra thu vien Python...
pip install -q flask psutil

:: Chay Flask Server1 (port 8001)
echo [1/3] Khoi dong Flask Server1 (port 8001)...
start "Server1 - Port 8001" cmd /k "cd /d "%~dp0backend" && python app.py --port 8001"

:: Doi 1 giay
timeout /t 1 /nobreak >nul

:: Chay Flask Server2 (port 8002)
echo [2/3] Khoi dong Flask Server2 (port 8002)...
start "Server2 - Port 8002" cmd /k "cd /d "%~dp0backend" && python app.py --port 8002"

:: Doi 1 giay
timeout /t 1 /nobreak >nul

:: Chay Flask Server3 - Backup (port 8003)
echo [3/3] Khoi dong Flask Server3 Backup (port 8003)...
start "Server3 - Backup Port 8003" cmd /k "cd /d "%~dp0backend" && python app.py --port 8003"

echo.
echo ========================================
echo   TAT CA DA KHOI DONG THANH CONG!
echo ========================================
echo   Server1:  http://localhost:8001
echo   Server2:  http://localhost:8002
echo   Server3:  http://localhost:8003 (backup)
echo.
echo   Test nhanh:
echo     http://localhost:8001/health
echo     http://localhost:8001/metrics
echo     http://localhost:8001/info
echo ========================================
echo.
pause
