#!/usr/bin/env python3
"""
Grammar Trace Parser
Parses llama.cpp grammar trace JSON and extracts structured data
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from models import (
    GenerationTrace,
    TokenFilteringEvent,
    TokenAcceptedEvent,
    TokenCandidate
)


class GrammarTraceParser:
    """Parser for llama.cpp grammar trace files"""

    def __init__(self):
        pass

    def parse_trace_file(self, trace_path: str) -> GenerationTrace:
        """Parse a trace JSON file into structured objects"""
        try:
            with open(trace_path, 'r') as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Trace file not found: {trace_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in trace file: {e}", file=sys.stderr)
            sys.exit(1)

        # Validate required fields
        if "trace_version" not in raw_data:
            print("Warning: trace_version not found in trace file", file=sys.stderr)

        if "events" not in raw_data:
            print("Error: No events found in trace file", file=sys.stderr)
            sys.exit(1)

        trace = GenerationTrace(
            trace_version=raw_data.get("trace_version", "unknown"),
            events=[],
            generated_tokens=[],
            generation_steps=0,
            total_rejections=0
        )

        # Parse events
        for raw_event in raw_data.get("events", []):
            event_type = raw_event.get("type")
            step = raw_event.get("step", 0)
            data = raw_event.get("data", {})

            if event_type == "token_filtering":
                event = self._parse_token_filtering(step, data)
                trace.events.append(event)
                trace.total_rejections += event.rejected_count

            elif event_type == "token_accepted":
                event = self._parse_token_accepted(step, data)
                trace.events.append(event)
                trace.generated_tokens.append(event.token_str)

            else:
                print(f"Warning: Unknown event type: {event_type}", file=sys.stderr)

        # Calculate generation steps
        if trace.events:
            trace.generation_steps = max(
                (e.step for e in trace.events if hasattr(e, 'step')),
                default=0
            )

        return trace

    def _parse_token_filtering(self, step: int, data: Dict) -> TokenFilteringEvent:
        """Parse token filtering event"""
        candidates_before = [
            TokenCandidate(
                token=c.get("token", 0),
                prob=c.get("p", 0.0),
                logit=c.get("logit", 0.0),
                token_str=c.get("str", "")
            )
            for c in data.get("candidates_before", [])
        ]

        candidates_after = [
            TokenCandidate(
                token=c.get("token", 0),
                prob=c.get("p", 0.0),
                logit=c.get("logit", 0.0),
                token_str=c.get("str", "")
            )
            for c in data.get("candidates_after", [])
        ]

        return TokenFilteringEvent(
            step=step,
            candidates_before=candidates_before,
            candidates_after=candidates_after,
            rejected_count=data.get("rejected_count", 0)
        )

    def _parse_token_accepted(self, step: int, data: Dict) -> TokenAcceptedEvent:
        """Parse token accepted event"""
        return TokenAcceptedEvent(
            step=step,
            token=data.get("token", 0),
            token_str=data.get("token_str", "")
        )

    def validate_trace(self, trace: GenerationTrace) -> List[str]:
        """Validate trace integrity and return list of warnings/errors"""
        warnings = []

        # Check for matching token_filtering and token_accepted events per step
        for step in range(trace.generation_steps + 1):
            step_summary = trace.get_step_summary(step)

            if step_summary["filtering"] is None:
                warnings.append(f"Step {step}: Missing token_filtering event")

            if step_summary["accepted"] is None:
                warnings.append(f"Step {step}: Missing token_accepted event")

            # Check that accepted token is in candidates_after
            if step_summary["filtering"] and step_summary["accepted"]:
                filtering = step_summary["filtering"]
                accepted = step_summary["accepted"]

                accepted_in_candidates = any(
                    c.token == accepted.token
                    for c in filtering.candidates_after
                )

                if not accepted_in_candidates:
                    warnings.append(
                        f"Step {step}: Accepted token {accepted.token} "
                        f"not found in candidates_after"
                    )

        return warnings


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse llama.cpp grammar trace files"
    )
    parser.add_argument(
        "trace_file",
        help="Path to trace JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for processed trace (dashboard format)"
    )
    parser.add_argument(
        "--structured", "-j",
        help="Output file for structured JSON format (simplified format with token probabilities)"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of top alternative tokens to include in structured JSON (default: 5)"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Print summary statistics"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate trace integrity"
    )

    args = parser.parse_args()

    # Parse trace
    trace_parser = GrammarTraceParser()
    trace = trace_parser.parse_trace_file(args.trace_file)

    # Validate if requested
    if args.validate:
        warnings = trace_parser.validate_trace(trace)
        if warnings:
            print(f"\n=== Validation Warnings ({len(warnings)}) ===")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("\n=== Validation Passed ===")

    # Print summary if requested
    if args.summary or not args.output:
        print(f"\n=== Trace Summary ===")
        print(f"Version: {trace.trace_version}")
        print(f"Generation steps: {trace.generation_steps}")
        print(f"Tokens generated: {len(trace.generated_tokens)}")
        print(f"Total rejections: {trace.total_rejections}")

        if trace.generated_tokens:
            generated_text = ''.join(trace.generated_tokens)
            print(f"\nGenerated text ({len(generated_text)} chars):")
            print(generated_text[:500] + ("..." if len(generated_text) > 500 else ""))

        # Show high-impact steps
        high_impact = trace.get_high_impact_steps()
        if high_impact:
            print(f"\nHigh-impact decision points ({len(high_impact)}):")
            for step_num in high_impact[:10]:
                summary = trace.get_step_summary(step_num)
                if summary["filtering"]:
                    shift = summary["filtering"].get_probability_shift()
                    token = summary["token"] or "(unknown)"
                    print(f"  Step {step_num}: {token} (prob shift: {shift*100:.1f}%)")

    # Export if output specified
    if args.output:
        from exporter import TraceExporter
        exporter = TraceExporter()
        exporter.export_for_dashboard(trace, args.output)
        print(f"\nExported to: {args.output}")

    # Export structured JSON if specified
    if args.structured:
        from exporter import TraceExporter
        exporter = TraceExporter()
        exporter.export_structured_json(trace, args.structured, top_k=args.top_k)
        print(f"\nStructured JSON exported to: {args.structured}")


if __name__ == "__main__":
    main()
