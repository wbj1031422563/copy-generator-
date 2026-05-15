#!/usr/bin/env bash
# AutoDL production-style: one port serves API + built Vue (recommended for sharing)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-6006}"

export COPYGEN_AUTH_USER="${COPYGEN_AUTH_USER:-admin}"
export COPYGEN_AUTH_PASSWORD="${COPYGEN_AUTH_PASSWORD:-admin123456}"
export COPYGEN_AUTH_SECRET="${COPYGEN_AUTH_SECRET:-copygen-autodl-session-v1}"

if [[ ! -f web/static/dist/index.html ]]; then
  echo "==> Building frontend..."
  cd web/frontend && npm install && npm run build && cd "$ROOT"
fi

echo "==> Serving on http://0.0.0.0:${PORT}"
echo "    Map port ${PORT} in AutoDL custom service panel"
exec uv run python -m uvicorn web.server:app --host 0.0.0.0 --port "$PORT"
