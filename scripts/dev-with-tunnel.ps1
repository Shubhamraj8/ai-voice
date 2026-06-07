# dev-with-tunnel.ps1
# Starts ngrok tunnel + FastAPI + Next.js with a single command.
#
# Usage (from repo root):
#   .\scripts\dev-with-tunnel.ps1
#
# Prerequisites:
#   - ngrok installed and on PATH  (winget install ngrok  OR  choco install ngrok)
#   - Python deps installed        (pip install -r apps/api/requirements.txt)
#   - .env populated               (cp .env.example .env, then fill values)

param(
    [int]$ApiPort  = 8000,
    [int]$WebPort  = 3000
)

# ---------------------------------------------------------------------------
# Load .env so we can use NGROK_AUTHTOKEN etc. in this shell session
# ---------------------------------------------------------------------------
$envFile = Join-Path $PSScriptRoot ".." ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name  = $Matches[1].Trim()
            $value = $Matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "[info] Loaded .env" -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# Verify ngrok is available
# ---------------------------------------------------------------------------
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Error @"
ngrok not found on PATH.

Install it with one of:
  winget install ngrok.ngrok
  choco install ngrok
  scoop install ngrok

Or download from https://ngrok.com/download and add to PATH.
"@
    exit 1
}

# ---------------------------------------------------------------------------
# Start ngrok in background
# ---------------------------------------------------------------------------
Write-Host "[ngrok] Starting tunnel → localhost:$ApiPort ..." -ForegroundColor Green

$ngrokArgs = @("http", $ApiPort.ToString(), "--log=stdout")
if ($env:NGROK_AUTHTOKEN) { $ngrokArgs += @("--authtoken", $env:NGROK_AUTHTOKEN) }
if ($env:NGROK_SUBDOMAIN)  { $ngrokArgs += @("--subdomain",  $env:NGROK_SUBDOMAIN)  }

$ngrokProc = Start-Process ngrok -ArgumentList $ngrokArgs -PassThru -WindowStyle Minimized

# Give ngrok a moment to establish the tunnel
Start-Sleep -Seconds 2

# Fetch the public URL from ngrok's local API
try {
    $tunnels   = (Invoke-RestMethod "http://127.0.0.1:4040/api/tunnels").tunnels
    $publicUrl = ($tunnels | Where-Object { $_.proto -eq "https" })[0].public_url
    $webhookUrl = "$publicUrl/webhooks/twilio/voice"

    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host "  ngrok tunnel:   $publicUrl" -ForegroundColor Yellow
    Write-Host "  Twilio webhook: $webhookUrl" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Paste the webhook URL into Twilio Console:" -ForegroundColor Yellow
    Write-Host "  Phone Numbers → Manage → Active Numbers → Voice URL" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host ""
}
catch {
    Write-Warning "Could not fetch ngrok URL — tunnel may still be starting."
    Write-Warning "Check http://127.0.0.1:4040 in your browser."
}

# ---------------------------------------------------------------------------
# Start FastAPI + Next.js via pnpm dev (concurrently)
# ---------------------------------------------------------------------------
Write-Host "[dev] Starting FastAPI + Next.js ..." -ForegroundColor Green
Write-Host "[dev] Press Ctrl+C to stop everything.`n" -ForegroundColor Cyan

try {
    # Run pnpm dev in the foreground so Ctrl+C kills all children
    & pnpm run dev
}
finally {
    Write-Host "`n[info] Stopping ngrok ..." -ForegroundColor Cyan
    Stop-Process -Id $ngrokProc.Id -ErrorAction SilentlyContinue
    Write-Host "[info] Done." -ForegroundColor Cyan
}
