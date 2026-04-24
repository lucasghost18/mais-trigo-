#!/usr/bin/env bash
set -euo pipefail

# Usage: sudo ./scripts/install_linux.sh /path/to/project username
# Defaults: project dir = /home/$USER/Documentos/code, username = current user

APP_DIR=${1:-/home/$(logname)/Documentos/code}
RUN_USER=${2:-$(logname)}
VENV_DIR="$APP_DIR/.venv"

echo "Installing app from: $APP_DIR"
echo "Run as user: $RUN_USER"

if [ ! -d "$APP_DIR" ]; then
  echo "Project directory not found: $APP_DIR"
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"
pip install gunicorn

SERVICE_FILE=/etc/systemd/system/mais-trigo.service

cat <<EOF | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Mais Trigo Flask App
After=network.target

[Service]
User=$RUN_USER
Group=$RUN_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn -w 3 -b 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now mais-trigo.service

echo "Service installed and started. Check logs with: sudo journalctl -u mais-trigo.service -f"
