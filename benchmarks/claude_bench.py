"""
Claude API Benchmark

Runs two parallel experiments using Claude Haiku:
1. Baseline: Claude maintains a running summary, then recalls signatures.
2. OMP-anchored: Same flow, but each turn includes FACTUAL ANCHORS from Tree-sitter.

Requires: ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

from benchmarks.codebase import Turn, get_ground_truth, get_turns
from benchmarks.scorer import BenchmarkResult, TokenStats, TurnScore, score_turn

# Model to use - Haiku for cost efficiency
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096


def _get_client():
    """Lazily import and create the Anthropic client."""
    try:
        import anthropic
    except ImportError:
        print("Error: 'anthropic' package not installed.", file=sys.stderr)
        print("Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def _call_claude(client, system: str, messages: list[dict]) -> tuple[str, int, int]:
    """Make a Claude API call with full message history.

    Returns:
        (response_text, input_tokens, output_tokens)
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    )
    text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    return text, input_tokens, output_tokens


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token for code/English mix."""
    return len(text) // 4


def _format_ground_truth_as_example(gt: dict[str, dict]) -> str:
    """Format ground truth in the exact JSON schema we expect back.

    This produces a concrete example so Claude knows the exact format.
    """
    example = {}
    for qname, info in list(gt.items())[:2]:
        example[qname] = {
            "name": info["name"],
            "qualified_name": info["qualified_name"],
            "parameters": [
                [p[0], p[1], _normalize_default_for_json(p[2])]
                for p in info["parameters"]
            ],
            "return_type": info["return_type"],
            "is_async": info["is_async"],
            "is_static": info["is_static"],
            "kind": info["kind"],
        }
    return json.dumps(example, indent=2)


# ---------------------------------------------------------------------------
# Default value normalization
# ---------------------------------------------------------------------------

def _normalize_default_for_json(default) -> object:
    """Normalize a default value from ground truth for JSON serialization."""
    if default is None:
        return None
    s = str(default)
    # Python None literal → JSON null
    if s == "None":
        return None
    # Strip surrounding quotes from tree-sitter extracted strings
    # e.g., '"user"' → "user", '"sha256"' → "sha256"
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    # Booleans
    if s == "True":
        return True
    if s == "False":
        return False
    # Integers
    try:
        return int(s)
    except ValueError:
        pass
    return s


def _normalize_default_from_recall(default) -> str | None:
    """Normalize a default value from Claude's recall for comparison."""
    if default is None:
        return None
    return str(default)


def _normalize_default_from_ground_truth(default) -> str | None:
    """Normalize a default value from ground truth for comparison."""
    if default is None:
        return None
    s = str(default)
    # Python None literal → None
    if s == "None":
        return None
    # Strip surrounding quotes: '"user"' → 'user'
    if len(s) >= 2 and s[0] in ('"', "'") and s[-1] in ('"', "'"):
        s = s[1:-1]
    return s


def _normalize_params_for_comparison(
    params: list,
) -> list[tuple[str, str | None, str | None]]:
    """Normalize parameters for comparison, handling format differences."""
    result = []
    for p in params:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            name = str(p[0])
            ptype = str(p[1]) if p[1] is not None else None
            default = _normalize_default_from_recall(p[2]) if len(p) > 2 else None
            # Normalize None-like values
            if default in ("null", "None", "none"):
                default = None
            result.append((name, ptype, default))
    return result


def _normalize_gt_params_for_comparison(
    params: list,
) -> list[tuple[str, str | None, str | None]]:
    """Normalize ground-truth parameters for comparison."""
    result = []
    for p in params:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            name = str(p[0])
            ptype = str(p[1]) if p[1] is not None else None
            default = _normalize_default_from_ground_truth(p[2]) if len(p) > 2 else None
            result.append((name, ptype, default))
    return result


# ---------------------------------------------------------------------------
# Baseline run - raw LLM memory
# ---------------------------------------------------------------------------

BASELINE_SYSTEM = """You are a coding assistant tracking an evolving Python codebase.
You maintain a running memory of every function and method signature.
You must remember precisely: qualified name (ClassName.method for methods),
parameters with types and defaults, return types, and whether functions are async.

When asked to summarize: provide a brief summary of changes.
When asked to recall signatures: respond with ONLY a JSON object, no explanation."""


RECALL_PROMPT_TEMPLATE = """Based on your running memory, recall EVERY function and
method signature that CURRENTLY exists in the codebase.

Use "ClassName.method_name" as the key for class methods.

Respond with ONLY a raw JSON object (no markdown fencing, no explanation).
Use this EXACT format - match the key structure precisely:

{example}

Include ALL functions and methods currently in the codebase."""


