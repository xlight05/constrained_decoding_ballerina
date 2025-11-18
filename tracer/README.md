# Rejection Sampling Tracer

Tools for tracing and analyzing rejection sampling in llama.cpp constrained decoding.

## Components

### 1. merge_logs.py - Standalone Log Merger

Combines `debug_response.json` (API response with logprobs) and `rejection_log.json` (rejection sampling events) into a unified view.

**Usage:**
```bash
python merge_logs.py <debug_response.json> <rejection_log.json> [output.json]
```

**Example:**
```bash
python merge_logs.py ../invoker/debug_response.json ../traces/rejection_log.json ../traces/combined.json
```

**Output Format:**
```json
{
  "metadata": {
    "request_id": "...",
    "model": "...",
    "created": 1234567890
  },
  "steps": [
    {
      "step": 0,
      "token": {
        "id": 198,
        "text": "\n",
        "logprob": -22.10
      },
      "api_top_logprobs": [...],
      "rejection_sampling": {
        "was_rejected": true,
        "rejected": {"id": 151667, "text": "<think>", "prob": 1.0},
        "pre_masking": [...],
        "post_grammar": [...],
        "post_chain": [...],
        "resampled": {"id": 198, "text": "\n", "prob": 1.0}
      }
    }
  ],
  "summary": {
    "total_steps": 51,
    "rejected_steps": 6,
    "rejection_rate": 0.118
  }
}
```

### 2. proxy_server.py - Automatic Combining Proxy

A proxy server that sits between your client and llama-server, automatically merging API responses with rejection logs.

**Installation:**
```bash
pip install -r requirements.txt
```

**Usage:**
```bash
# Start llama-server with rejection logging
llama-server \
  --model /path/to/model.gguf \
  --port 8080 \
  --rejection-log ./traces/rejection_log.json

# In another terminal, start the proxy
python proxy_server.py \
  --llama-url http://localhost:8080 \
  --proxy-port 8081 \
  --output-dir ./traces \
  --rejection-log ./traces/rejection_log.json

# Configure your client to use the proxy
# Change from: http://localhost:8080
# To:          http://localhost:8081
```

**Options:**
- `--llama-url`: URL of llama-server (default: http://localhost:8080)
- `--proxy-port`: Port for proxy (default: 8081)
- `--output-dir`: Where to save combined JSONs (default: ./traces)
- `--rejection-log`: Path to rejection log file (default: ./traces/rejection_log.json)
- `--no-save`: Don't save combined outputs to disk

**How It Works:**

1. Client sends request to proxy (port 8081)
2. Proxy forwards request to llama-server (port 8080)
3. llama-server processes request and writes rejection events to `rejection_log.json`
4. Proxy receives response from llama-server
5. Proxy reads rejection log and finds events for this request
6. Proxy merges response + rejection events into combined JSON
7. Proxy saves combined JSON to `output_dir/combined_TIMESTAMP.json`
8. Proxy returns original response to client

**Example with Ballerina Client:**

```ballerina
// Change the client URL to point to the proxy
http:Client cl = check new ("http://localhost:8081/v1", timeout = 120);

// Make requests as normal - combined JSON will be auto-generated
ChatResp resp = check cl->post("/chat/completions", req);
```

## Workflow

### Development/Testing Workflow

1. **Start llama-server with rejection logging:**
   ```bash
   llama-server \
     --model /path/to/model.gguf \
     --rejection-log ./traces/rejection_log.json
   ```

2. **Make a request with logprobs:**
   ```bash
   curl http://localhost:8080/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [{"role": "user", "content": "Hello"}],
       "grammar": "...",
       "logprobs": 5
     }' > debug_response.json
   ```

3. **Stop llama-server** (to close rejection log file)

4. **Merge logs:**
   ```bash
   python merge_logs.py debug_response.json traces/rejection_log.json traces/combined.json
   ```

### Production Workflow

1. **Start llama-server:**
   ```bash
   llama-server --model /path/to/model.gguf --rejection-log ./traces/rejection_log.json
   ```

2. **Start proxy:**
   ```bash
   python proxy_server.py --llama-url http://localhost:8080 --proxy-port 8081
   ```

3. **Point clients to proxy:**
   ```
   http://localhost:8081 (instead of http://localhost:8080)
   ```

4. **Combined JSONs are automatically saved** to `./traces/combined_*.json`

## Understanding the Output

Each step in the combined JSON shows:

- **token**: The actual token that was generated
- **api_top_logprobs**: Top N tokens by probability (from API response)
- **rejection_sampling.was_rejected**: Whether rejection occurred
- **rejection_sampling.rejected**: The token that was initially sampled but rejected
- **rejection_sampling.pre_masking**: Probability distribution before grammar
- **rejection_sampling.post_grammar**: Valid tokens after grammar masking
- **rejection_sampling.post_chain**: Tokens after chain samplers (top_k, top_p, etc.)
- **rejection_sampling.resampled**: The final token after resampling

### Key Insights

- **pre_masking**: Shows what the model "wanted" to generate
- **post_grammar**: Shows which tokens are grammar-valid
- **post_chain**: Shows how chain samplers filter further
- **Rejection rate**: Higher rate means grammar frequently conflicts with model preferences

## Notes

- The proxy currently uses a simple heuristic to match rejection events with requests (most recent task_id)
- For production use with concurrent requests, llama-server would need to return task_id in API responses
- The `-inf` values in rejection_log.json are automatically converted to `null` during merging
- Rejection log file must be closed (server stopped) for complete JSON parsing in standalone merger
- Proxy handles incomplete rejection log files by attempting to fix JSON structure
