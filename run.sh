#!/usr/bin/env bash
# One-command startup: seeds the DB (if empty) and launches backend + frontend.
set -e
cd "$(dirname "$0")"

if [ ! -f backend/venv/bin/activate ] && [ ! -d backend/.venv ]; then
  python3 -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate 2>/dev/null || source backend/.venv/Scripts/activate
pip install -q -r backend/requirements.txt

export MAGNET_DB="$(pwd)/backend/magnet.db"
export MAGNET_AUTO_SEED=1

(cd web && [ -d node_modules ] || npm install)

echo "Starting backend on :8000 and frontend on :5173..."
(cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!
(cd web && npm run dev -- --host) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
