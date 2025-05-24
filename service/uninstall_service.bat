@echo off
echo Uninstalling Bot Runtime Tracker service...

REM Stop and remove the service
python runtime_service.py stop
python runtime_service.py remove

echo Service uninstalled successfully!
pause 