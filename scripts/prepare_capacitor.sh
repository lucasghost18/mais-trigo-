#!/usr/bin/env bash
set -euo pipefail

echo "Preparing Capacitor wrapper for MaisTrigo"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install Node.js and npm first." >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx not found but should be available with npm. Aborting." >&2
  exit 1
fi

echo "Installing Capacitor CLI locally..."
npm install --save-dev @capacitor/cli @capacitor/android @capacitor/core || true

echo "Initialize Capacitor project (skipping if already initialized)"
if [ ! -f capacitor.config.json ]; then
  npx cap init MaisTrigo com.maistrigo.app --web-dir=www || true
fi

echo "Note: This project uses Flask templates. For development you can run the Flask server and point Capacitor to it by setting the server url in Android studio (or using 'npx cap open android' and configuring)."

cat <<'EOF'
Recommended quick dev flow:

# 1) Run Flask dev server (on laptop):
#    python run.py  (or gunicorn -b 127.0.0.1:8000 wsgi:app)

# 2) In Android emulator use host loopback 10.0.2.2 to reach 127.0.0.1 on host.
#    In Android Studio's Capacitor config you can set server.url to http://10.0.2.2:8000 for dev builds.

# 3) Add Android platform and open project:
#    npx cap add android
#    npx cap open android

# For production: build a static webDir (copy templates/static files into 'www') and run:
#    npx cap copy
#    npx cap open android
EOF

echo "Prepared. Review capacitor.config.json and run 'npx cap add android' when ready."
