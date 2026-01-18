#!/bin/bash

# Identity Auth UI - Quick Start Script

echo "Starting Identity Authentication System..."
echo ""

# Start MongoDB if not running
echo "Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    echo "Starting MongoDB..."
    mongod --dbpath ./data/db --fork --logpath ./data/mongodb.log
fi

# Start Identity Server (Flask API on port 5001)
echo "Starting Identity API Server on port 5001..."
python3 identity_server.py &
API_PID=$!

# Wait for API to be ready
sleep 3

# Start React Frontend (on port 3000)
echo "Starting React Frontend on port 3000..."
cd src/frontend

# Update index.js to use AuthApp
cp src/index.js src/index-original.js 2>/dev/null
cp src/index-auth.js src/index.js

# Kill any existing React dev server
lsof -ti:3000 | xargs kill -9 2>/dev/null

npm start &
FRONTEND_PID=$!

echo ""
echo "====================================="
echo "Identity Auth System Running"
echo "====================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "API:      http://localhost:5001"
echo ""
echo "API Endpoints:"
echo "  POST /api/auth/signup"
echo "  POST /api/auth/login"
echo "  GET  /api/auth/me"
echo "  GET  /api/auth/profile"
echo "  PUT  /api/auth/profile"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $API_PID $FRONTEND_PID 2>/dev/null; cd ../..; exit" INT
wait
