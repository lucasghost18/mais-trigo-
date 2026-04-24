#!/usr/bin/env bash
# Cloudflare Tunnel - Exponha seu Flask na internet (Linux/Mac)
# Execute este script a partir da pasta do projeto

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT=5000

echo "========================================"
echo "  Cloudflare Tunnel - Mais Trigo"
echo "========================================"
echo ""

# Verifica se o Flask está rodando na porta 5000
echo "Verificando se o Flask está rodando na porta ${PORT}..."
if ! curl -s http://localhost:${PORT} > /dev/null 2>&1; then
    echo "ERRO: Flask não está rodando na porta ${PORT}!"
    echo "Execute primeiro: cd ${APP_DIR} && python run.py"
    exit 1
fi

echo "Flask detectado na porta ${PORT} ✓"
echo ""

# Verifica se cloudflared existe
if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared não encontrado. Instalando..."

    # Detecta o SO
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i /tmp/cloudflared.deb || sudo apt-get install -f -y
        rm -f /tmp/cloudflared.deb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        if command -v brew &> /dev/null; then
            brew install cloudflared
        else
            curl -L --output /tmp/cloudflared.tgz https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz
            tar -xzf /tmp/cloudflared.tgz -C /tmp
            sudo mv /tmp/cloudflared /usr/local/bin/
            rm -f /tmp/cloudflared.tgz
        fi
    else
        echo "Sistema operacional não suportado para instalação automática."
        echo "Baixe manualmente em: https://github.com/cloudflare/cloudflared/releases"
        exit 1
    fi

    echo "cloudflared instalado com sucesso ✓"
fi

echo ""
echo "Iniciando túnel Cloudflare para http://localhost:${PORT} ..."
echo "Aguarde, a URL pública será exibida abaixo:"
echo ""
echo "----------------------------------------"

cloudflared tunnel --url http://localhost:${PORT}

