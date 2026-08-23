@echo off
setlocal

rem Socials Studio launcher (Windows). Opens a terminal in the install
rem directory and starts Claude Code there. This never logs into a
rem platform, publishes anything, or runs the installer/bootstrap.py setup
rem again -- that already ran once, at install time.

cd /d "%~dp0"

where claude >nul 2>nul
if errorlevel 1 (
    echo.
    echo Claude Code was not found on PATH.
    echo Install it from https://claude.com/claude-code, sign in with a
    echo qualifying Claude account, then run this launcher again.
    echo.
    pause
    exit /b 1
)

echo Starting Socials Studio...
echo.
claude
pause
