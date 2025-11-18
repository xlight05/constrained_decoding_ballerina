#!/bin/bash
#
# Launch llama-server with grammar tracing enabled
#
# Usage: ./run_server_with_trace.sh [MODEL_PATH]
#

set -e

# Configuration
MODEL_PATH="${1:-${MODEL_PATH}}"
GRAMMAR_PATH="$(pwd)/spec_builder/grammars/spec.gbnf"
TRACE_OUTPUT="$(pwd)/traces/trace_$(date +%Y%m%d_%H%M%S).json"
PORT=8080
LLAMACPP_DIR="${LLAMACPP_DIR:-/Users/wso2/llamacpp/llama.cpp}"

# Validate inputs
if [ -z "$MODEL_PATH" ]; then
    echo "Error: MODEL_PATH not specified"
    echo "Usage: ./run_server_with_trace.sh <path-to-model.gguf>"
    echo "   or: MODEL_PATH=/path/to/model.gguf ./run_server_with_trace.sh"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found: $MODEL_PATH"
    exit 1
fi

if [ ! -f "$GRAMMAR_PATH" ]; then
    echo "Error: Grammar file not found: $GRAMMAR_PATH"
    exit 1
fi

if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "Error: llama.cpp directory not found: $LLAMACPP_DIR"
    echo "Set LLAMACPP_DIR environment variable to your llama.cpp clone location"
    exit 1
fi

# Ensure trace directory exists
mkdir -p "$(pwd)/traces"

# Check if llama-server is built
LLAMA_SERVER="$LLAMACPP_DIR/llama-server"
if [ ! -f "$LLAMA_SERVER" ]; then
    echo "Error: llama-server not found at $LLAMA_SERVER"
    echo "Build it first: cd $LLAMACPP_DIR && make llama-server"
    exit 1
fi

echo "=== Grammar Trace Server ==="
echo "Model: $MODEL_PATH"
echo "Grammar: $GRAMMAR_PATH"
echo "Trace output: $TRACE_OUTPUT"
echo "Port: $PORT"
echo "=========================="
echo

# Launch llama-server with tracing
exec "$LLAMA_SERVER" \
  --model "$MODEL_PATH" \
  --grammar-file "$GRAMMAR_PATH" \
  --grammar-trace "$TRACE_OUTPUT" \
  --port $PORT \
  --verbose \
  -ngl 999 \
  --ctx-size 4096 \
  2>&1 | tee "$(pwd)/traces/server_$(date +%Y%m%d_%H%M%S).log"
