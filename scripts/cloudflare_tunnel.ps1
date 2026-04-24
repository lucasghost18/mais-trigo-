# Cloudflare Tunnel - Exponha seu Flask na internet (Windows)
# Requer: PowerShell como Administrador
# Execute este script a partir da pasta do projeto

$ErrorActionPreference = "Stop"

$PORT = 5000

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel - Mais Trigo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se o Flask está rodando na porta 5000
Write-Host "Verificando se o Flask está rodando na porta ${PORT}..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", $PORT)
    $tcpClient.Close()
    $flaskRunning = $true
} catch {
    $flaskRunning = $false
}

if (-not $flaskRunning) {
    Write-Host "ERRO: Flask não está rodando na porta ${PORT}!" -ForegroundColor Red
    Write-Host "Execute primeiro: python run.py" -ForegroundColor Red
    exit 1
}

Write-Host "Flask detectado na porta ${PORT} ✓" -ForegroundColor Green
Write-Host ""

# Verifica se cloudflared existe
$cloudflaredPath = "$env:LOCALAPPDATA\cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "cloudflared não encontrado. Baixando..." -ForegroundColor Yellow
    $tempPath = "$env:TEMP\cloudflared.exe"
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $tempPath -UseBasicParsing

    New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\cloudflared" | Out-Null
    Move-Item -Path $tempPath -Destination $cloudflaredPath -Force
    Write-Host "cloudflared instalado em: $cloudflaredPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "Iniciando túnel Cloudflare para http://localhost:${PORT} ..." -ForegroundColor Cyan
Write-Host "Aguarde, a URL pública será exibida abaixo:" -ForegroundColor Yellow
Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Green

& $cloudflaredPath tunnel --url http://localhost:${PORT}

