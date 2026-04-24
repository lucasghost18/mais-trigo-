#!/usr/bin/env bash
# Create a desktop launcher that opens the local app in the browser.
# Usage: ./scripts/create_desktop_shortcut.sh http://127.0.0.1:8000

URL=${1:-http://127.0.0.1:8000}
DESKTOP_FILE="$HOME/.local/share/applications/mais-trigo.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Mais Trigo
Comment=Sistema de Pedidos - Mais Trigo
Exec=xdg-open $URL
Terminal=false
Type=Application
Categories=Utility;
EOF

chmod 644 "$DESKTOP_FILE"
echo "Desktop launcher created: $DESKTOP_FILE"
