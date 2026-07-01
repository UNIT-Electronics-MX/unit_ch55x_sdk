@echo off
SETLOCAL ENABLEEXTENSIONS

set "SCRIPT_DIR=%~dp0"
if not "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR%\"
set "DOCKER_FILE=%SCRIPT_DIR%docker-compose.yml"
for %%I in ("%SCRIPT_DIR%..") do set "SDK_ROOT=%%~fI\"

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

:pio
if "%2"=="" (
    echo Error: you must specify the PlatformIO project path.
    exit /b 1
)
call "%SDK_ROOT%upgrade.bat" "%~2" %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

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
