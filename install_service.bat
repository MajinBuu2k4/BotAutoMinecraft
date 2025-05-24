@echo off
echo Installing Bot Runtime Tracker service...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator!
    pause
    exit /b 1
)

REM Try to find Python path using multiple methods
set "PYTHON_PATH="

REM Method 1: Check Python 3.11 in registry
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set "PYTHON_PATH=%%b"

REM Method 2: Check Python 3.11 in registry (32-bit)
if not defined PYTHON_PATH (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set "PYTHON_PATH=%%b"
)

REM Method 3: Check Python 3.11 in user registry
if not defined PYTHON_PATH (
    for /f "tokens=2*" %%a in ('reg query "HKCU\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set "PYTHON_PATH=%%b"
)

REM Method 4: Try to find Python using where command
if not defined PYTHON_PATH (
    for /f "tokens=*" %%a in ('where python 2^>nul') do (
        set "PYTHON_PATH=%%~dpa"
        goto :found_python
    )
)
:found_python

REM Method 5: Check common installation paths
if not defined PYTHON_PATH (
    if exist "C:\Python311\python.exe" set "PYTHON_PATH=C:\Python311\"
    if exist "C:\Program Files\Python311\python.exe" set "PYTHON_PATH=C:\Program Files\Python311\"
    if exist "C:\Program Files (x86)\Python311\python.exe" set "PYTHON_PATH=C:\Program Files (x86)\Python311\"
)

REM Check if Python was found
if not defined PYTHON_PATH (
    echo Python not found! Please make sure Python 3.11 is installed and added to PATH
    echo Current PATH: %PATH%
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_PATH%

REM Install required Python package
"%PYTHON_PATH%python.exe" -m pip install --upgrade pip
"%PYTHON_PATH%python.exe" -m pip install pywin32 pywin32-ctypes

REM Change to service directory and install service
cd service
echo Installing service...
"%PYTHON_PATH%python.exe" setup_service.py install
if %errorLevel% neq 0 (
    echo Failed to install service!
    pause
    exit /b 1
)

echo Service installed and started successfully!
pause 