def run_baseline(
    client,
    turns: list[Turn],
    sample_turns: list[int],
    on_progress: Optional[callable] = None,
) -> BenchmarkResult:
    """Run the baseline (raw LLM recall) benchmark.

    At each turn, Claude receives previous context + new code and updates
    its understanding. At sample turns, we ask Claude to recall all signatures.
    """
    result = BenchmarkResult(mode="claude_baseline")
    running_summary = "No previous context - this is the first turn."
    cumulative_input_tokens = 0

    for turn in turns:
        # Build the update prompt WITH previous context
        update_prompt = (
            f"PREVIOUS CONTEXT (your running memory):\n{running_summary}\n\n"
            f"---\n\n"
            f"Turn {turn.number}: {turn.description}\n\n"
            f"Here is the CURRENT full source code:\n\n"
            f"```python\n{turn.source}\n```\n\n"
            f"Update your mental model. Summarize what changed AND list every "
            f"function/method signature that currently exists (name, params with "
            f"types+defaults, return type, async status). This summary will be "
            f"your only memory for the next turn."
        )

        messages = [{"role": "user", "content": update_prompt}]
        response, input_toks, _ = _call_claude(client, BASELINE_SYSTEM, messages)
        running_summary = response
        cumulative_input_tokens += input_toks

        # Estimate token counts for this turn
        summary_tokens = _estimate_tokens(running_summary)
        source_tokens = _estimate_tokens(turn.source)

        if on_progress:
            on_progress(turn.number, "baseline")

        # Score at sample turns
        if turn.number in sample_turns:
            ground_truth = get_ground_truth(turn)
            example = _format_ground_truth_as_example(ground_truth)
            recall_prompt = RECALL_PROMPT_TEMPLATE.format(example=example)

            recall_messages = [
                {"role": "user", "content": update_prompt},
                {"role": "assistant", "content": running_summary},
                {"role": "user", "content": recall_prompt},
            ]
            recall_response, recall_toks, _ = _call_claude(
                client, BASELINE_SYSTEM, recall_messages
            )
            cumulative_input_tokens += recall_toks
            recalled = _parse_recall_json(recall_response)
            ts = _score_with_normalization(turn.number, ground_truth, recalled)
            ts.token_stats = TokenStats(
                summary_tokens=summary_tokens,
                source_tokens=source_tokens,
                prompt_tokens=input_toks,
                cumulative_tokens=cumulative_input_tokens,
            )
            result.turn_scores.append(ts)

        time.sleep(0.3)

    return result


# ---------------------------------------------------------------------------
# OMP-anchored run
# ---------------------------------------------------------------------------

OMP_SYSTEM = """You are a coding assistant using the Open Memory Protocol (OMP).
You receive FACTUAL ANCHORS from a deterministic parser at each turn.
These anchors are 100% accurate - they come from Tree-sitter, not from memory.
You MUST NOT contradict the FACTUAL ANCHORS. They are the source of truth.

When asked to recall signatures: reproduce the FACTUAL ANCHORS exactly as
structured JSON. Do not add, remove, or modify any function signatures.
Respond with ONLY a JSON object, no explanation, no markdown fencing."""


def run_omp_anchored(
    client,
    turns: list[Turn],
    sample_turns: list[int],
    on_progress: Optional[callable] = None,
) -> BenchmarkResult:
    """Run the OMP-anchored benchmark.

    Same as baseline, but at recall time the prompt includes FACTUAL ANCHORS
    in the exact format expected for output.
    """
    result = BenchmarkResult(mode="claude_omp")
    running_intent = "No previous context - this is the first turn."
    cumulative_input_tokens = 0

    for turn in turns:
        ground_truth = get_ground_truth(turn)

        # Format the ground truth as the FACTUAL ANCHORS in output-ready format
        anchors_json = _format_anchors(ground_truth)

        update_prompt = (
            f"Turn {turn.number}: {turn.description}\n\n"
            f"FACTUAL ANCHORS (from deterministic parser - 100% accurate):\n"
            f"{anchors_json}\n\n"
            f"Note the intent behind this change (2-3 sentences). "
            f"Do NOT contradict the FACTUAL ANCHORS."
        )

        messages = [{"role": "user", "content": update_prompt}]
        response, input_toks, _ = _call_claude(client, OMP_SYSTEM, messages)
        running_intent = response
        cumulative_input_tokens += input_toks

        summary_tokens = _estimate_tokens(running_intent)
        source_tokens = _estimate_tokens(anchors_json)

        if on_progress:
            on_progress(turn.number, "omp")

        # Score at sample turns
        if turn.number in sample_turns:
            recall_prompt = (
                f"Recall every function and method in the codebase.\n\n"
                f"FACTUAL ANCHORS (deterministic ground truth - reproduce exactly):\n"
                f"{anchors_json}\n\n"
                f"Reproduce the FACTUAL ANCHORS above as a JSON object.\n"
                f"Use the EXACT same keys, parameter names, types, defaults, "
                f"and return types. Do not add or remove anything.\n"
                f"Respond with ONLY the JSON object."
            )

            recall_messages = [
                {"role": "user", "content": update_prompt},
                {"role": "assistant", "content": running_intent},
                {"role": "user", "content": recall_prompt},
            ]
            recall_response, recall_toks, _ = _call_claude(
                client, OMP_SYSTEM, recall_messages
            )
            cumulative_input_tokens += recall_toks
            recalled = _parse_recall_json(recall_response)
            ts = _score_with_normalization(turn.number, ground_truth, recalled)
            ts.token_stats = TokenStats(
                summary_tokens=summary_tokens,
                source_tokens=source_tokens,
                prompt_tokens=input_toks,
                cumulative_tokens=cumulative_input_tokens,
            )
            result.turn_scores.append(ts)

        time.sleep(0.3)

    return result


