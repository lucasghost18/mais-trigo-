<#
Build helper for Windows using PyInstaller.

Usage (PowerShell):
  .\scripts\build_windows.ps1 -AppDir 'C:\path\to\project'

Requires: Python installed and available on PATH. This script will create a venv at `.venv` and install requirements.
#>

param(
  [string]$AppDir = (Get-Location).Path,
  [string]$OutDir = "dist"
)

Write-Host "Building project at: $AppDir"

$venv = Join-Path $AppDir '.venv'
if (-Not (Test-Path $venv)) {
  Write-Host "Creating virtualenv..."
  python -m venv $venv
}

& "$venv\Scripts\pip.exe" install --upgrade pip
& "$venv\Scripts\pip.exe" install -r "$AppDir\requirements.txt"
& "$venv\Scripts\pip.exe" install pyinstaller

# Run pyinstaller to create a single-file exe. We include templates and static folders as data.
Push-Location $AppDir
& "$venv\Scripts\pyinstaller.exe" --noconfirm --onefile --add-data "app\templates;app\templates" --add-data "app\static;app\static" run.py
Pop-Location

Write-Host "Build complete. Binary is in $AppDir\dist"
