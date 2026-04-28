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
KL='\033[0;34m[kerala]\033[0m'    # blue
TN='\033[0;33m[tamilnadu]\033[0m' # yellow
FE='\033[0;32m[frontend]\033[0m'  # green
DV='\033[1;37m[dev]\033[0m'       # bold white
ER='\033[0;31m[dev]\033[0m'       # red errors

# --- Auto-activate the project virtualenv if present and not active ----
# Without this, uvicorn / python deps live in $ROOT/.venv/bin and won't be
# found on PATH, which silently kills the Kerala backend (uvicorn: command
# not found) while TN still works because /usr/bin/python3 has stdlib.
if [[ -z "${VIRTUAL_ENV:-}" && -f "$ROOT/.venv/bin/activate" ]]; then
  echo -e "$DV Activating $ROOT/.venv"
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

# --- Pre-flight: required commands must be on PATH ---------------------
preflight_fail=0
need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo -e "$ER Missing command: $1 — $2"
    preflight_fail=1
  fi
}
need uvicorn "Run \`pip install -r backend/kerala/requirements.txt\` inside .venv."
need python   "Python 3.11+ is required."
need npm      "Install Node 18+ from https://nodejs.org/"

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo -e "$ER Frontend deps missing — run \`cd frontend && npm install\` first."
  preflight_fail=1
fi
if (( preflight_fail )); then
  exit 1
fi

# --- Pre-flight: ports must be free ------------------------------------
port_in_use() {
  ss -tln 2>/dev/null | awk '{print $4}' | grep -Eq ":$1\$"
}
for p in 8001 8002 5173; do
  if port_in_use "$p"; then
    echo -e "$ER Port $p is already in use. Free it with:"
    echo -e "$ER   pkill -f 'uvicorn main:app' ; pkill -f 'python server.py' ; pkill -f 'vite'"
    exit 1
  fi
done

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