def _format_anchors(ground_truth: dict[str, dict]) -> str:
    """Format ground truth as FACTUAL ANCHORS in the exact output JSON format."""
    anchors = {}
    for qname, info in ground_truth.items():
        anchors[qname] = {
            "name": info["name"],
            "qualified_name": info["qualified_name"],
            "parameters": [
                [p[0], p[1], _normalize_default_for_json(p[2])]
                for p in info["parameters"]
            ],
            "return_type": info["return_type"],
            "is_async": info["is_async"],
            "is_static": info["is_static"],
            "kind": info["kind"],
        }
    return json.dumps(anchors, indent=2)


# ---------------------------------------------------------------------------
# Scoring with normalization
# ---------------------------------------------------------------------------

def _score_with_normalization(
    turn_number: int,
    ground_truth: dict[str, dict],
    recalled: dict[str, dict],
) -> TurnScore:
    """Score with normalized parameter comparison.

    Wraps the standard scorer but normalizes parameters on both sides first.
    """
    # Normalize ground truth params
    normalized_gt = {}
    for qname, info in ground_truth.items():
        normalized_gt[qname] = {
            **info,
            "parameters": _normalize_gt_params_for_comparison(info["parameters"]),
        }

    # Normalize recalled params
    normalized_rc = {}
    for qname, info in recalled.items():
        normalized_rc[qname] = {
            **info,
            "parameters": _normalize_params_for_comparison(
                info.get("parameters", [])
            ),
        }

    return score_turn(turn_number, normalized_gt, normalized_rc)


# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------

def _parse_recall_json(response: str) -> dict[str, dict]:
    """Parse the LLM's JSON recall response, with fallback for malformed output."""
    text = response.strip()

    # Strip markdown fencing if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    if not isinstance(data, dict):
        return {}

    # Normalize the format
    recalled: dict[str, dict] = {}
    for qname, info in data.items():
        if not isinstance(info, dict):
            continue

        # Normalize parameters to list-of-tuples format
        params = info.get("parameters", [])
        normalized_params = []
        for p in params:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                name = str(p[0])
                ptype = str(p[1]) if p[1] is not None else None
                default = p[2] if len(p) > 2 else None
                # Normalize None-like defaults
                if default is None or default in ("null", "None", "none"):
                    default = None
                normalized_params.append((name, ptype, default))
            elif isinstance(p, dict):
                # Handle {"name": ..., "type": ..., "default": ...} format
                name = str(p.get("name", ""))
                ptype = str(p["type"]) if p.get("type") is not None else None
                default = p.get("default")
                if default is None or default in ("null", "None", "none"):
                    default = None
                normalized_params.append((name, ptype, default))

        info["parameters"] = normalized_params
        recalled[qname] = info

    return recalled


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_claude_benchmark(
    sample_turns: list[int] | None = None,
    on_progress: Optional[callable] = None,
) -> tuple[BenchmarkResult, BenchmarkResult]:
    """Run both baseline and OMP-anchored benchmarks using Claude.

    Returns:
        (baseline_result, omp_result)
    """
    if sample_turns is None:
        sample_turns = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

    client = _get_client()
    turns = get_turns()

    print("  Running Claude baseline (raw LLM recall)...")
    baseline = run_baseline(client, turns, sample_turns, on_progress)

    print("  Running Claude OMP-anchored (with FACTUAL ANCHORS)...")
    omp = run_omp_anchored(client, turns, sample_turns, on_progress)

    return baseline, omp
