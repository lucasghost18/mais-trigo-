# Requires -Version 5.1
# Mais Trigo - Iniciar Servidor + Cloudflare Tunnel com um clique

$ErrorActionPreference = "Stop"

$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$PORT = 5000
$CLOUDFLARE_PATH = "$env:LOCALAPPDATA\cloudflared\cloudflared.exe"

function Write-Color($Text, $Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}

Clear-Host
Write-Color "========================================" "Cyan"
Write-Color "   MAIS TRIGO - Iniciar Servidor" "Cyan"
Write-Color "========================================" "Cyan"
Write-Host ""

# 1. Verificar/instalar cloudflared
if (-not (Test-Path $CLOUDFLARE_PATH)) {
    Write-Color "[1/4] cloudflared não encontrado. Baixando..." "Yellow"
    New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\cloudflared" | Out-Null
    $tempFile = "$env:TEMP\cloudflared.exe"
    try {
        Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $tempFile -UseBasicParsing
        Move-Item -Path $tempFile -Destination $CLOUDFLARE_PATH -Force
        Write-Color "[1/4] cloudflared instalado com sucesso!" "Green"
    } catch {
        Write-Color "[ERRO] Falha ao baixar cloudflared. Verifique sua conexão." "Red"
        pause
        exit 1
    }
} else {
    Write-Color "[1/4] cloudflared encontrado." "Green"
}

# 2. Iniciar Flask em background (janela oculta)
Write-Color "[2/4] Iniciando servidor Flask na porta $PORT..." "Yellow"
$pythonPath = Join-Path $PROJECT_DIR ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = "python"
}

$flaskProcess = Start-Process -FilePath $pythonPath -ArgumentList "run.py" -WorkingDirectory $PROJECT_DIR -WindowStyle Hidden -PassThru
Write-Color "[2/4] Flask iniciado (PID: $($flaskProcess.Id))" "Green"

# Aguardar Flask subir
$maxWait = 15
$flaskReady = $false
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $PORT)
        $tcp.Close()
        $flaskReady = $true
        break
    } catch {
        Write-Host "." -NoNewline
    }
}
Write-Host ""

if (-not $flaskReady) {
    Write-Color "[ERRO] Flask não respondeu após $maxWait segundos." "Red"
    Stop-Process -Id $flaskProcess.Id -Force -ErrorAction SilentlyContinue
    pause
    exit 1
}
Write-Color "[2/4] Flask respondendo na porta $PORT!" "Green"

# 3. Iniciar Cloudflare Tunnel
Write-Color "[3/4] Iniciando Cloudflare Tunnel..." "Yellow"
$errFile = "$env:TEMP\mais_trigo_cf_err.txt"
$outFile = "$env:TEMP\mais_trigo_cf_out.txt"
Remove-Item $errFile -ErrorAction SilentlyContinue
Remove-Item $outFile -ErrorAction SilentlyContinue

$cfProcess = Start-Process -FilePath $CLOUDFLARE_PATH -ArgumentList "tunnel","--url","http://localhost:$PORT" -RedirectStandardOutput $outFile -RedirectStandardError $errFile -WindowStyle Hidden -PassThru
Write-Color "[3/4] Tunnel iniciado (PID: $($cfProcess.Id))" "Green"

# 4. Aguardar URL e exibir
Write-Color "[4/4] Aguardando URL pública..." "Yellow"
$tunnelUrl = $null
$maxWait = 20
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $errFile) {
        $content = Get-Content $errFile -ErrorAction SilentlyContinue
        $match = $content | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
        if ($match) {
            $tunnelUrl = $match.Matches[0].Value
            break
        }
    }
    Write-Host "." -NoNewline
}
Write-Host ""

if (-not $tunnelUrl) {
    Write-Color "[AVISO] Não foi possível capturar a URL automaticamente." "Yellow"
    Write-Color "        O tunnel está rodando. Verifique o arquivo: $errFile" "Yellow"
} else {
    Write-Host ""
    Write-Color "========================================" "Green"
    Write-Color "   SERVIDOR ONLINE!" "Green"
    Write-Color "========================================" "Green"
    Write-Host ""
    Write-Color "🔗 URL PÚBLICA:" "Cyan"
    Write-Color "   $tunnelUrl" "White"
    Write-Host ""
    Write-Color "📍 URL LOCAL:" "Cyan"
    Write-Color "   http://localhost:$PORT" "White"
    Write-Host ""
    Write-Color "👤 LOGIN ADMIN:" "Cyan"
    Write-Color "   Usuário: mais vendas" "White"
    Write-Color "   Senha:   3341" "White"
    Write-Host ""

    # Copiar URL para clipboard
    try {
        $tunnelUrl | Set-Clipboard
        Write-Color "📋 URL copiada para a área de transferência!" "Magenta"
    } catch {
        # Ignore clipboard errors
    }

    # Abrir navegador
    Write-Color "Abrindo navegador em 3 segundos..." "DarkGray"
    Start-Sleep -Seconds 3
    Start-Process $tunnelUrl
}

Write-Host ""
Write-Color "Pressione qualquer tecla para ENCERRAR o servidor e o tunnel..." "Red"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Limpeza
Write-Color "`nEncerrando processos..." "Yellow"
Stop-Process -Id $cfProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $flaskProcess.Id -Force -ErrorAction SilentlyContinue
Write-Color "Servidor encerrado. Até logo!" "Green"
Start-Sleep -Seconds 1

