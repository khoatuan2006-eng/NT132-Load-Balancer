@echo off
title Load Balancer - Start All
echo ========================================
echo   KHOI DONG HE THONG LOAD BALANCER
echo ========================================
echo.

:: ============================================================
:: CẤU HÌNH — Đổi IP Ubuntu VM tại đây nếu cần
:: ============================================================
set VM_IP=192.168.56.101

:: Lay duong dan thu muc chua file .bat nay
cd /d "%~dp0"

:: Chay Server1 (port 8001)
echo [1/4] Khoi dong Server1 (port 8001)...
start "Server1 - Port 8001" cmd /c "cd /d "%~dp0" && python backend/app.py --port 8001"

:: Chay Server2 (port 8002)
echo [2/4] Khoi dong Server2 (port 8002)...
start "Server2 - Port 8002" cmd /c "cd /d "%~dp0" && python backend/app.py --port 8002"

:: Chay Server3 - Backup (port 8003)
echo [3/4] Khoi dong Server3 - Backup (port 8003)...
start "Server3 - Backup Port 8003" cmd /c "cd /d "%~dp0" && python backend/app.py --port 8003"

:: Doi 2 giay cho backend khoi dong
timeout /t 2 /nobreak >nul

:: Chay Dashboard API (port 5000) - ket noi toi HAProxy tren Ubuntu VM
echo [4/4] Khoi dong Dashboard API (port 5000)...
start "Dashboard API" cmd /c "cd /d "%~dp0" && python dashboard/api.py --haproxy-ip %VM_IP%"

echo.
echo ========================================
echo   TAT CA DA KHOI DONG THANH CONG!
echo ========================================
echo   Server1    : http://localhost:8001
echo   Server2    : http://localhost:8002
echo   Server3    : http://localhost:8003 (backup)
echo   Dashboard  : http://localhost:5000
echo   HAProxy VM : http://%VM_IP%:80
echo   HA Stats   : http://%VM_IP%:8404/stats
echo ========================================
echo.
pause
