@echo off
chcp 65001 >nul
title Mais Trigo - Iniciar Servidor + Tunnel

REM Verificar se PowerShell está disponível
powershell -Command "Get-Variable" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] PowerShell nao encontrado!
    pause
    exit /b 1
)

REM Executar o script PowerShell que gerencia tudo
echo Iniciando Mais Trigo com Cloudflare Tunnel...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0start_tunnel.ps1"

