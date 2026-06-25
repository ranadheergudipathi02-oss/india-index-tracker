@echo off
REM Phase 4 - Task Scheduler entry point. Runs the daily fetch -> diff -> build -> commit -> push -> alert.
setlocal
set "ROOT=C:\Claude developement\static-index-tracker"
set "PY=C:\Users\Saila's PC\AppData\Local\Programs\Python\Python312\python.exe"
cd /d "%ROOT%"
if not exist "logs" mkdir "logs"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "DAY=%%i"
"%PY%" run_daily.py >> "logs\run_%DAY%.log" 2>&1
endlocal
