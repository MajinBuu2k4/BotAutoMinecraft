$logFile = "C:\Users\Administrator\Desktop\BotAutoMinecraft\watchdog\watchdog-output.log"

function Write-Log {
    param (
        [string]$message
    )
    Write-Host $message
    $message | Out-File -FilePath $logFile -Encoding utf8 -Append
}

# Xóa log cũ mỗi lần chạy
Clear-Content -Path $logFile -ErrorAction SilentlyContinue

$maxBot = 15

# Tạo danh sách bot
$botList = 1..$maxBot | ForEach-Object {
    $id = "{0:D2}" -f $_
    [PSCustomObject]@{
        Name    = "Vanguard$id"
        LogPath = "C:\Users\Administrator\Desktop\BotAutoMinecraft\bots\logs\Vanguard$id.log"
        ExePath = "C:\Users\Administrator\Desktop\BotAutoMinecraft\node\Vanguard$id.exe"
        Script  = "C:\Users\Administrator\Desktop\BotAutoMinecraft\bots\Vanguard$id.js"
    }
}

# Lấy tất cả processes Vanguard một lần
$allProcesses = Get-Process | Where-Object { $_.Path -like "*Vanguard*.exe" } -ErrorAction SilentlyContinue

foreach ($bot in $botList) {
    $name   = $bot.Name
    $log    = $bot.LogPath
    $exe    = $bot.ExePath
    $script = $bot.Script
    $needRestart = $false

    # Tìm process trong danh sách đã lọc
    $process = $allProcesses | Where-Object { $_.Path -eq $exe }

    # Kiểm tra log nếu process đang chạy hoặc file log tồn tại
    if ((Test-Path $log) -and ($process -or !(Test-Path $log))) {
        try {
            $lastWrite = (Get-Item $log).LastWriteTime
            $secondsAgo = (New-TimeSpan -Start $lastWrite -End (Get-Date)).TotalSeconds
            
            # Đọc dòng cuối cùng của log hiệu quả hơn
            $lastLine = Get-Content $log -Tail 1 -ErrorAction Stop

            if ($secondsAgo -gt 15) {
                Write-Log "⏰ [$name] log quá cũ ($([math]::Round($secondsAgo))s) → restart"
                $needRestart = $true
            }
            elseif ($lastLine -notmatch 'ALIVE-INGAME') {
                Write-Log "📄 [$name] trạng thái không ổn ($lastLine) → restart"
                $needRestart = $true
            }
            else {
                Write-Log "✅ [$name] OK ($([math]::Round($secondsAgo))s trước)"
            }
        }
        catch {
            Write-Log "❌ [$name] lỗi đọc log → restart"
            $needRestart = $true
        }
    }
    else {
        Write-Log "❌ [$name] chưa có log → cần chạy"
        $needRestart = $true
    }

    # Xử lý khởi động/restart bot
    if (-not $process) {
        Write-Log "🛠 [$name] chưa chạy → khởi động"
        Start-Process -FilePath $exe -ArgumentList $script -WindowStyle Minimized
    }
    elseif ($needRestart) {
        Write-Log "🔄 [$name] cần restart..."
        Stop-Process -Id $process.Id -Force
        Start-Process -FilePath $exe -ArgumentList $script -WindowStyle Minimized
    }
}
