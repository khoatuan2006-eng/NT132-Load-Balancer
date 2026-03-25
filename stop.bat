@echo off
title Load Balancer - Stop All
echo ========================================
echo   DUNG HE THONG LOAD BALANCER
echo ========================================
echo.

echo [1/2] Dung Nginx...
cd /d d:\LoadBalance\nginx-1.29.6
nginx.exe -s stop 2>nul
taskkill /f /im nginx.exe >nul 2>nul

echo [2/2] Dung tat ca Python server...
taskkill /f /im python.exe >nul 2>nul

echo.
echo ========================================
echo   DA DUNG TAT CA!
echo ========================================
pause
