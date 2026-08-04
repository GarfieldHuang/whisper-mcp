@echo off
setlocal
cd /d %~dp0
py -3 -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo Installation completed.
echo Python: %CD%\.venv\Scripts\python.exe
endlocal
