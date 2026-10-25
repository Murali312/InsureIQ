# PowerShell Script to Execute the India Health Insurance AI Agent Test Suite
param(
    [string]$TestPath = "tests",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment python not found at $VenvPython. Falling back to system python."
    $VenvPython = "python"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🧪 Running India Health Insurance AI Agent Test Suite" -ForegroundColor Cyan
Write-Host "Python Executable: $VenvPython" -ForegroundColor Gray
Write-Host "Target Path:       $TestPath" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

$env:APP_ENV = "test"
$env:EMBEDDING_PROVIDER = "fallback"

$pytestArgs = @("-m", "pytest", $TestPath)
if ($Verbose) {
    $pytestArgs += "-v"
}

& $VenvPython @pytestArgs
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✅ ALL TESTS PASSED SUCCESSFULLY!" -ForegroundColor Green
} else {
    Write-Host "`n❌ TEST EXECUTION FAILED WITH CODE $exitCode" -ForegroundColor Red
}

exit $exitCode
