# Grammar Path Tracing & Visualization

This directory contains a complete system for tracing and visualizing grammar-constrained decoding in llama.cpp.

## Overview

The system allows you to:
1. **Trace** how grammar constraints affect token selection during inference
2. **Parse** raw trace data into a structured format
3. **Visualize** token decisions with an interactive web dashboard

## Components

### 1. llama.cpp Modifications (Not in this repo)

Before using this system, you need to modify your llama.cpp installation. See the plan file for detailed instructions:

- `/Users/wso2/.claude/plans/replicated-swimming-sunset.md`

Key modifications:
- `src/llama-grammar.cpp` - Add trace logging infrastructure
- `src/llama-grammar.h` - Add trace API
- `common/common.h` - Add `--grammar-trace` parameter
- `common/arg.cpp` - Parse `--grammar-trace` flag

### 2. Python Trace Parser (`tracer/`)

Parses raw JSON trace files from llama.cpp into dashboard-friendly format.

**Files:**
- `models.py` - Data structures for traces
- `parser.py` - Main parsing logic
- `exporter.py` - Export to dashboard format

**Usage:**
```bash
python3 tracer/parser.py traces/trace_20231227_103000.json \
  --output dashboard/data/processed.json \
  --summary \
  --validate
```

### 3. Interactive Dashboard (`dashboard/`)

Web-based visualization with token-click interaction.

**Features:**
- Click any token → see its probability distribution
- Before/after grammar filtering comparison
- High-impact decision point highlighting
- Detailed step-by-step analysis

**Testing:**
```bash
cd dashboard
npm install
npm test              # Run tests
npm run test:ui       # Interactive test UI
npm run test:coverage # Coverage report
```

### 4. Integration Scripts

**`run_server_with_trace.sh`** - Launch llama-server with tracing

```bash
./run_server_with_trace.sh /path/to/model.gguf
```

**`run_trace_workflow.sh`** - Complete end-to-end workflow

```bash
./run_trace_workflow.sh /path/to/model.gguf
```

This will:
1. Start llama-server with tracing
2. Run Ballerina invoker
3. Parse trace data
4. Open dashboard

## Quick Start

### Step 1: Modify llama.cpp

Apply modifications to your llama.cpp installation (see plan file).

Build llama-server:
```bash
cd /Users/wso2/llamacpp/llama.cpp
make clean && make llama-server
```

### Step 2: Run Complete Workflow

```bash
# Set environment variables
export LLAMACPP_DIR=/Users/wso2/llamacpp/llama.cpp
export MODEL_PATH=/path/to/your/model.gguf

# Run workflow
./run_trace_workflow.sh $MODEL_PATH
```

This will automatically:
- Start the server
- Generate trace data with prompt "write a ballerina app which prints 0 to 10"
- Parse and visualize the trace

### Step 3: Explore Dashboard

The dashboard will open automatically. Features:

**Click a token** to see:
- Probability distribution before/after grammar filtering
- Which tokens were rejected and why
- Grammar impact metrics

**Visual indicators:**
- 🔴 Red dot = High-impact decision (>30% prob shift)
- 🟡 Gold background = Currently selected token
- Green bars = Selected token in chart
- Blue bars = Accepted by grammar
- Red bars = Rejected by grammar

## Log File Format

Trace files are JSON with this structure:

```json
{
  "trace_version": "1.0",
  "metadata": {
    "model": "model.gguf",
    "grammar_file": "spec.gbnf",
    "prompt": "write a ballerina app which prints 0 to 10",
    "timestamp": "2025-12-27T10:30:00Z"
  },
  "events": [
    {
      "step": 0,
      "type": "token_filtering",
      "data": {
        "candidates_before": [
          {"token": 1509, "logit": 8.42, "p": 0.45, "str": "import"},
          {"token": 1678, "logit": 7.89, "p": 0.32, "str": "public"}
        ],
        "candidates_after": [
          {"token": 1509, "logit": 8.42, "p": 0.45, "str": "import"}
        ],
        "rejected_count": 1
      }
    },
    {
      "step": 0,
      "type": "token_accepted",
      "data": {
        "token": 1509,
        "token_str": "import"
      }
    }
  ]
}
```

## Testing

### Python Parser Tests

```bash
# Install pytest if needed
pip install pytest

# Run parser tests
python3 -m pytest tracer/
```

### Dashboard Tests

```bash
cd dashboard
npm install
npm test              # Run all tests
npm run test:ui       # Interactive UI
npm run test:coverage # Coverage report
```

Test fixtures are in `dashboard/fixtures/` and come from actual execution traces.

## File Structure

```
constrained_decoding/
├── tracer/                    # Python trace parser
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   └── exporter.py
├── dashboard/                 # Interactive visualization
│   ├── index.html
│   ├── viewer.js
│   ├── viewer.test.js
│   ├── package.json
│   ├── vitest.config.js
│   ├── fixtures/             # Test fixtures from real runs
│   └── data/                 # Processed traces
├── traces/                    # Raw trace files (gitignored)
├── run_server_with_trace.sh  # Server launcher
├── run_trace_workflow.sh     # Complete workflow
└── TRACING_README.md         # This file
```

## Troubleshooting

### Server won't start with --grammar-trace

Make sure you've applied all modifications to llama.cpp and rebuilt:
```bash
cd $LLAMACPP_DIR
make clean && make llama-server
```

### No trace file generated

Check server logs in `traces/server_*.log` for errors.

### Dashboard shows no data

1. Verify trace file exists: `ls -lh traces/`
2. Parse it manually: `python3 tracer/parser.py traces/trace_*.json -o dashboard/data/test.json --validate`
3. Check for validation errors

### Tests failing

Make sure you've installed dependencies:
```bash
cd dashboard
npm install
```

## Examples

### Example 1: foreach vs while Decision

Prompt: "write a ballerina app which prints 0 to 10"

Expected trace shows:
- Step ~25: Grammar allows both `foreach` and `while`
- Model selects `foreach` (higher probability)
- Keywords like `for` and `if` are rejected by grammar

### Example 2: Type Selection

After `foreach`, the grammar requires a type descriptor.

Expected trace shows:
- Candidates: `int`, `string`, `var`, `float`, `boolean`
- Only allowed types pass grammar filter
- Model selects `int`

## References

- **Plan File**: `/Users/wso2/.claude/plans/replicated-swimming-sunset.md`
- **GBNF Spec**: `spec_builder/grammars/spec.gbnf`
- **llama.cpp**: https://github.com/ggerganov/llama.cpp

## License

Same as parent project.
