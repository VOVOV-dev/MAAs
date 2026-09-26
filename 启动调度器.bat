@echo off
cd /d "%~dp0"

rem ============ request admin (scheduler needs it to launch game tools) ============
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

rem ============ run scheduler ============
rem default: daemon mode, runs a full round now then daily at 4:00
rem pass args like:  --once  --dry-run  --only zzz
scheduler\python\python.exe scheduler\scheduler.py %*
pause
