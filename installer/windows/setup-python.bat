@echo off
rem Provisions {app}\.venv from uv's own *managed* Python 3.12 and installs
rem requirements.txt into it. Staged into {app} alongside launch.bat and
rem invoked via setup.iss's [Run] section as `cmd.exe /C "{app}\setup-python.bat"`
rem -- see that file's comments for why a plain cmd.exe /C wrapper, and why not
rem an inline cmd.exe /C uv command.
rem
rem Writes a heartbeat line to _setup-python.log before and after each uv call
rem (each with its own >>, so it's flushed to disk immediately, not held open)
rem so a CI run that has to be killed for taking too long still leaves behind
rem evidence of exactly how far this script got -- see the "Diagnostic -- dump
rem state if the silent install is still running" step in
rem .github/workflows/build-installers.yml, which reads this file even when
rem the install step itself was killed by its own timeout before it could.
rem
rem Each uv call's exit code is captured into a variable *immediately* after
rem it runs -- before any other command, including the heartbeat `echo` --
rem because any intervening command overwrites %errorlevel% with its own
rem result. Checking `if errorlevel 1` after an echo would silently check
rem echo's exit code (almost always 0), not uv's -- this script used to have
rem exactly that bug for the venv step, and never checked the pip install
rem step's result at all. setup.iss's [Run] entry for this script depends on
rem a genuinely non-zero exit code here to know installation failed and stop
rem before running bootstrap.py -- see that file's [Run] comments.
setlocal
set "APPDIR=%~dp0"

echo [setup-python.bat] starting uv venv >"%APPDIR%_setup-python.log"
"%APPDIR%_bootstrap-uv\uv.exe" venv --python 3.12 --python-preference only-managed "%APPDIR%.venv" >>"%APPDIR%_setup-python.log" 2>&1
set "VENV_EXIT=%errorlevel%"
echo [setup-python.bat] uv venv exit=%VENV_EXIT% >>"%APPDIR%_setup-python.log"
if not "%VENV_EXIT%"=="0" (
    echo [setup-python.bat] aborting -- uv venv failed, not attempting dependency install >>"%APPDIR%_setup-python.log"
    exit /b %VENV_EXIT%
)

echo [setup-python.bat] starting uv pip install >>"%APPDIR%_setup-python.log"
"%APPDIR%_bootstrap-uv\uv.exe" pip install --python "%APPDIR%.venv\Scripts\python.exe" -r "%APPDIR%requirements.txt" >>"%APPDIR%_setup-python.log" 2>&1
set "PIP_EXIT=%errorlevel%"
echo [setup-python.bat] uv pip install exit=%PIP_EXIT% >>"%APPDIR%_setup-python.log"
if not "%PIP_EXIT%"=="0" (
    echo [setup-python.bat] aborting -- uv pip install failed >>"%APPDIR%_setup-python.log"
    exit /b %PIP_EXIT%
)

exit /b 0
