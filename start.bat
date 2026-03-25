@echo off
title Load Balancer - Start All
echo ========================================
echo   KHOI DONG HE THONG LOAD BALANCER
echo ========================================
echo.

:: Chay Server1 (port 8001)
echo [1/4] Khoi dong Server1 (port 8001)...
start "Server1 - Port 8001" cmd /c "cd /d d:\LoadBalance\Server1 && python -m http.server 8001"

:: Chay Server2 (port 8002)
echo [2/4] Khoi dong Server2 (port 8002)...
start "Server2 - Port 8002" cmd /c "cd /d d:\LoadBalance\Server2 && python -m http.server 8002"

:: Chay Server3 - Backup (port 8003)
echo [3/4] Khoi dong Server3 - Backup (port 8003)...
start "Server3 - Backup Port 8003" cmd /c "cd /d d:\LoadBalance\Server3 && python -m http.server 8003"

:: Doi 1 giay cho cac server khoi dong
timeout /t 1 /nobreak >nul

:: Chay Nginx
echo [4/4] Khoi dong Nginx (port 8080)...
cd /d d:\LoadBalance\nginx-1.29.6
start nginx.exe

echo.
echo ========================================
echo   TAT CA DA KHOI DONG THANH CONG!
echo ========================================
echo   Server1:  http://localhost:8001
echo   Server2:  http://localhost:8002
echo   Server3:  http://localhost:8003 (backup)
echo   Nginx LB: http://localhost:8080
echo ========================================
echo.
echo Nhan phim bat ky de mo trinh duyet...
pause >nul
start http://localhost:8080
