#!/usr/bin/env python3
"""
Proxy server for llama-server that automatically combines API responses with rejection logs.

This proxy:
1. Intercepts requests to llama-server
2. Forwards them to the actual llama-server
3. Collects rejection sampling events for this request
4. Merges response with rejection log
5. Returns/saves combined JSON

Usage:
    python proxy_server.py --llama-url http://localhost:8080 --proxy-port 8081 --output-dir ./traces
"""

import argparse
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from flask import Flask, request, Response, jsonify
import requests


app = Flask(__name__)


class RejectionLogMonitor:
    """Monitor rejection_log.json file for new events matching a task_id."""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.lock = threading.Lock()

    def get_events_for_task(self, task_id: int, timeout: float = 30.0) -> List[Dict]:
        """
        Poll rejection log file and extract events for given task_id.

        Args:
            task_id: Task ID to filter events
            timeout: Max time to wait for events (seconds)

        Returns:
            List of rejection events for this task
        """
        start_time = time.time()
        events = []

        while time.time() - start_time < timeout:
            try:
                with self.lock:
                    if Path(self.log_file_path).exists():
                        with open(self.log_file_path, 'r') as f:
                            content = f.read()
                            # Handle -inf values
                            content = content.replace('-inf', 'null')

                            # Try to parse (might be incomplete if server is still writing)
                            try:
                                log_data = json.loads(content)
                                all_events = log_data.get('events', [])

                                # Filter events for this task_id
                                events = [e for e in all_events if e.get('task_id') == task_id]

                                if events:
                                    return events

                            except json.JSONDecodeError:
                                # File might be incomplete, try adding closing brackets
                                content_fixed = content.rstrip().rstrip(',') + '\n  ]\n}'
                                try:
                                    log_data = json.loads(content_fixed)
                                    all_events = log_data.get('events', [])
                                    events = [e for e in all_events if e.get('task_id') == task_id]
                                    if events:
                                        return events
                                except json.JSONDecodeError:
                                    pass  # Still being written

            except Exception as e:
                print(f"Warning: Error reading rejection log: {e}")

            time.sleep(0.1)  # Poll every 100ms

        return events


class ProxyConfig:
    """Global configuration for the proxy server."""
    llama_url: str = "http://localhost:8080"
    output_dir: Path = Path("./traces")
    rejection_log_path: str = "./traces/rejection_log.json"
    monitor: Optional[RejectionLogMonitor] = None
    save_combined: bool = True


def merge_response_with_rejections(response_data: Dict, rejection_events: List[Dict]) -> Dict:
    """
    Merge API response with rejection sampling events.

    Args:
        response_data: llama-server API response
        rejection_events: List of rejection events for this request

    Returns:
        Combined dictionary
    """
    # Build rejection event map by step
    rejection_map = {event['step']: event for event in rejection_events}

    # Extract logprobs content
    logprobs_content = response_data.get('choices', [{}])[0].get('logprobs', {}).get('content', [])

    # Create combined structure
    combined = {
        "metadata": {
            "request_id": response_data.get('id', 'unknown'),
            "model": response_data.get('model', 'unknown'),
            "created": response_data.get('created', 0),
            "timestamp": datetime.now().isoformat(),
        },
        "steps": []
    }

    # Merge each step
    for step_idx, logprob_entry in enumerate(logprobs_content):
        step_data = {
            "step": step_idx,
            "token": {
                "id": logprob_entry.get('id'),
                "text": logprob_entry.get('token'),
                "bytes": logprob_entry.get('bytes'),
                "logprob": logprob_entry.get('logprob'),
            },
            "api_top_logprobs": logprob_entry.get('top_logprobs', []),
        }

        # Add rejection sampling data if available
        if step_idx in rejection_map:
            rejection_event = rejection_map[step_idx]
            step_data["rejection_sampling"] = {
                "task_id": rejection_event.get('task_id'),
                "slot_id": rejection_event.get('slot_id'),
                "was_rejected": True,
                "rejected": rejection_event.get('rejected'),
                "pre_masking": rejection_event.get('pre_masking', []),
                "post_grammar": rejection_event.get('post_grammar', []),
                "post_chain": rejection_event.get('post_chain', []),
                "resampled": rejection_event.get('resampled'),
            }
        else:
            step_data["rejection_sampling"] = {
                "was_rejected": False,
                "note": "Token was grammar-valid on first sample"
            }

        combined["steps"].append(step_data)

    # Add summary
    total_steps = len(combined["steps"])
    rejected_steps = sum(1 for s in combined["steps"] if s["rejection_sampling"]["was_rejected"])

    combined["summary"] = {
        "total_steps": total_steps,
        "rejected_steps": rejected_steps,
        "rejection_rate": rejected_steps / total_steps if total_steps > 0 else 0.0,
        "final_output": response_data.get('choices', [{}])[0].get('message', {}).get('content', ''),
    }

    return combined


