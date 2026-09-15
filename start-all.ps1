$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Building frontend ===" -ForegroundColor Cyan
Push-Location "$root\frontend"
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "Frontend build failed!" -ForegroundColor Red; exit 1 }
Pop-Location

Write-Host "=== Starting backend (port 5000) ===" -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:root\backend
    python run.py 2>&1
}

Write-Host "=== Starting ngrok (port 5000) ===" -ForegroundColor Cyan
$ngrokJob = Start-Job -ScriptBlock {
    ngrok http 5000 --log stdout --log-level info 2>&1
}

Write-Host ""
Write-Host "All services started! Press Ctrl+C to stop." -ForegroundColor Green
Write-Host ""

try {
    while ($true) {
        # Stream output from both jobs into this terminal
        Receive-Job -Job $backendJob -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "[backend] $_" -ForegroundColor Yellow
        }
        Receive-Job -Job $ngrokJob -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "[ngrok]   $_" -ForegroundColor Cyan
        }

        # If either job failed, show it
        if ($backendJob.State -eq 'Failed') {
            Write-Host "[backend] JOB FAILED" -ForegroundColor Red
            Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        }
        if ($ngrokJob.State -eq 'Failed') {
            Write-Host "[ngrok]   JOB FAILED" -ForegroundColor Red
            Receive-Job -Job $ngrokJob -ErrorAction SilentlyContinue
        }

        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`nStopping all services..." -ForegroundColor Red
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $ngrokJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $ngrokJob -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped." -ForegroundColor Red
}
