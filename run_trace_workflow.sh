#!/bin/bash
#
# Complete workflow: Start server, run inference, parse trace, open dashboard
#
# Usage: ./run_trace_workflow.sh <path-to-model.gguf>
#

set -e

MODEL_PATH="${1}"
PROJECT_DIR="$(pwd)"

if [ -z "$MODEL_PATH" ]; then
    echo "Error: MODEL_PATH not specified"
    echo "Usage: ./run_trace_workflow.sh <path-to-model.gguf>"
    exit 1
fi

echo "=== Grammar Trace Workflow ==="
echo

# Step 1: Start server with tracing in background
echo "[1/5] Starting llama-server with grammar tracing..."
./run_server_with_trace.sh "$MODEL_PATH" &
SERVER_PID=$!

# Give server time to start
echo "Waiting for server to start..."
sleep 8

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Server failed to start"
    exit 1
fi

echo "Server started (PID: $SERVER_PID)"
echo

# Step 2: Run Ballerina invoker
echo "[2/5] Running Ballerina invoker to generate trace data..."
cd invoker
if ! bal run main.bal; then
    echo "Error: Invoker failed"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi
cd "$PROJECT_DIR"
echo

# Step 3: Find latest trace file
echo "[3/5] Locating latest trace file..."
TRACE_FILE=$(ls -t traces/trace_*.json 2>/dev/null | head -1)

if [ -z "$TRACE_FILE" ]; then
    echo "Error: No trace file found"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "Found trace: $TRACE_FILE"
echo

# Step 4: Parse and export trace
echo "[4/5] Parsing trace data..."
if ! python3 tracer/parser.py "$TRACE_FILE" \
    --output "dashboard/data/latest.json" \
    --summary \
    --validate; then
    echo "Error: Trace parsing failed"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi
echo

# Step 5: Open dashboard
echo "[5/5] Opening dashboard..."
DASHBOARD_PATH="$PROJECT_DIR/dashboard/index.html"

if command -v open &> /dev/null; then
    # macOS
    open "$DASHBOARD_PATH"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$DASHBOARD_PATH"
elif command -v start &> /dev/null; then
    # Windows (Git Bash)
    start "$DASHBOARD_PATH"
else
    echo "Could not automatically open dashboard"
    echo "Please open: $DASHBOARD_PATH"
fi

echo
echo "=== Workflow Complete ==="
echo "Dashboard: $DASHBOARD_PATH"
echo "Trace data: dashboard/data/latest.json"
echo "Server is still running (PID: $SERVER_PID)"
echo
echo "To stop the server:"
echo "  kill $SERVER_PID"
echo
