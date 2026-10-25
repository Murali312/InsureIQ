# PowerShell Script to Package Project into Clean ZIP Distribution
param(
    [string]$OutputFile = "india-health-insurance-ai-agent.zip"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

$ZipPath = Join-Path $ProjectRoot $OutputFile
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Packaging India Health Insurance AI Agent" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Output ZIP:   $ZipPath" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

# Directories and files to exclude from package
$ExcludePatterns = @(
    "*\.venv\*",
    "*\venv\*",
    "*\env\*",
    "*\.git\*",
    "*\vector_store\*",
    "*\tmp_test_chroma\*",
    "*\data\*",
    "*\__pycache__\*",
    "*\.pytest_cache\*",
    "*\*.pyc",
    "*\*.log",
    "*\.env",
    "*\.env.local",
    "*\tmp\*",
    "*\temp\*",
    "*india-health-insurance-ai-agent.zip",
    "*\staging_pkg_temp\*"
)

# Collect files to include
$FilesToZip = Get-ChildItem -Path $ProjectRoot -Recurse -File | Where-Object {
    $filePath = $_.FullName
    $exclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($filePath -like $pattern) {
            $exclude = $true
            break
        }
    }
    -not $exclude
}

Write-Host "Collected $($FilesToZip.Count) production files to package." -ForegroundColor Gray

# Create temporary staging directory
$StageDir = Join-Path $ProjectRoot "staging_pkg_temp"
if (Test-Path $StageDir) {
    Remove-Item $StageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir | Out-Null

try {
    foreach ($file in $FilesToZip) {
        $relativePath = $file.FullName.Substring($ProjectRoot.Length).TrimStart("\", "/")
        $targetFile = Join-Path $StageDir $relativePath
        $targetDir = Split-Path -Parent $targetFile
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $file.FullName -Destination $targetFile -Force
    }

    # Compress staging folder into ZIP
    Compress-Archive -Path "$StageDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

    Write-Host "SUCCESS: ZIP created at: $ZipPath" -ForegroundColor Green

    # Verify and inspect ZIP contents
    $zipSize = (Get-Item $ZipPath).Length / 1KB
    Write-Host "Package Size: $([Math]::Round($zipSize, 2)) KB" -ForegroundColor Cyan
    Write-Host "Archive Manifest:" -ForegroundColor Yellow

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    $entryCount = 0
    foreach ($entry in $archive.Entries) {
        if (-not $entry.FullName.EndsWith("/")) {
            Write-Host "  - $($entry.FullName)" -ForegroundColor DarkGray
            $entryCount++
        }
    }
    $archive.Dispose()
    Write-Host "Total Archived Production Files: $entryCount" -ForegroundColor Green

} finally {
    if (Test-Path $StageDir) {
        Remove-Item $StageDir -Recurse -Force
    }
}
