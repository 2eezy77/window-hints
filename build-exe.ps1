#Requires -Version 5.1
# Builds dist\MultiwindowUIHints.exe (one file, no console window, requests Administrator via UAC).
# Run once: powershell -ExecutionPolicy Bypass -File .\build-exe.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

Write-Host "Installing PyInstaller..."
& python -m pip install "pyinstaller>=6" -q

$Entry = Join-Path $Root "multiwindow_ui_hints.py"
if (-not (Test-Path -LiteralPath $Entry)) {
    Write-Error "Missing $Entry"
}

Write-Host "Building exe (this may take a minute)..."
& python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --uac-admin `
    --name "MultiwindowUIHints" `
    --paths $Root `
    --collect-all "multiwindow_ui_hints" `
    --collect-all "keyboard" `
    --collect-all "pystray" `
    --collect-all "pywinauto" `
    --collect-all "uiautomation" `
    $Entry

$exe = Join-Path $Root "dist\MultiwindowUIHints.exe"
if (Test-Path -LiteralPath $exe) {
    Write-Host ""
    Write-Host "Built: $exe" -ForegroundColor Green
    Write-Host "Copy that to your Desktop or Pin to Start if you like."
} else {
    Write-Host "Build finished but exe not found at expected path." -ForegroundColor Yellow
}
