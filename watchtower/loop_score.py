"""
Loop Score Algorithm — The core brain of Watchtower.

Detects repetitive patterns in multi-agent execution by tracking
three signals: node repetition, sequence cycles, and tool call repeats.

Score range: 0.0 (no loops) to 1.0 (fully stuck).
"""

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Step:
    """A single execution step captured by the interceptor."""
    node_name: str
    tool_calls: list[str] = field(default_factory=list)  # ["search('AI market')", ...]
    action_label: str = ""  # human-readable label when no tool calls
    step_number: int = 0


@dataclass
class LoopResult:
    """The result of a loop analysis."""
    score: float                    # 0.0 to 1.0
    node_repetition: float          # signal 1
    sequence_repetition: float      # signal 2
    tool_repetition: float          # signal 3
    pattern: str                    # human-readable pattern like "A→B→A→B"
    repeat_count: int               # how many times the pattern repeated
    is_alert: bool                  # True if score >= threshold


class LoopDetector:
    """
    Sliding-window loop detector.
    
    Keeps the last `window_size` steps and computes a Loop Score
    on every new step. No ML, no embeddings — just pattern matching.
    """

    def __init__(self, window_size: int = 10, threshold: float = 0.7):
        self.window_size = window_size
        self.threshold = threshold
        self.steps: list[Step] = []

    def add_step(self, step: Step) -> LoopResult:
        """Add a new step and compute the current Loop Score."""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)

        # Only analyze within the window
        window = self.steps[-self.window_size:]

        if len(window) < 3:
            return LoopResult(
                score=0.0, node_repetition=0.0,
                sequence_repetition=0.0, tool_repetition=0.0,
                pattern="", repeat_count=0, is_alert=False
            )

        # --- Signal 1: Node Repetition ---
        # Two sub-signals:
        # a) Concentration: how dominant is the most frequent node?
        # b) Uniqueness: how few unique nodes appear?
        #    If window=10 has only 2 unique nodes, that's suspicious.
        node_names = [s.node_name for s in window]
        counts = Counter(node_names)
        most_common_count = counts.most_common(1)[0][1]
        concentration = most_common_count / len(window)

        unique_nodes = len(counts)
        # Fewer unique nodes = more suspicious.
        # 1 unique node = 1.0, 2 = 0.8, 3 = 0.6, etc.
        uniqueness_signal = max(0.0, 1.0 - (unique_nodes - 1) * 0.2)

        node_rep = 0.5 * concentration + 0.5 * uniqueness_signal

        # --- Signal 2: Sequence Repetition ---
        # Look for repeating n-grams (patterns of 2-4 nodes).
        seq_rep, pattern, repeat_count = self._detect_sequence_pattern(node_names)

        # --- Signal 3: Tool Call Repetition ---
        # Same tool called with same/similar params?
        tool_rep = self._detect_tool_repetition(window)

        # --- Combine into Loop Score ---
        # Weights: sequence patterns are strongest signal,
        # node repetition is supporting, tool repetition confirms.
        score = (
            0.45 * seq_rep +
            0.30 * node_rep +
            0.25 * tool_rep
        )

        # Clamp to 0-1
        score = min(1.0, max(0.0, score))

        return LoopResult(
            score=round(score, 2),
            node_repetition=round(node_rep, 2),
            sequence_repetition=round(seq_rep, 2),
            tool_repetition=round(tool_rep, 2),
            pattern=pattern,
            repeat_count=repeat_count,
            is_alert=score >= self.threshold
        )

    def _detect_sequence_pattern(self, names: list[str]) -> tuple[float, str, int]:
        """
        Find repeating patterns in the node sequence.
        
        Tries pattern lengths 2, 3, 4.
        Example: [A, B, A, B, A, B] → pattern "A→B", repeated 3x, score ~1.0
        """
        best_score = 0.0
        best_pattern = ""
        best_count = 0

        for pattern_len in range(2, min(5, len(names) // 2 + 1)):
            # Take the last `pattern_len` nodes as candidate pattern
            candidate = names[-pattern_len:]

            # Count how many times this pattern appears consecutively
            # going backwards from the end
            count = 0
            i = len(names) - pattern_len
            while i >= 0:
                segment = names[i:i + pattern_len]
                if segment == candidate:
                    count += 1
                    i -= pattern_len
                else:
                    break

            if count >= 2:
                # Score: how much of the window is covered by this pattern
                coverage = (count * pattern_len) / len(names)
                score = min(1.0, coverage)

                if score > best_score:
                    best_score = score
                    best_pattern = "→".join(candidate)
                    best_count = count

        return best_score, best_pattern, best_count

    def _detect_tool_repetition(self, window: list[Step]) -> float:
        """
        Check if the same tool calls are being repeated.
        
        Compares tool call strings directly (exact match).
        Returns ratio of repeated calls to total calls.
        """
        all_calls = []
        for step in window:
            all_calls.extend(step.tool_calls)

        if len(all_calls) < 2:
            return 0.0

        # Count how many calls are duplicates
        call_counts = Counter(all_calls)
        repeated = sum(c - 1 for c in call_counts.values() if c > 1)

        return repeated / len(all_calls)

    def reset(self):
        """Clear all recorded steps."""
        self.steps = []
