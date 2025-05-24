@echo off
:: Kiểm tra quyền admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo Please run this script as Administrator!
    echo Right click and select "Run as administrator"
    pause
    exit /b 1
)

echo Installing Bot Runtime Tracker Service...

:: Dừng service nếu đang chạy
echo Stopping service if running...
net stop "BotRuntimeTracker"
if %errorLevel% == 2 echo Service is not running

:: Xóa service cũ nếu tồn tại
echo Removing existing service...
python "%~dp0runtime_service.py" remove
if %errorLevel% == 0 (
    echo Old service removed successfully
) else (
    echo No existing service found
)

:: Đợi một chút để đảm bảo service đã được dừng và xóa hoàn toàn
timeout /t 2 /nobreak >nul

:: Cài đặt service mới với quyền tự động khởi động
echo Installing new service...
python "%~dp0runtime_service.py" --startup auto install
if %errorLevel% == 0 (
    echo Service installed successfully
) else (
    echo Failed to install service
    pause
    exit /b 1
)

:: Cấu hình quyền và recovery cho service
echo Configuring service permissions and recovery...
:: Thiết lập quyền chạy với tài khoản LocalSystem và các quyền cần thiết
sc config "BotRuntimeTracker" obj= "LocalSystem" start= delayed-auto
sc privs "BotRuntimeTracker" "SeIncreaseQuotaPrivilege/SeSecurityPrivilege/SeTcbPrivilege/SeAssignPrimaryTokenPrivilege/SeChangeNotifyPrivilege/SeCreateGlobalPrivilege/SeIncreaseWorkingSetPrivilege"

:: Thiết lập recovery options
sc failure "BotRuntimeTracker" reset= 86400 actions= restart/0/restart/60000/restart/120000

:: Đợi một chút trước khi khởi động service
timeout /t 2 /nobreak >nul

:: Khởi động service
echo Starting service...
net start "BotRuntimeTracker"
if %errorLevel% == 0 (
    echo Service started successfully
) else (
    echo Failed to start service
    echo Checking service status and error...
    sc query "BotRuntimeTracker"
    echo.
    echo Checking detailed error...
    powershell -Command "Get-WinEvent -FilterHashtable @{LogName='System'; ID=7000,7011,7024,7026,7031,7034,7045} | Where-Object {$_.Message -like '*BotRuntimeTracker*'} | Select-Object TimeCreated,Message -First 5"
)

echo.
echo Installation completed. Please check services.msc to verify.
echo Service Name: Bot Runtime Tracker Service
echo.

:: Hiển thị thông tin chi tiết
sc qc "BotRuntimeTracker"
sc qfailure "BotRuntimeTracker"
sc enumdepend "BotRuntimeTracker"
sc sdshow "BotRuntimeTracker"

pause 