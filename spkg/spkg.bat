@echo off
SETLOCAL ENABLEEXTENSIONS

set "SCRIPT_DIR=%~dp0"
if not "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR%\"
set "DOCKER_FILE=%SCRIPT_DIR%docker-compose.yml"
for %%I in ("%SCRIPT_DIR%..") do set "SDK_ROOT=%%~fI\"
set "PLATFORM_NAME=unit_ch55x"

echo SCRIPT_DIR is [%SCRIPT_DIR%]
echo DOCKER_FILE is [%DOCKER_FILE%]

if "%1"=="" goto :help

if "%1"=="--version" goto :version
if "%1"=="--help" goto :help
if "%1"=="compose" goto :compose
if "%1"=="cop" goto :compose
if "%1"=="init" goto :init
if "%1"=="pio" goto :pio
if "%1"=="-p" goto :build

goto :help

:version
echo spkg version 1.0.0
exit /b

:help
echo(
echo spkg - CH552 SDK CLI Tool (Windows)
echo(
echo Usage:
echo   spkg -p ^<path^> [command]    Run 'make [command]' in the path
echo   spkg pio ^<path^> [args...]   Run PlatformIO and refresh the local platform
echo   spkg compose                  Build the Docker image
echo   spkg init ^<path^>            Create new project from template_project
echo   spkg --version                Show version
echo   spkg --help                   Show this help
echo(
exit /b

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
exit /b 1

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

if not exist "%INSTALLED_JSON%" exit /b 0

call :read_json_version INSTALLED_VERSION "%INSTALLED_JSON%"
if "%INSTALLED_VERSION%"=="%SDK_VERSION%" exit /b 0

echo Updating PlatformIO platform %PLATFORM_NAME%: %INSTALLED_VERSION% -^> %SDK_VERSION%
call "%PIO_CMD%" pkg uninstall -g -p "%PLATFORM_NAME%" --skip-dependencies --silent >nul 2>nul
if exist "%INSTALLED_DIR%" rmdir /S /Q "%INSTALLED_DIR%"
exit /b 0

:pio
if "%2"=="" (
    echo Error: you must specify the PlatformIO project path.
    exit /b 1
)

set "PROJECT_DIR=%~f2"
if not exist "%PROJECT_DIR%\platformio.ini" (
    echo Error: platformio.ini not found in %PROJECT_DIR%
    exit /b 1
)

call :find_pio
if errorlevel 1 (
    echo Error: PlatformIO was not found. Install PlatformIO or add pio to PATH.
    exit /b 1
)

call :sync_platformio
if errorlevel 1 exit /b 1

set "PIO_ARGS=%3 %4 %5 %6 %7 %8 %9"
if "%3"=="" set "PIO_ARGS=run"

echo Running PlatformIO in: %PROJECT_DIR%
pushd "%PROJECT_DIR%"
call "%PIO_CMD%" %PIO_ARGS%
set "PIO_EXIT=%ERRORLEVEL%"
popd
exit /b %PIO_EXIT%

:init
if "%2"=="" (
    echo Error: destination path is missing.
    exit /b
)
if exist "%2" (
    echo Error: directory "%2" already exists.
    exit /b
)
echo Creating new project at "%2"...
xcopy /E /I /Y "%SCRIPT_DIR%template_project" "%2"
echo Project created.
exit /b

:compose
echo Building Docker image from: %DOCKER_FILE%
call docker compose -f "%DOCKER_FILE%" build
if errorlevel 1 (
    echo Docker Compose build failed.
) else (
    echo Docker image built successfully.
)
exit /b

:build
if "%2"=="" (
    echo Error: you must specify the project path.
    exit /b
)

set "PROJECT_DIR=%~f2"
set "MAKE_CMD=%3"
if "%MAKE_CMD%"=="" set MAKE_CMD=bin

if not exist "%PROJECT_DIR%\Makefile" (
    echo Error: Makefile not found in %PROJECT_DIR%
    exit /b
)

echo Running 'make %MAKE_CMD%' in: %PROJECT_DIR%

docker compose -f "%DOCKER_FILE%" run --rm ^
    -v "%PROJECT_DIR%:/project" ^
    --workdir /project ^
    ch552_compiler make %MAKE_CMD%

IF EXIST "%PROJECT_DIR%\build\main.bin" (
    echo Build successful: %PROJECT_DIR%\build\main.bin generated.
) ELSE (
    echo Error: build failed.
)
exit /b
