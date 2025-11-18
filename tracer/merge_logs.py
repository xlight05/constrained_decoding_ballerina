#!/usr/bin/env python3
"""
Merge debug_response.json and rejection_log.json into a unified view.

For each token generation step, combines:
- API response logprobs from debug_response.json
- Rejection sampling details from rejection_log.json

Correlation: Uses step number to match events.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_json(file_path: str) -> Dict:
    """Load and parse JSON file, handling -inf values."""
    with open(file_path, 'r') as f:
        content = f.read()
        # Replace -inf with null for valid JSON (will be converted to None in Python)
        content = content.replace('-inf', 'null')
        return json.loads(content)


def save_json(data: Dict, file_path: str) -> None:
    """Save data as formatted JSON."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved combined output to: {file_path}")


def create_rejection_map(rejection_log: Dict) -> Dict[int, Dict]:
    """
    Create a map of step -> rejection event for quick lookup.

    Args:
        rejection_log: Parsed rejection_log.json

    Returns:
        Dictionary mapping step number to rejection event
    """
    rejection_map = {}
    for event in rejection_log.get('events', []):
        step = event['step']
        rejection_map[step] = event
    return rejection_map


def merge_logs(debug_response: Dict, rejection_log: Dict) -> Dict:
    """
    Merge debug_response and rejection_log into unified structure.

    Args:
        debug_response: Parsed debug_response.json (API response)
        rejection_log: Parsed rejection_log.json (rejection sampling events)

    Returns:
        Combined dictionary with merged data
    """
    # Build rejection event map for O(1) lookup
    rejection_map = create_rejection_map(rejection_log)

    # Extract logprobs content array
    logprobs_content = debug_response.get('choices', [{}])[0].get('logprobs', {}).get('content', [])

    # Create combined structure
    combined = {
        "metadata": {
            "request_id": debug_response.get('id', 'unknown'),
            "model": debug_response.get('model', 'unknown'),
            "created": debug_response.get('created', 0),
            "rejection_log_version": rejection_log.get('log_version', 'unknown'),
            "rejection_log_timestamp": rejection_log.get('timestamp', 'unknown'),
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

        # Add rejection sampling data if available for this step
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
                "note": "Token was grammar-valid on first sample, no rejection occurred"
            }

        combined["steps"].append(step_data)

    # Add summary statistics
    total_steps = len(combined["steps"])
    rejected_steps = sum(1 for s in combined["steps"] if s["rejection_sampling"]["was_rejected"])

    combined["summary"] = {
        "total_steps": total_steps,
        "rejected_steps": rejected_steps,
        "rejection_rate": rejected_steps / total_steps if total_steps > 0 else 0.0,
        "final_output": debug_response.get('choices', [{}])[0].get('message', {}).get('content', ''),
    }

    return combined


def main():
    """Main entry point for the merge script."""
    if len(sys.argv) < 3:
        print("Usage: python merge_logs.py <debug_response.json> <rejection_log.json> [output.json]")
        print("\nExample:")
        print("  python merge_logs.py invoker/debug_response.json traces/rejection_log.json traces/combined.json")
        sys.exit(1)

    debug_response_path = sys.argv[1]
    rejection_log_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else "combined_output.json"

    # Validate input files exist
    if not Path(debug_response_path).exists():
        print(f"Error: File not found: {debug_response_path}")
        sys.exit(1)

    if not Path(rejection_log_path).exists():
        print(f"Error: File not found: {rejection_log_path}")
        sys.exit(1)

    print(f"Loading debug_response from: {debug_response_path}")
    debug_response = load_json(debug_response_path)

    print(f"Loading rejection_log from: {rejection_log_path}")
    rejection_log = load_json(rejection_log_path)

    print("Merging logs...")
    combined = merge_logs(debug_response, rejection_log)

    print(f"Merged {len(combined['steps'])} steps")
    print(f"  - Rejected steps: {combined['summary']['rejected_steps']}")
    print(f"  - Rejection rate: {combined['summary']['rejection_rate']:.1%}")

    save_json(combined, output_path)
    print("\nDone!")


if __name__ == "__main__":
    main()
