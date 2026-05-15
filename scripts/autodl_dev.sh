#!/usr/bin/env bash
# AutoDL: expose dev UI on 0.0.0.0:6006 (map this port in AutoDL custom service panel)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COPYGEN_AUTH_USER="${COPYGEN_AUTH_USER:-admin}"
export COPYGEN_AUTH_PASSWORD="${COPYGEN_AUTH_PASSWORD:-admin123456}"
export COPYGEN_AUTH_SECRET="${COPYGEN_AUTH_SECRET:-copygen-autodl-session-v1}"

echo "==> Backend http://0.0.0.0:8765"
uv run python -m uvicorn web.server:app --host 0.0.0.0 --port 8765 &
BACK_PID=$!

cleanup() { kill "$BACK_PID" 2>/dev/null || true; }
trap cleanup EXIT

sleep 2
echo "==> Frontend http://0.0.0.0:6006 (open AutoDL port mapping for 6006)"
cd web/frontend
npm run dev:public
