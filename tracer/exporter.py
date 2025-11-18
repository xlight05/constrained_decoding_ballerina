"""
Export trace data for dashboard consumption
"""

import json
import math
from typing import Dict, List
from models import GenerationTrace, TokenFilteringEvent, TokenAcceptedEvent


class TraceExporter:
    """Export trace data in dashboard-friendly format"""

    @staticmethod
    def _normalize_logits_to_probs(candidates: List) -> List:
        """Convert logits to probabilities using softmax"""
        if not candidates:
            return []

        # Extract logits
        logits = [c.logit for c in candidates]

        # Softmax: exp(logit) / sum(exp(logits))
        # Use log-sum-exp trick for numerical stability
        max_logit = max(logits)
        exp_logits = [math.exp(logit - max_logit) for logit in logits]
        sum_exp = sum(exp_logits)

        # Update probabilities
        normalized = []
        for c, exp_val in zip(candidates, exp_logits):
            prob = exp_val / sum_exp if sum_exp > 0 else 0
            normalized.append({
                "token": c.token,
                "prob": prob,
                "logit": c.logit,
                "str": c.token_str
            })

        return normalized

    def export_for_dashboard(self, trace: GenerationTrace, output_path: str):
        """Export complete trace in format optimized for visualization"""

        # Calculate statistics
        filtering_events = [
            e for e in trace.events
            if isinstance(e, TokenFilteringEvent)
        ]

        stats = self._calculate_statistics(filtering_events)

        # Build timeline
        timeline = self._build_timeline(trace)

        # Identify decision points
        decision_points = self._identify_decision_points(filtering_events)

        dashboard_data = {
            "metadata": {
                "trace_version": trace.trace_version,
                "generation_steps": trace.generation_steps,
                "total_tokens": len(trace.generated_tokens),
                "total_rejections": trace.total_rejections
            },
            "statistics": stats,
            "decision_points": decision_points,
            "timeline": timeline,
            "generated_text": ''.join(trace.generated_tokens)
        }

        with open(output_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

    def _calculate_statistics(self, filtering_events: List[TokenFilteringEvent]) -> Dict:
        """Calculate statistics about token rejections"""
        if not filtering_events:
            return {}

        rejection_counts = [e.rejected_count for e in filtering_events]

        # Calculate prob shifts using normalized probabilities
        prob_shifts = []
        for e in filtering_events:
            candidates_before_norm = self._normalize_logits_to_probs(e.candidates_before)
            candidates_after_norm = self._normalize_logits_to_probs(e.candidates_after)

            before_ids = {c.token for c in e.candidates_before}
            after_ids = {c.token for c in e.candidates_after}
            rejected_ids = before_ids - after_ids

            prob_shift = sum(
                c["prob"] for c in candidates_before_norm
                if c["token"] in rejected_ids
            )
            prob_shifts.append(prob_shift)

        return {
            "total_filtering_events": len(filtering_events),
            "avg_rejections_per_step": sum(rejection_counts) / len(rejection_counts),
            "max_rejections_in_step": max(rejection_counts),
            "avg_prob_shift": sum(prob_shifts) / len(prob_shifts) if prob_shifts else 0,
            "max_prob_shift": max(prob_shifts) if prob_shifts else 0
        }

    def _identify_decision_points(
        self,
        filtering_events: List[TokenFilteringEvent],
        threshold: float = 0.3
    ) -> List[Dict]:
        """Identify steps where grammar had significant impact"""
        decision_points = []

        for event in filtering_events:
            prob_shift = event.get_probability_shift()

            # Significant if >30% probability was filtered
            if prob_shift > threshold:
                rejected_details = event.get_rejection_details()

                # Sort by probability (highest first)
                top_rejected = sorted(
                    rejected_details,
                    key=lambda x: x["prob"],
                    reverse=True
                )[:5]

                decision_points.append({
                    "step": event.step,
                    "prob_shift": prob_shift,
                    "rejections": event.rejected_count,
                    "top_rejected": top_rejected
                })

        return decision_points

    def _build_timeline(self, trace: GenerationTrace) -> List[Dict]:
        """Build step-by-step timeline for visualization"""
        timeline = []

        for step in range(trace.generation_steps + 1):
            step_summary = trace.get_step_summary(step)

            # Find filtering event for this step
            filtering = step_summary.get("filtering")

            # Find accepted token
            accepted = step_summary.get("accepted")

            timeline_entry = {
                "step": step,
                "token": accepted.token_str if accepted else None,
                "token_id": accepted.token if accepted else None,
            }

            if filtering:
                # Normalize logits to probabilities for ALL candidates
                # (do this BEFORE limiting to top 20 so probabilities are accurate)
                candidates_before_norm = self._normalize_logits_to_probs(filtering.candidates_before)
                candidates_after_norm = self._normalize_logits_to_probs(filtering.candidates_after)

                # Calculate probability shift: sum of probabilities of REJECTED tokens
                # Rejected = tokens in before but not in after
                before_ids = {c.token for c in filtering.candidates_before}
                after_ids = {c.token for c in filtering.candidates_after}
                rejected_ids = before_ids - after_ids

                # Sum up probabilities of rejected tokens
                prob_shift = sum(
                    c["prob"] for c in candidates_before_norm
                    if c["token"] in rejected_ids
                )

                # Sort by probability (highest first) and limit to top 20
                candidates_before_sorted = sorted(
                    candidates_before_norm,
                    key=lambda c: c["prob"],
                    reverse=True
                )[:20]

                candidates_after_sorted = sorted(
                    candidates_after_norm,
                    key=lambda c: c["prob"],
                    reverse=True
                )[:20]

                timeline_entry.update({
                    "candidates_before": candidates_before_sorted,
                    "candidates_after": candidates_after_sorted,
                    "rejected_count": filtering.rejected_count,
                    "prob_shift": prob_shift
                })

            timeline.append(timeline_entry)

        return timeline

    def export_structured_json(self, trace: GenerationTrace, output_path: str, top_k: int = 5):
        """
        Export trace in simplified structured JSON format showing token probabilities.

        Args:
            trace: The generation trace to export
            output_path: Path to write the JSON file
            top_k: Number of top alternative tokens to include (default: 5)

        Output format:
        [
          {
            "step": 1,
            "accepted_token": "The",
            "accepted_probability": 0.42,
            "all_tokens": [
              {"token": "The", "probability": 0.42},
              {"token": "A", "probability": 0.31},
              ...
            ]
          },
          ...
        ]
        """
        structured_data = []

        for step in range(trace.generation_steps + 1):
            step_summary = trace.get_step_summary(step)

            filtering = step_summary.get("filtering")
            accepted = step_summary.get("accepted")

            if not filtering or not accepted:
                # Skip steps without complete data
                continue

            # Normalize logits to probabilities
            # Use candidates_after (after grammar filtering) to get accurate probabilities
            # for the tokens that were actually available for selection
            candidates_norm = self._normalize_logits_to_probs(filtering.candidates_after)

            # Sort by probability (highest first)
            candidates_sorted = sorted(
                candidates_norm,
                key=lambda c: c["prob"],
                reverse=True
            )

            # Find the accepted token's probability
            accepted_prob = 0.0
            for candidate in candidates_norm:
                if candidate["token"] == accepted.token:
                    accepted_prob = candidate["prob"]
                    break

            # Build all_tokens list with top_k tokens
            all_tokens = [
                {
                    "token": c["str"],
                    "probability": round(c["prob"], 4)
                }
                for c in candidates_sorted[:top_k]
            ]

            step_entry = {
                "step": step,
                "accepted_token": accepted.token_str,
                "accepted_probability": round(accepted_prob, 4),
                "all_tokens": all_tokens
            }

            structured_data.append(step_entry)

        # Write to file
        with open(output_path, 'w') as f:
            json.dump(structured_data, f, indent=2)

        return structured_data
