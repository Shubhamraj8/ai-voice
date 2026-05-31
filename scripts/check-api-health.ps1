# Quick health check for local or Render API (ticket 1.17 verification)
param(
    [string]$BaseUrl = "http://localhost:8000"
)

$uri = "$BaseUrl.TrimEnd('/')/health"
Write-Host "GET $uri"

try {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 30
    $sw.Stop()
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Time:   $($sw.ElapsedMilliseconds) ms"
    Write-Host "Body:   $($response.Content)"
    if ($response.StatusCode -ne 200) { exit 1 }
    if ($sw.ElapsedMilliseconds -gt 200) {
        Write-Host "WARN: slower than 200ms target (may be cold start on Render free tier)"
    }
} catch {
    Write-Host "FAIL: $($_.Exception.Message)"
    exit 1
}
