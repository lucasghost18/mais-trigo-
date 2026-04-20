param(
  [string]$AppDir = (Get-Location).Path,
  [string]$Version = "1.0.0"
)

Write-Host "Building Windows executable and NSIS installer in: $AppDir"

$venv = Join-Path $AppDir '.venv'
if (-Not (Test-Path $venv)) {
  Write-Host "Creating virtualenv..."
  python -m venv $venv
}

& "$venv\Scripts\pip.exe" install --upgrade pip
& "$venv\Scripts\pip.exe" install -r "$AppDir\requirements.txt"
& "$venv\Scripts\pip.exe" install pyinstaller

# Build single-file exe (uses run.py)
Push-Location $AppDir
& "$venv\Scripts\pyinstaller.exe" --noconfirm --onefile --add-data "app\templates;app\templates" --add-data "app\static;app\static" run.py
Pop-Location

# Check for makensis (NSIS)
if (-Not (Get-Command makensis -ErrorAction SilentlyContinue)) {
  Write-Error "makensis not found. Install NSIS and ensure makensis is on PATH before building installer."
  exit 1
}

$nsisScript = Join-Path $AppDir 'scripts\windows_installer.nsi'
Write-Host "Running makensis on $nsisScript"
& makensis /DVERSION=$Version $nsisScript

Write-Host "Installer build complete. Check dist\ and the generated installer in the current folder."
