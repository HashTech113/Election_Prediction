#!/usr/bin/env bash
# Regenerate the static JSON snapshots the frontend serves in production.
#
# The frontend can run as a pure static site (no backend) by reading pre-baked
# JSON from frontend/public/data/{kerala,tamilnadu}/. This script captures the
# live backend responses into those files. Run it whenever the underlying CSVs
# / models change, then rebuild and redeploy the frontend.
#
# Usage:
#   1. Start the backends (e.g. `npm run dev:kerala` and `npm run dev:tamilnadu`,
#      or `npm run dev`), so they answer on :8001 and :8002.
#   2. ./scripts/snapshot-data.sh
#
# Override hosts with KERALA_URL / TN_URL env vars if needed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K="${KERALA_URL:-http://127.0.0.1:8001}"
T="${TN_URL:-http://127.0.0.1:8002}"
KD="$ROOT/frontend/public/data/kerala"
TD="$ROOT/frontend/public/data/tamilnadu"

mkdir -p "$KD" "$TD"
fail=0

snap() { # url  outfile
  local code
  code=$(curl -s -m 30 -o "$2" -w "%{http_code}" "$1" || echo "000")
  if [ "$code" = "200" ] && python3 -c "import json;json.load(open('$2'))" 2>/dev/null; then
    printf '  OK   %-55s (%s bytes)\n' "${2#$ROOT/}" "$(wc -c < "$2")"
  else
    printf '  FAIL %-55s (HTTP %s) <- %s\n' "${2#$ROOT/}" "$code" "$1"
    fail=1
  fi
}

echo "Kerala  ($K)"
snap "$K/api/health"                                        "$KD/health.json"
snap "$K/api/predictions/meta"                              "$KD/predictions-meta.json"
snap "$K/api/predictions"                                   "$KD/predictions.json"
snap "$K/api/predictions/lenses"                            "$KD/lenses.json"
snap "$K/api/predictions/lens?name=historical_projection"   "$KD/lens-historical_projection.json"
snap "$K/api/predictions/lens?name=long_term_trend"         "$KD/lens-long_term_trend.json"
snap "$K/api/predictions/lens?name=recent_swing"            "$KD/lens-recent_swing.json"
snap "$K/api/predictions/lens?name=final_prediction"        "$KD/lens-final_prediction.json"

echo "Tamil Nadu  ($T)"
snap "$T/api/health"                                            "$TD/health.json"
snap "$T/api/predictions/meta"                                  "$TD/predictions-meta.json"
snap "$T/api/predictions"                                       "$TD/predictions.json"
snap "$T/api/predictions?analysis_type=long_term_trend"         "$TD/analysis-long_term_trend.json"
snap "$T/api/predictions?analysis_type=recent_swing"            "$TD/analysis-recent_swing.json"
snap "$T/api/predictions?analysis_type=live_intelligence_score" "$TD/analysis-live_intelligence_score.json"

if [ "$fail" -ne 0 ]; then
  echo "One or more snapshots failed — are both backends running on :8001 and :8002?" >&2
  exit 1
fi
echo "Done. Snapshots written under frontend/public/data/."