@app.route('/v1/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_request(endpoint):
    """Proxy all /v1/* requests to llama-server and merge with rejection log."""

    # Forward request to llama-server
    target_url = f"{ProxyConfig.llama_url}/v1/{endpoint}"

    # Copy request data
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    print(f"Proxying {request.method} /v1/{endpoint} -> {target_url}")

    # Forward the request
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.get_data(),
        params=request.args,
        allow_redirects=False,
    )

    # Check if this is a chat completion request with logprobs
    if endpoint == 'chat/completions' and request.method == 'POST':
        try:
            response_data = resp.json()
            request_data = request.get_json()

            # Check if logprobs were requested
            if request_data and request_data.get('logprobs'):
                # Extract task_id from response (this is a challenge - llama-server doesn't return task_id)
                # We'll use a workaround: monitor rejection log for new events with recent timestamp

                print("Chat completion with logprobs detected, collecting rejection data...")

                # Wait a bit for rejection log to be written
                time.sleep(0.5)

                # Get all recent rejection events (last 10 seconds)
                # Note: This is a simplification. In production, you'd want better task_id tracking
                rejection_events = []
                if ProxyConfig.monitor:
                    # For now, get the most recent events
                    # TODO: Implement proper task_id correlation
                    try:
                        with open(ProxyConfig.rejection_log_path, 'r') as f:
                            content = f.read().replace('-inf', 'null')
                            content_fixed = content.rstrip().rstrip(',') + '\n  ]\n}'
                            log_data = json.loads(content_fixed)
                            all_events = log_data.get('events', [])

                            # Get events from the last few seconds (assuming single-threaded testing)
                            # In production, need proper task_id correlation
                            if all_events:
                                # Simple heuristic: take most recent task_id's events
                                latest_task_id = all_events[-1].get('task_id')
                                rejection_events = [e for e in all_events if e.get('task_id') == latest_task_id]

                    except Exception as e:
                        print(f"Warning: Could not load rejection events: {e}")

                # Merge response with rejection data
                if rejection_events:
                    combined = merge_response_with_rejections(response_data, rejection_events)

                    # Save combined output
                    if ProxyConfig.save_combined:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file = ProxyConfig.output_dir / f"combined_{timestamp}.json"
                        with open(output_file, 'w') as f:
                            json.dump(combined, f, indent=2)
                        print(f"Saved combined output to: {output_file}")

                    # Return combined data in a custom header
                    response = Response(
                        response=resp.content,
                        status=resp.status_code,
                        headers=dict(resp.headers)
                    )
                    response.headers['X-Combined-Data-Available'] = str(output_file)
                    return response

        except Exception as e:
            print(f"Warning: Error processing response: {e}")

    # Return original response
    return Response(
        response=resp.content,
        status=resp.status_code,
        headers=dict(resp.headers)
    )


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_other(path):
    """Proxy all other requests directly."""
    target_url = f"{ProxyConfig.llama_url}/{path}"
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.get_data(),
        params=request.args,
        allow_redirects=False,
    )

    return Response(
        response=resp.content,
        status=resp.status_code,
        headers=dict(resp.headers)
    )


def main():
    parser = argparse.ArgumentParser(description='Proxy server for llama-server with rejection log merging')
    parser.add_argument('--llama-url', default='http://localhost:8080',
                        help='URL of llama-server (default: http://localhost:8080)')
    parser.add_argument('--proxy-port', type=int, default=8081,
                        help='Port for proxy server (default: 8081)')
    parser.add_argument('--output-dir', default='./traces',
                        help='Directory to save combined outputs (default: ./traces)')
    parser.add_argument('--rejection-log', default='./traces/rejection_log.json',
                        help='Path to rejection log file (default: ./traces/rejection_log.json)')
    parser.add_argument('--no-save', action='store_true',
                        help='Do not save combined outputs to disk')

    args = parser.parse_args()

    # Configure proxy
    ProxyConfig.llama_url = args.llama_url
    ProxyConfig.output_dir = Path(args.output_dir)
    ProxyConfig.output_dir.mkdir(parents=True, exist_ok=True)
    ProxyConfig.rejection_log_path = args.rejection_log
    ProxyConfig.monitor = RejectionLogMonitor(args.rejection_log)
    ProxyConfig.save_combined = not args.no_save

    print(f"Starting proxy server...")
    print(f"  Proxy listening on: http://localhost:{args.proxy_port}")
    print(f"  Forwarding to: {args.llama_url}")
    print(f"  Rejection log: {args.rejection_log}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Save combined: {ProxyConfig.save_combined}")
    print()
    print(f"Configure your client to use: http://localhost:{args.proxy_port}")

    app.run(host='0.0.0.0', port=args.proxy_port, debug=False)


if __name__ == '__main__':
    main()
