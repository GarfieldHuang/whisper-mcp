@echo off
REM Set up whisper-mcp. Downloads Python first if the machine has none.
REM
REM ASCII-only on purpose: cmd.exe parses .bat with the OEM codepage
REM (Big5 on zh-TW), which mangles UTF-8 Chinese into garbage commands.
REM
REM Uses curl.exe (shipped with Windows 10 1803+) rather than PowerShell,
REM which corporate Group Policy commonly blocks.
setlocal
cd /d "%~dp0"

set "PYVER=3.12.10"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"

set "PYEXE="
call :find_python
if defined PYEXE goto have_python

echo.
echo No Python 3.10+ found on this machine.
echo Installing Python %PYVER% for the current user only - no administrator
echo rights needed, and nothing outside your own profile is touched.
echo.
call :install_python
if errorlevel 1 exit /b 1

call :find_python
if not defined PYEXE (
    echo [ERROR] Python still not found after installation.
    echo         Install it manually from https://www.python.org/downloads/
    exit /b 1
)

:have_python
echo Using Python: %PYEXE%
"%PYEXE%" -c "import sys;print('Version:', sys.version.split()[0])"

echo.
echo Creating virtual environment...
"%PYEXE%" -m venv .venv
if errorlevel 1 exit /b 1

echo Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Installation completed.
echo Python: %CD%\.venv\Scripts\python.exe
echo Server: %CD%\server.py
echo.
echo Use those two paths for the MCP command and args fields.
exit /b 0


REM ---------------------------------------------------------------
REM Locate a usable Python. Sets PYEXE when one is 3.10 or newer.
REM ---------------------------------------------------------------
:find_python
set "CAND="
for /f "delims=" %%I in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "CAND=%%I"
call :accept_if_new
if defined PYEXE goto :eof

set "CAND="
for /f "delims=" %%I in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "CAND=%%I"
call :accept_if_new
if defined PYEXE goto :eof

REM A freshly installed per-user copy is not on PATH in this session yet.
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "CAND=%%D\python.exe"
        call :accept_if_new
    )
)
goto :eof

:accept_if_new
if not defined CAND goto :eof
if defined PYEXE goto :eof
"%CAND%" -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYEXE=%CAND%"
set "CAND="
goto :eof


REM ---------------------------------------------------------------
REM Download and install Python for the current user.
REM ---------------------------------------------------------------
:install_python
set "PYTMP=%TEMP%\python-%PYVER%-amd64.exe"

echo Downloading %PYURL%
REM --ssl-no-revoke: corporate MITM proxies break curl's certificate
REM revocation check with CERT_TRUST_REVOCATION_STATUS_UNKNOWN.
curl -L --ssl-no-revoke --fail --progress-bar -o "%PYTMP%" "%PYURL%"
if errorlevel 1 (
    echo.
    echo [ERROR] Download failed.
    echo         Install Python 3.10+ manually from
    echo         https://www.python.org/downloads/
    echo         then run setup.bat again.
    exit /b 1
)

echo Running the installer, this takes a minute...
REM InstallAllUsers=0 keeps it per-user so no admin prompt appears.
start /wait "" "%PYTMP%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0
set "RC=%ERRORLEVEL%"
del "%PYTMP%" >nul 2>&1

if not "%RC%"=="0" (
    echo [ERROR] Installer exited with code %RC%.
    exit /b 1
)
goto :eof
