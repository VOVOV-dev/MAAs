@echo off
cd /d "%~dp0"

rem ============ request admin (needed to launch/close game tools) ============
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

rem ============ check python ============
if not exist "scheduler\python\python.exe" (
    echo [ERROR] Python not found. Please run setup.ps1 first.
    pause
    exit /b 1
)

rem ============ run catch-up ============
rem no args: interactive selection (pick game by number/name)
rem with args like:  maaend  or  1,3  or  all  or  maaend --kill --config 快速日常
scheduler\python\python.exe scheduler\run_one.py %*
pause
