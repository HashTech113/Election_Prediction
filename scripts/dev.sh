#!/usr/bin/env bash
# Run all three services locally:
#   - Kerala backend     → http://localhost:8001
#   - Tamil Nadu backend → http://localhost:8002
#   - Frontend (Vite)    → http://localhost:5173
#
# Stops all three on Ctrl-C.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Coloured prefix per service so interleaved logs are scannable.
KL='\033[0;34m[kerala]\033[0m'   # blue
TN='\033[0;33m[tamilnadu]\033[0m' # yellow
FE='\033[0;32m[frontend]\033[0m'  # green
DV='\033[1;37m[dev]\033[0m'       # bold white

cleanup() {
  echo
  echo -e "$DV Stopping all services…"
  kill 0 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo -e "$DV Project root: $ROOT"
echo -e "$DV Booting all three services…"
echo

echo -e "$KL Starting Kerala backend (FastAPI / uvicorn) on http://localhost:8001"
(
  cd "$ROOT/backend/kerala"
  PORT=8001 HOST=0.0.0.0 \
    uvicorn main:app --reload --host 0.0.0.0 --port 8001 2>&1 \
    | sed -u "s/^/$(echo -e "$KL") /"
) &

echo -e "$TN Starting Tamil Nadu backend (stdlib HTTP) on http://localhost:8002"
(
  cd "$ROOT/backend/tamilnadu"
  PORT=8002 HOST=0.0.0.0 python server.py 2>&1 \
    | sed -u "s/^/$(echo -e "$TN") /"
) &

echo -e "$FE Starting Vite dev server on http://localhost:5173"
(
  cd "$ROOT/frontend"
  npm run dev 2>&1 \
    | sed -u "s/^/$(echo -e "$FE") /"
) &

echo
echo -e "$DV All services launched. Press Ctrl+C to stop."
echo -e "$DV  Frontend          → http://localhost:5173"
echo -e "$DV  Kerala API        → http://localhost:8001/api/health"
echo -e "$DV  Tamil Nadu API    → http://localhost:8002/api/health"
echo

wait
