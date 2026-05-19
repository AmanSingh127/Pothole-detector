@echo off
:: ============================================
:: Pothole Tracker - One-Time Firewall Setup
:: Right-click this file → Run as administrator
:: ============================================

echo.
echo ====================================
echo  Pothole Tracker - Firewall Setup
echo ====================================
echo.

:: Check admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Remove old rule if exists
netsh advfirewall firewall delete rule name="Pothole Tracker GPS" >nul 2>&1

:: Add inbound rule for GPS server port
netsh advfirewall firewall add rule name="Pothole Tracker GPS" dir=in action=allow protocol=TCP localport=8085

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! Firewall rule added for port 8085.
    echo You only need to run this once.
    echo.
    echo Now run: python dashcam_tracker.py --ip YOUR_PHONE_IP
    echo.
) else (
    echo.
    echo FAILED to add firewall rule. Try running as administrator.
    echo.
)
pause
