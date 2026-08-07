@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
  py app.py
  goto :eof
)

where python >nul 2>&1
if %errorlevel%==0 (
  python app.py
  goto :eof
)

echo Python was not found on this PC.
echo Please install Python 3 from python.org and make sure "Add Python to PATH" is enabled.
pause
