#!/usr/bin/env bash
# Tutor Portal — launcher.
# Starts the single FastAPI process (it serves the API *and* the SPA),
# then opens the app in the browser. Idempotent: safe to run any time.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8950}"
PY="${PY:-/usr/bin/python3}"

# Local Ollama with the newer model set (falls back to 11434 if 11437 is down).
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11437}"
export TUTOR_MODEL="${TUTOR_MODEL:-hermes3:latest}"

cd "$DIR"

if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "Tutor Portal already running at http://127.0.0.1:${PORT}/"
else
  echo "Starting Tutor Portal on port ${PORT} (tutor model: ${TUTOR_MODEL})…"
  nohup "$PY" -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" \
      > "$DIR/data/server.log" 2>&1 &
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then break; fi
    sleep 0.4
  done
fi

if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "Ready:  http://127.0.0.1:${PORT}/"
  LAN="$(hostname -I 2>/dev/null | awk '{print $1}')"
  [ -n "${LAN:-}" ] && echo "LAN:    http://${LAN}:${PORT}/"
  (command -v xdg-open >/dev/null && xdg-open "http://127.0.0.1:${PORT}/" >/dev/null 2>&1 &) || true
else
  echo "Failed to start — see $DIR/data/server.log" >&2; exit 1
fi
