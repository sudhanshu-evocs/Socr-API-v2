# start.ps1 — Launch Flask backend + React frontend simultaneously
# Usage: .\start.ps1 [-EnableSift]
# Run from the project root directory

param(
    [switch]$EnableSift
)

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $ROOT "venv\Scripts\python.exe"
$pythonExecutable = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

# --- Backend ---
Write-Host "[BACKEND] Starting Flask server..." -ForegroundColor Blue
$siftEnabled = $EnableSift -or ($env:ENABLE_SIFT_COMPARISON -match '^(?i:true|1|yes|on)$')
$backendCommand = if ($siftEnabled) {
    "cd '$ROOT'; `$env:PYTHONPATH='$ROOT\src'; `$env:ENABLE_SIFT_COMPARISON='true'; & '$pythonExecutable' -m experimental.sift_comparison.local_app"
} else {
    "cd '$ROOT'; `$env:PYTHONPATH='$ROOT\src'; & '$pythonExecutable' src\docuverus\app.py"
}
if ($siftEnabled) {
    Write-Host "[BACKEND] Experimental SIFT comparison is enabled for this local run." -ForegroundColor Magenta
}
$backendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    $backendCommand
) -PassThru

# --- Frontend ---
Write-Host "[FRONTEND] Starting React dev server..." -ForegroundColor Green
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ROOT\react-app'; npm start"
) -PassThru

Write-Host ""
Write-Host "Both servers started in separate windows." -ForegroundColor Cyan
Write-Host "  Backend  : http://localhost:5000" -ForegroundColor Blue
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Close the respective PowerShell windows to stop each server." -ForegroundColor Yellow
