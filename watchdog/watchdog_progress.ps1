# Đường dẫn file log
$logFile = "C:\Users\Administrator\Desktop\BotAutoMinecraft\watchdog\watchdog-progress-output.log"

function Write-Log {
    param (
        [string]$message
    )
    Write-Host $message
    $message | Out-File -FilePath $logFile -Encoding utf8 -Append
}

function Format-TimeSpan {
    param (
        [TimeSpan]$timeSpan
    )
    if ($timeSpan.TotalHours -ge 1) {
        return "{0:D2}:{1:D2}:{2:D2}" -f $timeSpan.Hours, $timeSpan.Minutes, $timeSpan.Seconds
    } elseif ($timeSpan.TotalMinutes -ge 1) {
        return "{0:D2}:{1:D2}" -f $timeSpan.Minutes, $timeSpan.Seconds
    } else {
        return "{0}s" -f $timeSpan.Seconds
    }
}

# Nếu muốn xóa log cũ mỗi lần chạy, bỏ comment dòng dưới
# Clear-Content -Path $logFile -ErrorAction SilentlyContinue

$maxBot = 15

$botList = 1..$maxBot | ForEach-Object {
    $id = "{0:D2}" -f $_
    [PSCustomObject]@{
        Name    = "Vanguard$id"
        ExePath = "C:\Users\Administrator\Desktop\BotAutoMinecraft\node\Vanguard$id.exe"
        Script  = "C:\Users\Administrator\Desktop\BotAutoMinecraft\bots\Vanguard$id.js"
    }
}

foreach ($bot in $botList) {
    $name   = $bot.Name
    $exe    = $bot.ExePath
    $script = $bot.Script

    # Kiểm tra tiến trình bot
    $process = Get-Process | Where-Object { $_.Path -eq $exe } -ErrorAction SilentlyContinue

    if ($process) {
        $timeSpan = New-TimeSpan -Start $process.StartTime -End (Get-Date)
        $formattedTime = Format-TimeSpan -timeSpan $timeSpan
        Write-Log "✅ [$name] OK ($formattedTime trước)"
    } else {
        Write-Log "❌ [$name] offline"
    }
}
