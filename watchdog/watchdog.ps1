$logFile = "C:\Users\Administrator\Desktop\BotAutoMinecraft\watchdog\watchdog-output.log"

function Write-Log {
    param (
        [string]$message
    )
    Write-Host $message
    $message | Out-File -FilePath $logFile -Encoding utf8 -Append
}


# Nếu muốn xóa log cũ mỗi lần chạy, uncomment dòng dưới
# Clear-Content -Path $logFile -ErrorAction SilentlyContinue

$maxBot = 15

$botList = 1..$maxBot | ForEach-Object {
    $id = "{0:D2}" -f $_
    [PSCustomObject]@{
        Name    = "Vanguard$id"
        LogPath = "C:\Users\Administrator\Desktop\BotAutoMinecraft\bots\logs\Vanguard$id.log"
        ExePath = "C:\Users\Administrator\Desktop\BotAutoMinecraft\node\Vanguard$id.exe"
        Script  = "C:\Users\Administrator\Desktop\BotAutoMinecraft\bots\Vanguard$id.js"
    }
}

foreach ($bot in $botList) {
    $name   = $bot.Name
    $log    = $bot.LogPath
    $exe    = $bot.ExePath
    $script = $bot.Script
    $needRestart = $false

    # Kiểm tra log
    if (Test-Path $log) {
        $lastWrite = (Get-Item $log).LastWriteTime
        $secondsAgo = (New-TimeSpan -Start $lastWrite -End (Get-Date)).TotalSeconds
        $lastLine = Get-Content $log -Tail 1

        if ($secondsAgo -gt 15) {
            Write-Log "⏰ [$name] log quá cũ ($([math]::Round($secondsAgo))s) → restart"
            $needRestart = $true
        } elseif ($lastLine -notmatch 'ALIVE-INGAME') {
            Write-Log "📄 [$name] trạng thái không ổn ($lastLine) → restart"
            $needRestart = $true
        } else {
            Write-Log "✅ [$name] OK ($([math]::Round($secondsAgo))s trước)"
        }
    } else {
        Write-Log "❌ [$name] chưa có log → cần chạy"
        $needRestart = $true
    }

    # Kiểm tra tiến trình bot
    $process = Get-Process | Where-Object { $_.Path -eq $exe } -ErrorAction SilentlyContinue

    if (-not $process) {
        Write-Log "🛠 [$name] chưa chạy → khởi động"
        Start-Process -FilePath $exe -ArgumentList $script -WindowStyle Minimized
    } elseif ($needRestart) {
        Write-Log "🔄 [$name] cần restart..."
        Stop-Process -Id $process.Id -Force
        Start-Process -FilePath $exe -ArgumentList $script -WindowStyle Minimized
    }
}
