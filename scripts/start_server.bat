@echo off
chcp 65001 >nul
title Mais Trigo - Servidor + Tunnel

echo ==========================================
echo    MAIS TRIGO - Iniciando Servidor
echo ==========================================
echo.

REM Navegar para pasta do projeto
cd /d "%~dp0\.."

REM Verificar se cloudflared existe
if not exist "cloudflared.exe" (
    echo [ERRO] cloudflared.exe nao encontrado!
    echo Baixe em: https://github.com/cloudflare/cloudflared/releases
    pause
    exit /b 1
)

REM Ativar ambiente virtual e iniciar Flask em background
echo [1/3] Iniciando servidor Flask...
start "Flask Server" cmd /c ".venv\Scripts\python.exe run.py"

REM Aguardar servidor subir
timeout /t 3 /nobreak >nul

REM Iniciar Cloudflare Tunnel
echo [2/3] Iniciando Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /c "cloudflared.exe tunnel --url http://localhost:5000"

REM Aguardar tunnel criar URL
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Servidor rodando!
echo.
echo Acesse pelo navegador:
echo    http://localhost:5000  (local)
echo    ou pelo link do Cloudflare (veja janela do tunnel)
echo.
echo Credenciais de teste:
echo    Admin:    mais vendas / 3341
echo.
pause

