# dev-with-tunnel.ps1
# One command for Twilio voice testing: ngrok + FastAPI.
#
# Usage (from repo root):
#   .\scripts\dev-with-tunnel.ps1
#   pnpm dev:voice
#
# Do NOT run "ngrok http 8000" separately - this script finds and starts ngrok.

param(
    [int]$ApiPort = 8000,
    [switch]$WithWeb
)

function Resolve-NgrokExe {
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe",
        "$env:ProgramFiles\ngrok\ngrok.exe",
        "$env:USERPROFILE\scoop\apps\ngrok\current\ngrok.exe"
    )

    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }

    $wingetSearch = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ngrok.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($wingetSearch) {
        return $wingetSearch.FullName
    }

    return $null
}

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name  = $Matches[1].Trim()
            $value = $Matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "[info] Loaded .env" -ForegroundColor Cyan
}

function Get-NgrokPublicUrl {
    param([int]$MaxAttempts = 8)
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $tunnels = (Invoke-RestMethod "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3).tunnels
            $https = $tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
            if ($https -and $https.public_url) {
                return $https.public_url
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $null
}

function Stop-StaleNgrok {
    Get-Process ngrok -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "[ngrok] Stopping stale ngrok (pid $($_.Id)) ..." -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
$repoRoot = (Join-Path $PSScriptRoot "..") | Resolve-Path
$envFile  = Join-Path $repoRoot ".env"
Load-DotEnv -Path $envFile

# ---------------------------------------------------------------------------
# Find ngrok (PATH or winget install path - no manual PATH setup needed)
# ---------------------------------------------------------------------------
$ngrokExe = Resolve-NgrokExe
if (-not $ngrokExe) {
    Write-Host ""
    Write-Host "ngrok not installed. Run once:" -ForegroundColor Red
    Write-Host "  winget install ngrok.ngrok" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "[ngrok] Found: $ngrokExe" -ForegroundColor Cyan

if ($env:NGROK_AUTHTOKEN) {
    & $ngrokExe config add-authtoken $env:NGROK_AUTHTOKEN 2>&1 | Out-Null
}
else {
    Write-Warning "NGROK_AUTHTOKEN not set in .env - ngrok may fail. Add it from dashboard.ngrok.com"
}

# ---------------------------------------------------------------------------
# Start ngrok tunnel
# ---------------------------------------------------------------------------
Stop-StaleNgrok

Write-Host "[ngrok] Starting tunnel -> localhost:$ApiPort ..." -ForegroundColor Green

$ngrokArgs = @("http", $ApiPort.ToString(), "--log=stdout")
if ($env:NGROK_AUTHTOKEN) { $ngrokArgs += @("--authtoken", $env:NGROK_AUTHTOKEN) }

$ngrokProc = Start-Process $ngrokExe -ArgumentList $ngrokArgs -PassThru -WindowStyle Minimized

$publicUrl = Get-NgrokPublicUrl
if ($publicUrl) {
    $webhookUrl = "$publicUrl/webhooks/twilio/voice"
    [System.Environment]::SetEnvironmentVariable("PUBLIC_API_BASE_URL", $publicUrl, "Process")

    Write-Host ""
    Write-Host ("=" * 62) -ForegroundColor Yellow
    Write-Host "  READY - call your Twilio number now" -ForegroundColor Green
    Write-Host ("=" * 62) -ForegroundColor Yellow
    Write-Host "  ngrok URL:        $publicUrl" -ForegroundColor Yellow
    Write-Host "  Twilio Voice URL: $webhookUrl" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Also save in .env (for next restart):" -ForegroundColor Cyan
    Write-Host "  PUBLIC_API_BASE_URL=$publicUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "  Logs appear below when you call." -ForegroundColor Cyan
    Write-Host "  ngrok inspector: http://127.0.0.1:4040" -ForegroundColor Cyan
    Write-Host ("=" * 62) -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Warning "Could not read ngrok URL. Open http://127.0.0.1:4040 and check authtoken."
}

# ---------------------------------------------------------------------------
# Start dev server(s)
# ---------------------------------------------------------------------------
Set-Location $repoRoot

if ($WithWeb) {
    Write-Host "[dev] Starting FastAPI + Next.js ..." -ForegroundColor Green
    $devCmd = { pnpm run dev }
}
else {
    Write-Host "[dev] Starting FastAPI only (voice testing) ..." -ForegroundColor Green
    $devCmd = { pnpm --filter @ai-voice/api dev }
}

Write-Host "[dev] Press Ctrl+C to stop.`n" -ForegroundColor Cyan

try {
    & $devCmd
}
finally {
    Write-Host "`n[info] Stopping ngrok ..." -ForegroundColor Cyan
    if ($ngrokProc -and -not $ngrokProc.HasExited) {
        Stop-Process -Id $ngrokProc.Id -Force -ErrorAction SilentlyContinue
    }
    Stop-StaleNgrok
    Write-Host "[info] Done." -ForegroundColor Cyan
}
