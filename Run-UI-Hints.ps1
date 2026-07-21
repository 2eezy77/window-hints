#Requires -Version 5.1
# Double-click friendly: re-launches elevated (UAC), same as Admin PowerShell from this folder.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $MyInvocation.MyCommand.Path
    )
    exit 0
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python was not found on PATH. Install Python 3 and try again." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

& python -m pip install -r (Join-Path $Root "requirements.txt") -q
& python -m multiwindow_ui_hints
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "Exited with code $code" -ForegroundColor Yellow
    Read-Host "Press Enter to close"
}
exit $code
