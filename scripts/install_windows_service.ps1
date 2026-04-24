<#
Helper to register the built executable as a Windows service using NSSM.
Usage (PowerShell as Admin):
  .\scripts\install_windows_service.ps1 -ExePath 'C:\path\to\run.exe' -NssmPath 'C:\tools\nssm.exe'

If NSSM is not available, the script prints instructions to download it.
#>
param(
  [Parameter(Mandatory=$true)] [string]$ExePath,
  [string]$NssmPath = "nssm"
)

if (-Not (Test-Path $ExePath)) {
  Write-Error "Executable not found: $ExePath"
  exit 1
}

# Try to locate nssm
$nssm = $null
if (Get-Command $NssmPath -ErrorAction SilentlyContinue) {
  $nssm = (Get-Command $NssmPath).Source
} elseif (Test-Path "$PSScriptRoot\\..\\tools\\nssm.exe") {
  $nssm = (Resolve-Path "$PSScriptRoot\\..\\tools\\nssm.exe").Path
}

if (-Not $nssm) {
  Write-Host "NSSM not found. Download from https://nssm.cc/download and place nssm.exe on PATH or in the repo tools/ folder."
  exit 1
}

$serviceName = "MaisTrigo"
Write-Host "Installing service $serviceName using NSSM ($nssm) -> $ExePath"
& $nssm install $serviceName $ExePath
& $nssm set $serviceName AppRestartDelay 5000
& $nssm start $serviceName

Write-Host "Service $serviceName installed and started (check Windows Services or Event Viewer)."
