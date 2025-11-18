"""
Data models for grammar trace parsing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TokenCandidate:
    """Represents a single token candidate with its probability"""
    token: int
    prob: float
    logit: float
    token_str: str = ""

    def __post_init__(self):
        # Handle missing token_str field
        if not self.token_str:
            self.token_str = f"<token_{self.token}>"


@dataclass
class TokenFilteringEvent:
    """Represents a token filtering event where grammar constraints are applied"""
    step: int
    candidates_before: List[TokenCandidate]
    candidates_after: List[TokenCandidate]
    rejected_count: int

    def get_probability_shift(self) -> float:
        """Calculate how much probability mass was filtered out by grammar"""
        total_before = sum(c.prob for c in self.candidates_before)
        total_after = sum(c.prob for c in self.candidates_after)
        return total_before - total_after

    def get_rejection_details(self) -> List[Dict]:
        """Return list of rejected tokens with their probabilities"""
        before_ids = {c.token for c in self.candidates_before}
        after_ids = {c.token for c in self.candidates_after}
        rejected_ids = before_ids - after_ids

        return [
            {
                "token": c.token,
                "prob": c.prob,
                "logit": c.logit,
                "token_str": c.token_str
            }
            for c in self.candidates_before
            if c.token in rejected_ids
        ]


@dataclass
class TokenAcceptedEvent:
    """Represents a token that was accepted/selected by the sampler"""
    step: int
    token: int
    token_str: str


@dataclass
class GenerationTrace:
    """Complete trace of a generation sequence"""
    trace_version: str
    events: List = field(default_factory=list)
    generated_tokens: List[str] = field(default_factory=list)
    generation_steps: int = 0
    total_rejections: int = 0

    def get_step_summary(self, step: int) -> Dict:
        """Get all events for a specific step"""
        step_events = [e for e in self.events if hasattr(e, 'step') and e.step == step]

        # Get all filtering events for this step
        filtering_events = [e for e in step_events if isinstance(e, TokenFilteringEvent)]

        # Use the filtering event with the MOST candidates (has the real probability distribution)
        # llama.cpp may call token_filtering multiple times per step
        filtering_event = None
        if filtering_events:
            filtering_event = max(
                filtering_events,
                key=lambda e: len(e.candidates_before)
            )

        accepted_event = next(
            (e for e in step_events if isinstance(e, TokenAcceptedEvent)),
            None
        )

        return {
            "step": step,
            "filtering": filtering_event,
            "accepted": accepted_event,
            "token": accepted_event.token_str if accepted_event else None
        }

    def get_high_impact_steps(self, threshold: float = 0.3) -> List[int]:
        """Get steps where grammar had significant impact (>threshold prob shift)"""
        high_impact = []
        for event in self.events:
            if isinstance(event, TokenFilteringEvent):
                if event.get_probability_shift() > threshold:
                    high_impact.append(event.step)
        return high_impact
