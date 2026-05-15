@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ASCII-only .bat: safe for cmd on Chinese Windows (no UTF-8 parse bugs)
chcp 65001 >nul 2>&1
title Copy Generator

cd /d "%~dp0"

call :setup_node_env

echo.
echo   ========================================
echo   Academic Copy Studio
echo   ========================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv not found. Install: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo [1/4] Sync Python dependencies...
uv sync --quiet 2>nul
if errorlevel 1 (
    echo       retrying uv sync...
    uv sync
    if errorlevel 1 (
        echo [ERROR] uv sync failed
        pause
        exit /b 1
    )
)

echo [2/4] Build frontend (Vue)...
if not defined NPM_CMD (
    echo [ERROR] npm not found. Check nvm: nvm use ^<version^>
    echo         NVM_SYMLINK should point to your active node folder.
    pause
    exit /b 1
)

echo       node: !NODE_VER!
echo       npm:  !NPM_CMD!

pushd web\frontend
call "!NPM_CMD!" install --silent 2>nul
if errorlevel 1 (
    echo [!] npm install had warnings, continuing...
)
call "!NPM_CMD!" run build
if errorlevel 1 (
    echo [!] Frontend build failed - may show build-required page
)
popd

echo [3/4] Free port 8765...
uv run python scripts\free_port.py 8765

echo [4/4] Start server...
echo.
echo   URL: http://127.0.0.1:8765
echo   Stop: Ctrl+C
echo.

timeout /t 1 /nobreak >nul
start "" http://127.0.0.1:8765

uv run python -m uvicorn web.server:app --host 127.0.0.1 --port 8765

pause
endlocal
exit /b 0

REM ---------------------------------------------------------------------------
REM Prefer nvm-windows (NVM_SYMLINK) over Cursor/other node on PATH
REM ---------------------------------------------------------------------------
:setup_node_env
set "NPM_CMD="
set "NODE_VER=unknown"

if not defined NVM_HOME (
    for /f "skip=2 tokens=2,*" %%a in ('reg query "HKCU\Environment" /v NVM_HOME 2^>nul') do set "NVM_HOME=%%b"
)
if not defined NVM_SYMLINK (
    for /f "skip=2 tokens=2,*" %%a in ('reg query "HKCU\Environment" /v NVM_SYMLINK 2^>nul') do set "NVM_SYMLINK=%%b"
)

if defined NVM_HOME for %%a in ("!NVM_HOME!") do set "NVM_HOME=%%~a"
if defined NVM_SYMLINK for %%a in ("!NVM_SYMLINK!") do set "NVM_SYMLINK=%%~a"

if defined NVM_SYMLINK if exist "!NVM_SYMLINK!\npm.cmd" (
    set "PATH=!NVM_SYMLINK!;%PATH%"
    set "NPM_CMD=!NVM_SYMLINK!\npm.cmd"
    if exist "!NVM_SYMLINK!\node.exe" (
        for /f "delims=" %%v in ('"!NVM_SYMLINK!\node.exe" -v 2^>nul') do set "NODE_VER=%%v"
    )
    exit /b 0
)

REM Symlink missing: try nvm use current (needs NVM_HOME)
if defined NVM_HOME if exist "!NVM_HOME!\nvm.exe" (
    for /f "tokens=*" %%v in ('"!NVM_HOME!\nvm.exe" current 2^>nul') do (
        echo       activating nvm: %%v
        call "!NVM_HOME!\nvm.exe" use %%v >nul 2>&1
    )
    if exist "!NVM_SYMLINK!\npm.cmd" (
        set "PATH=!NVM_SYMLINK!;%PATH%"
        set "NPM_CMD=!NVM_SYMLINK!\npm.cmd"
        for /f "delims=" %%v in ('"!NVM_SYMLINK!\node.exe" -v 2^>nul') do set "NODE_VER=%%v"
        exit /b 0
    )
)

REM Fallback: first npm on PATH (after nvm setup failed)
for /f "delims=" %%p in ('where npm 2^>nul') do (
    if not defined NPM_CMD set "NPM_CMD=%%p"
)
if defined NPM_CMD (
    for /f "delims=" %%v in ('node -v 2^>nul') do set "NODE_VER=%%v"
)
exit /b 0
