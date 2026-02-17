"""
Scorer - Compares recalled signatures against ground truth.

For each function in the ground truth, checks:
1. Name match - Does the recalled name exactly match?
2. Parameter match - Same names, same types, same defaults?
3. Return type match - Exact string match?
4. Existence - Did the LLM "remember" a function that was deleted?
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FunctionScore:
    """Score for a single function comparison."""

    qualified_name: str
    name_match: bool = False
    params_match: bool = False
    return_type_match: bool = False
    exists_in_recall: bool = False
    is_phantom: bool = False  # Recalled but doesn't exist in ground truth

    @property
    def score(self) -> float:
        """0.0 to 1.0 - average of the three match components."""
        if not self.exists_in_recall:
            return 0.0
        checks = [self.name_match, self.params_match, self.return_type_match]
        return sum(checks) / len(checks)


@dataclass
class TokenStats:
    """Token usage for a single turn."""

    summary_tokens: int = 0       # Tokens in the running summary / compressed context
    source_tokens: int = 0        # Tokens in the source code at this turn
    prompt_tokens: int = 0        # Total input tokens for the update call
    cumulative_tokens: int = 0    # Running total of all input tokens across turns

    def to_dict(self) -> dict:
        return {
            "summary_tokens": self.summary_tokens,
            "source_tokens": self.source_tokens,
            "prompt_tokens": self.prompt_tokens,
            "cumulative_tokens": self.cumulative_tokens,
        }


@dataclass
class TurnScore:
    """Aggregate score for a single turn."""

    turn: int
    function_scores: list[FunctionScore] = field(default_factory=list)
    phantom_count: int = 0  # Functions recalled that don't exist
    token_stats: TokenStats | None = None

    @property
    def accuracy(self) -> float:
        """Overall accuracy as a percentage (0-100)."""
        if not self.function_scores:
            return 0.0
        total = sum(fs.score for fs in self.function_scores)
        return (total / len(self.function_scores)) * 100

    @property
    def perfect(self) -> bool:
        return self.accuracy == 100.0 and self.phantom_count == 0

    @property
    def drifted_functions(self) -> list[str]:
        return [fs.qualified_name for fs in self.function_scores if fs.score < 1.0]


@dataclass
class BenchmarkResult:
    """Full benchmark result across all turns."""

    mode: str  # "simulated" | "claude_baseline" | "claude_omp"
    turn_scores: list[TurnScore] = field(default_factory=list)

    @property
    def summary_table(self) -> list[dict]:
        """Return a list of dicts suitable for tabular display."""
        rows = []
        for ts in self.turn_scores:
            row = {
                "turn": ts.turn,
                "accuracy": round(ts.accuracy, 1),
                "functions": len(ts.function_scores),
                "drifted": len(ts.drifted_functions),
                "phantoms": ts.phantom_count,
            }
            if ts.token_stats:
                row["tokens"] = ts.token_stats.to_dict()
            rows.append(row)
        return rows

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "turns": self.summary_table,
        }


def score_turn(
    turn_number: int,
    ground_truth: dict[str, dict],
    recalled: dict[str, dict],
) -> TurnScore:
    """Score a single turn by comparing recalled signatures against ground truth.

    Args:
        turn_number: The turn number.
        ground_truth: Dict mapping qualified_name -> {name, parameters, return_type, ...}
                      as produced by codebase.get_ground_truth().
        recalled: Same format, representing what the LLM (or simulator) "remembers."

    Returns:
        A TurnScore with per-function breakdown.
    """
    function_scores: list[FunctionScore] = []
    phantom_count = 0

    # Score each ground-truth function
    for qname, gt_info in ground_truth.items():
        fs = FunctionScore(qualified_name=qname)

        if qname in recalled:
            rc = recalled[qname]
            fs.exists_in_recall = True
            fs.name_match = rc.get("name") == gt_info["name"]
            fs.params_match = rc.get("parameters") == gt_info["parameters"]
            fs.return_type_match = rc.get("return_type") == gt_info["return_type"]
        else:
            fs.exists_in_recall = False

        function_scores.append(fs)

    # Check for phantom functions (recalled but not in ground truth)
    for qname in recalled:
        if qname not in ground_truth:
            phantom_count += 1
            function_scores.append(FunctionScore(
                qualified_name=qname,
                is_phantom=True,
                exists_in_recall=True,
            ))

    return TurnScore(
        turn=turn_number,
        function_scores=function_scores,
        phantom_count=phantom_count,
    )


def format_results(
    results: list[BenchmarkResult],
    sample_turns: list[int] | None = None,
) -> str:
    """Format benchmark results as a readable table.

    Args:
        results: One or more BenchmarkResult objects to display side-by-side.
        sample_turns: Which turns to display (default: [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]).
    """
    if sample_turns is None:
        sample_turns = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

    # Check if any result has token stats
    has_tokens = any(
        ts.token_stats is not None
        for r in results
        for ts in r.turn_scores
    )

    # Build header
    mode_names = [r.mode for r in results]
    header_parts = ["Turn"]
    for name in mode_names:
        header_parts.append(f"{name:>18s}")
    if has_tokens:
        header_parts.append("  Context Tk")
    header_parts.append("  Drift")
    header = " | ".join(header_parts)
    separator = "-" * len(header)

    lines = [
        "",
        "  OMP Long-Term Integrity Benchmark",
        "  " + "=" * 50,
        "",
        f"  {header}",
        f"  {separator}",
    ]

    # Build turn index for each result
    turn_indices: list[dict[int, TurnScore]] = []
    for r in results:
        idx = {ts.turn: ts for ts in r.turn_scores}
        turn_indices.append(idx)

    for t in sample_turns:
        parts = [f"{t:4d}"]
        drift_info = ""
        token_info = ""
        for i, r in enumerate(results):
            ts = turn_indices[i].get(t)
            if ts:
                acc_str = f"{ts.accuracy:5.1f}%"
                parts.append(f"{acc_str:>18s}")
                if ts.drifted_functions and i == 0:
                    drift_info = f"  {len(ts.drifted_functions)} fn(s)"
                if has_tokens and ts.token_stats and i == 0:
                    stk = ts.token_stats.summary_tokens
                    token_info = f"  {stk:>10,d}"
            else:
                parts.append(f"{'N/A':>18s}")
        if has_tokens:
            parts.append(token_info)
        parts.append(drift_info)
        lines.append("  " + " | ".join(parts))

    lines.append(f"  {separator}")

    # Token summary footer
    if has_tokens:
        first_result = results[0]
        scored = [ts for ts in first_result.turn_scores if ts.token_stats]
        if scored:
            final = scored[-1]
            lines.append("")
            lines.append(
                f"  Context Tk = tokens in the running summary (compressed context)."
            )
            lines.append(
                f"  Final summary: {final.token_stats.summary_tokens:,d} tokens | "
                f"Cumulative input: {final.token_stats.cumulative_tokens:,d} tokens"
            )

    lines.append("")
    return "\n".join(lines)
