$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$DistPath = Join-Path $ProjectRoot "dist"
$ReleasePath = Join-Path $DistPath "TeaVisionEdge"
$ZipPath = Join-Path $DistPath "TeaVisionEdge-Windows.zip"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtual environment not found: $Python"
}

& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Run: .\.venv\Scripts\python.exe -m pip install pyinstaller"
}

Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name TeaVisionEdge `
        --add-data "ui\dark_theme.qss;ui" `
        --add-data "models\yolov8n.pt;models" `
        --add-data "models\person_mask.pt;models" `
        --add-data "models\gun_detection.pt;models" `
        --collect-all cv2 `
        --collect-all ultralytics `
        main.py

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $ReleaseConfig = Join-Path $ReleasePath "config"
    New-Item -ItemType Directory -Force -Path $ReleaseConfig | Out-Null
    Copy-Item `
        -Path (Join-Path $ProjectRoot "config\*.json") `
        -Destination $ReleaseConfig `
        -Force

    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive `
        -Path (Join-Path $ReleasePath "*") `
        -DestinationPath $ZipPath `
        -CompressionLevel Optimal

    Write-Host ""
    Write-Host "Release created:"
    Write-Host "  EXE: $ReleasePath\TeaVisionEdge.exe"
    Write-Host "  ZIP: $ZipPath"
}
finally {
    Pop-Location
}
