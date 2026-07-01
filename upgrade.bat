@echo off
SETLOCAL ENABLEEXTENSIONS

set "SDK_ROOT=%~dp0"
if not "%SDK_ROOT:~-1%"=="\" set "SDK_ROOT=%SDK_ROOT%\"
set "PLATFORM_NAME=unit_ch55x"

if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

set "PROJECT_DIR="
if not "%~1"=="" (
    set "PROJECT_DIR=%~f1"
    if not exist "%~f1\platformio.ini" (
        echo platformio.ini not found in %~f1
        exit /b 1
    )
    shift
)

call :find_pio
call :sync_platformio
if errorlevel 1 exit /b 1

if not "%PROJECT_DIR%"=="" goto :run_pio
exit /b 0

:help
echo Usage:
echo   upgrade.bat
echo   upgrade.bat ^<platformio-project^> [pio args...]
echo(
echo Examples:
echo   upgrade.bat
echo   upgrade.bat .\examples\ws2812 run
echo   upgrade.bat .\examples\ws2812 run -t upload
exit /b 0

:find_pio
set "PIO_CMD="
where pio >nul 2>nul
if not errorlevel 1 (
    set "PIO_CMD=pio"
    exit /b 0
)
where platformio >nul 2>nul
if not errorlevel 1 (
    set "PIO_CMD=platformio"
    exit /b 0
)
if exist "%USERPROFILE%\.platformio\penv\Scripts\pio.exe" (
    set "PIO_CMD=%USERPROFILE%\.platformio\penv\Scripts\pio.exe"
    exit /b 0
)
exit /b 0

:read_json_version
set "%~1="
for /f "usebackq delims=" %%V in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Get-Content -Raw '%~2' | ConvertFrom-Json).version } catch { '' }"`) do set "%~1=%%V"
exit /b 0

:sync_platformio
call :read_json_version SDK_VERSION "%SDK_ROOT%platform.json"
if "%SDK_VERSION%"=="" (
    echo Could not read SDK version from "%SDK_ROOT%platform.json".
    exit /b 1
)

set "PIO_CORE_DIR=%PLATFORMIO_CORE_DIR%"
if "%PIO_CORE_DIR%"=="" set "PIO_CORE_DIR=%USERPROFILE%\.platformio"
set "INSTALLED_DIR=%PIO_CORE_DIR%\platforms\%PLATFORM_NAME%"
set "INSTALLED_JSON=%INSTALLED_DIR%\platform.json"

if not exist "%INSTALLED_JSON%" (
    echo PlatformIO platform %PLATFORM_NAME% is not installed yet.
    exit /b 0
)

call :read_json_version INSTALLED_VERSION "%INSTALLED_JSON%"
if "%INSTALLED_VERSION%"=="%SDK_VERSION%" (
    echo PlatformIO platform %PLATFORM_NAME% is already at %SDK_VERSION%.
    exit /b 0
)

echo Updating PlatformIO platform %PLATFORM_NAME%: %INSTALLED_VERSION% -^> %SDK_VERSION%
if not "%PIO_CMD%"=="" call "%PIO_CMD%" pkg uninstall -g -p "%PLATFORM_NAME%" --skip-dependencies --silent >nul 2>nul
if exist "%INSTALLED_DIR%" rmdir /S /Q "%INSTALLED_DIR%"
exit /b 0

:run_pio
if "%PIO_CMD%"=="" (
    echo PlatformIO was not found. Install PlatformIO or add pio to PATH.
    exit /b 1
)

set "PIO_ARGS="
:collect_args
if "%~1"=="" goto :args_done
set "PIO_ARGS=%PIO_ARGS% "%~1""
shift
goto :collect_args

:args_done
if "%PIO_ARGS%"=="" set "PIO_ARGS=run"

echo Running PlatformIO in: %PROJECT_DIR%
pushd "%PROJECT_DIR%"
call "%PIO_CMD%" %PIO_ARGS%
set "PIO_EXIT=%ERRORLEVEL%"
popd
exit /b %PIO_EXIT%
