#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Install Python dependencies"
pip install -r requirements.txt

echo "==> Build Vue frontend"
cd web/frontend
if command -v npm >/dev/null 2>&1; then
  npm ci
  npm run build
else
  echo "ERROR: npm not found. Enable Node on Render or add NODE_VERSION."
  exit 1
fi

echo "==> Build done"
