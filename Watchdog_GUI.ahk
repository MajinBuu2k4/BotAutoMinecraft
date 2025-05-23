#Persistent
#SingleInstance force
SetBatchLines, -1

psScript := "C:\Users\Administrator\Desktop\BotAutoMinecraft\watchdog.ps1"
logFile := "C:\Users\Administrator\Desktop\BotAutoMinecraft\watchdog-output.log"

Gui, Add, Edit, x10 y10 w780 h400 vLogOutput ReadOnly -VScroll
Gui, Add, Button, x10 y420 w100 gRunWatchdog, Chạy Watchdog
Gui, Add, Button, x120 y420 w100 gRefreshLog, Làm mới log

Gui, Show, w800 h460, Xem Log Watchdog
SetTimer, AutoRefresh, 60000 ; 60 giây (nếu muốn 1 phút thì 60000)
Gosub, RefreshLog
return

RunWatchdog:
    ; Xóa file log trước khi chạy watchdog
    FileDelete, %logFile%
    RunWait, powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "%psScript%" *> "%logFile%", , Hide
    Gosub, RefreshLog
return

RefreshLog:
    if (FileExist(logFile)) {
        FileRead, contents, %logFile%
        GuiControl,, LogOutput, %contents%
    } else {
        GuiControl,, LogOutput, Không tìm thấy log file.
    }
return

AutoRefresh:
    Gosub, RunWatchdog
return

GuiClose:
    ExitApp
