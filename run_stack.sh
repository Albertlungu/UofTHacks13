#!/bin/bash

set -e

echo "=========================================="
echo "  Full Stack Launcher"
echo "=========================================="
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Ensure Gemini dependencies are present
python - <<'PY'
import importlib.util
missing = []
for pkg in ("google.generativeai", "google.api_core"):
    if importlib.util.find_spec(pkg) is None:
        missing.append(pkg)
if missing:
    print("Missing packages:", ", ".join(missing))
    raise SystemExit(1)
PY
if [ $? -ne 0 ]; then
  echo "Installing missing Google AI packages..."
  pip install -q google-generativeai google-api-core
fi

echo "Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
  echo "Starting MongoDB..."
  mkdir -p ./data/db
  mongod --dbpath ./data/db --fork --logpath ./data/mongodb.log
fi

echo "Starting identity API (MongoDB-backed)..."
python3 identity_server.py &
AUTH_PID=$!

echo "Starting core API..."
python3 main.py &
CORE_PID=$!

HAND_PID=""
if lsof -iTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Hand tracker already running on port 8765. Skipping launch."
else
  echo "Starting hand tracker..."
  python3 run_hand_tracker.py &
  HAND_PID=$!
fi

echo "Starting frontend..."
cd src/frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo ""
echo "=========================================="
echo "Services running"
echo "Frontend: http://localhost:3000"
echo "Core API:  http://localhost:5000"
echo "Auth API:  http://localhost:5001"
echo "Hand WS:   ws://localhost:8765"
echo "Press Ctrl+C to stop"
echo "=========================================="

echo ""

cleanup() {
  echo ""
  echo "Stopping services..."
  kill $FRONTEND_PID $CORE_PID $AUTH_PID 2>/dev/null || true
  if [ -n "$HAND_PID" ]; then
    kill $HAND_PID 2>/dev/null || true
  fi
  echo "Done."
  exit 0
}

trap cleanup SIGINT SIGTERM
wait $FRONTEND_PID $CORE_PID $AUTH_PID
