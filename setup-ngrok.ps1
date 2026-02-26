# ngrok Setup Script for Gerrys-Game
# This script helps you quickly set up ngrok for hosting the app

param(
    [string]$BackendUrl = "",
    [string]$FrontendUrl = ""
)

$envLocalPath = "$PSScriptRoot\.env.local"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ngrok Setup Script - Gerrys-Game" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to parse ngrok URL and extract domain and protocol
function Parse-NgrokUrl {
    param([string]$Url)
    
    $url = $Url.Trim()
    
    # Extract protocol
    if ($url -match '^(https?)://') {
        $protocol = $matches[1]
        $domainWithPort = $url -replace '^https?://', '' -replace ':.*$', ''
    }
    else {
        $protocol = "https"
        $domainWithPort = $url -replace ':.*$', ''
    }
    
    return @{
        Protocol = $protocol
        Domain = $domainWithPort
        Port = 443
    }
}

# If URLs provided as parameters, use them
if ($BackendUrl) {
    $backend = Parse-NgrokUrl $BackendUrl
    
    Write-Host "Updating .env.local with ngrok backend URL..." -ForegroundColor Yellow
    Write-Host "Backend: $($backend.Protocol)://$($backend.Domain):$($backend.Port)" -ForegroundColor Green
    
    $content = @"
# Local development environment variables
# ngrok backend URL (https with port 443)
VUE_APP_BACKEND_IP=$($backend.Domain)
VUE_APP_BACKEND_PORT=$($backend.Port)
VUE_APP_BACKEND_PROTOCOL=$($backend.Protocol)
"@
    
    Set-Content -Path $envLocalPath -Value $content
    Write-Host ".env.local updated successfully!" -ForegroundColor Green
}
else {
    Write-Host "MANUAL NGROK SETUP GUIDE" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Step 1: Start ngrok tunnels"
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "Terminal 1 (Backend):" -ForegroundColor Green
    Write-Host "  cd backend"
    Write-Host "  python run.py"
    Write-Host ""
    Write-Host "Terminal 2 (Frontend):" -ForegroundColor Green
    Write-Host "  cd frontend"
    Write-Host "  npm run serve"
    Write-Host ""
    Write-Host "Terminal 3 (ngrok for backend):" -ForegroundColor Green
    Write-Host "  ngrok http 5000"
    Write-Host ""
    Write-Host "Step 2: Copy the ngrok URL"
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "From the ngrok output, copy the Forwarding URL (https://...)"
    Write-Host ""
    Write-Host "Step 3: Update environment or run this script"
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "Either:"
    Write-Host "  Option A - Edit .env.local manually in $envLocalPath"
    Write-Host ""
    Write-Host "  Option B - Run this script with your ngrok URL:"
    Write-Host "  .\setup-ngrok.ps1 -BackendUrl 'https://xxxx-xx-xxx-xx-xxxx.ngrok.io'"
    Write-Host ""
    Write-Host "EXAMPLE .env.local for ngrok:" -ForegroundColor Yellow
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host "VUE_APP_BACKEND_IP=xxxx-xx-xxx-xx-xxxx.ngrok.io" -ForegroundColor Gray
    Write-Host "VUE_APP_BACKEND_PORT=443" -ForegroundColor Gray
    Write-Host "VUE_APP_BACKEND_PROTOCOL=https" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Note: ngrok uses HTTPS and port 443 by default!" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup complete! The frontend will now use the configured backend URL." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
