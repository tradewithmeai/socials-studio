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
setlocal
set "APPDIR=%~dp0"

echo [setup-python.bat] starting uv venv >"%APPDIR%_setup-python.log"
"%APPDIR%_bootstrap-uv\uv.exe" venv --python 3.12 --python-preference only-managed "%APPDIR%.venv" >>"%APPDIR%_setup-python.log" 2>&1
echo [setup-python.bat] uv venv exit=%errorlevel% >>"%APPDIR%_setup-python.log"
if errorlevel 1 exit /b 1

echo [setup-python.bat] starting uv pip install >>"%APPDIR%_setup-python.log"
"%APPDIR%_bootstrap-uv\uv.exe" pip install --python "%APPDIR%.venv\Scripts\python.exe" -r "%APPDIR%requirements.txt" >>"%APPDIR%_setup-python.log" 2>&1
echo [setup-python.bat] uv pip install exit=%errorlevel% >>"%APPDIR%_setup-python.log"
