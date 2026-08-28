@echo off
rem Provisions {app}\.venv from uv's own *managed* Python 3.12 and installs
rem requirements.txt into it. Staged into {app} alongside launch.bat and
rem invoked directly (no cmd.exe /C wrapper) from setup.iss's [Run] section --
rem see that file's comments for why: cmd.exe's /C argument parsing mishandles
rem a command line that starts with a quoted path and also contains an
rem output redirection, so calling uv this way from a plain [Run] Filename/
rem Parameters pair failed instantly and silently. A real script has no such
rem quoting hazard.
setlocal
set "APPDIR=%~dp0"

"%APPDIR%_bootstrap-uv\uv.exe" venv --python 3.12 --python-preference only-managed "%APPDIR%.venv" >"%APPDIR%_setup-python.log" 2>&1
if errorlevel 1 exit /b 1

"%APPDIR%_bootstrap-uv\uv.exe" pip install --python "%APPDIR%.venv\Scripts\python.exe" -r "%APPDIR%requirements.txt" >>"%APPDIR%_setup-python.log" 2>&1
