@echo off
setlocal EnableExtensions EnableDelayedExpansion

title SadakSetu Platform Launcher

echo ===============================================================
echo                SADAKSETU PLATFORM LAUNCHER
echo ===============================================================
echo.

set "ROOT=%~dp0"

rem -------------------------------------------------------------
rem Locate Backend and Frontend directories
rem -------------------------------------------------------------
if exist "%ROOT%backend\.venv\Scripts\python.exe" (
    set "BACKEND_DIR=%ROOT%backend"
) else if exist "%ROOT%SadakSetu--main\backend\.venv\Scripts\python.exe" (
    set "BACKEND_DIR=%ROOT%SadakSetu--main\backend"
) else if exist "%ROOT%SadakSetu\backend\.venv\Scripts\python.exe" (
    set "BACKEND_DIR=%ROOT%SadakSetu\backend"
) else if exist "%ROOT%..\backend\.venv\Scripts\python.exe" (
    set "BACKEND_DIR=%ROOT%..\backend"
)

if exist "%ROOT%package.json" (
    set "WEB_DIR=%ROOT%"
) else if exist "%ROOT%SadakSetu--main\package.json" (
    set "WEB_DIR=%ROOT%SadakSetu--main"
) else if exist "%ROOT%SADAK_SETU\SadakSetu_Dashboard\package.json" (
    set "WEB_DIR=%ROOT%SADAK_SETU\SadakSetu_Dashboard"
) else if exist "%ROOT%SadakSetu_Dashboard\package.json" (
    set "WEB_DIR=%ROOT%SadakSetu_Dashboard"
)

set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "API_PORT=8001"
set "WEB_PORT=5174"

if not exist "%PYTHON%" goto :err_python

rem Detect active Wi-Fi or Ethernet LAN IPv4 address
set "LAN_IP="
for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "@(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi*','Ethernet*' -ErrorAction SilentlyContinue)[0].IPAddress"`) do (
    set "LAN_IP=%%I"
)
if not defined LAN_IP set "LAN_IP=127.0.0.1"

rem 1. Check / Start Backend API
curl.exe --silent --fail --max-time 1 http://127.0.0.1:%API_PORT%/health >nul 2>&1
if not errorlevel 1 (
    echo [*] Backend API is already running on port %API_PORT%.
    goto :backend_up
)

echo [*] Starting Backend API on port %API_PORT%...
start "SadakSetu Backend API" /D "%BACKEND_DIR%" cmd /k "set ""AI_MODEL_PATH=models/baseline_yolo11.pt"" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %API_PORT%"

set "BACKEND_STARTED=0"
for /L %%A in (1,1,30) do (
    curl.exe --silent --fail --max-time 1 http://127.0.0.1:%API_PORT%/health >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_STARTED=1"
        goto :backend_up
    )
    ping -n 2 127.0.0.1 >nul
)

if "!BACKEND_STARTED!"=="0" (
    echo.
    echo [ERROR] Backend API failed to start on port %API_PORT% within 30 seconds.
    echo Please inspect the "SadakSetu Backend API" console window for errors.
    pause
    exit /b 1
)

:backend_up
echo [OK] Backend API is online.

rem 2. Check / Start Web Admin Dashboard
curl.exe --silent --fail --max-time 1 http://127.0.0.1:%WEB_PORT%/ >nul 2>&1
if not errorlevel 1 (
    echo [*] Web Admin Dashboard is already running on port %WEB_PORT%.
    goto :web_up
)

echo [*] Starting Web Admin Dashboard on port %WEB_PORT%...
start "SadakSetu Web Dashboard" /D "%WEB_DIR%" cmd /k "set ""VITE_API_BASE_URL=/api/v1"" && npm run dev -- --host 0.0.0.0 --port %WEB_PORT%"

set "WEB_STARTED=0"
for /L %%A in (1,1,25) do (
    curl.exe --silent --fail --max-time 1 http://127.0.0.1:%WEB_PORT%/ >nul 2>&1
    if not errorlevel 1 (
        set "WEB_STARTED=1"
        goto :web_up
    )
    ping -n 2 127.0.0.1 >nul
)

if "!WEB_STARTED!"=="0" (
    echo.
    echo [ERROR] Web Dashboard failed to start on port %WEB_PORT% within 25 seconds.
    echo Please inspect the "SadakSetu Web Dashboard" console window for errors.
    pause
    exit /b 1
)

:web_up
echo [OK] Web Dashboard is online.

rem 3. Configure ADB reverse tunnel for connected Android device
set "ADB_CMD="
where adb >nul 2>&1
if not errorlevel 1 (
    set "ADB_CMD=adb"
) else if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" (
    set "ADB_CMD=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
)

if defined ADB_CMD (
    "%ADB_CMD%" reverse tcp:%API_PORT% tcp:%API_PORT% >nul 2>&1
    "%ADB_CMD%" reverse tcp:%WEB_PORT% tcp:%WEB_PORT% >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Android ADB reverse port forwarding active for port %API_PORT% and %WEB_PORT%.
    ) else (
        echo [*] Note: No USB Android device currently attached for ADB port forwarding.
    )
)

echo.
echo ===============================================================
echo                 SADAKSETU PLATFORM IS READY
echo ===============================================================
echo.
echo   Web Admin Dashboard  : http://localhost:%WEB_PORT%/
echo   Network Web Dashboard: http://%LAN_IP%:%WEB_PORT%/
echo   Android API URL (LAN): http://%LAN_IP%:%API_PORT%/
echo   Android API URL (USB): http://127.0.0.1:%API_PORT%/
echo   Backend Health Check : http://localhost:%API_PORT%/health
echo   Swagger Documentation: http://localhost:%API_PORT%/docs
echo.
echo   Demo Admin Login:
echo     Email   : admin@sadaksetu.local
echo     Password: Admin@SadakSetu1
echo.
echo   Demo Citizen Login:
echo     Email   : aarav.citizen@gmail.com (or rohan.citizen@example.com)
echo     Password: Citizen123 (or User123)
echo.
echo   Demo Team Lead Login:
echo     Email   : vikram.lead@example.com (or ramesh.lead@gmail.com)
echo     Password: Leader123
echo.
echo ===============================================================
echo   Copy any of the above links into your browser.
echo ===============================================================
echo.
echo   Tip: Press any key to close this launcher console.
pause >nul
exit /b 0

:err_python
echo [ERROR] Python backend environment was not found at:
echo         %PYTHON%
pause
exit /b 1
