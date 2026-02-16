"""
OMP Benchmark Runner - CLI entry point.

Usage:
    python -m benchmarks.run                     # Simulated mode (default)
    python -m benchmarks.run --mode simulated    # Same as above
    python -m benchmarks.run --mode claude       # Real Claude API
    python -m benchmarks.run --mode both         # Run both and compare
    python -m benchmarks.run --json              # Output results as JSON
"""

from __future__ import annotations

import argparse
import json
import sys

from benchmarks.codebase import get_turns, get_ground_truth
from benchmarks.scorer import BenchmarkResult, score_turn, format_results
from benchmarks.simulator import SimulatedLLM, PerfectRecall, DriftConfig


def run_simulated(seed: int = 42) -> tuple[BenchmarkResult, BenchmarkResult]:
    """Run the deterministic simulation benchmark.

    Returns:
        (simulated_llm_result, omp_result)
    """
    turns = get_turns()
    sim = SimulatedLLM(DriftConfig(seed=seed))
    omp = PerfectRecall()

    sim_result = BenchmarkResult(mode="simulated_llm")
    omp_result = BenchmarkResult(mode="omp_anchored")

    for turn in turns:
        ground_truth = get_ground_truth(turn)

        # Simulated LLM recall
        sim_recalled = sim.recall(turn.number, ground_truth)
        sim_score = score_turn(turn.number, ground_truth, sim_recalled)
        sim_result.turn_scores.append(sim_score)

        # OMP perfect recall
        omp_recalled = omp.recall(turn.number, ground_truth)
        omp_score = score_turn(turn.number, ground_truth, omp_recalled)
        omp_result.turn_scores.append(omp_score)

    return sim_result, omp_result


def _progress(turn: int, mode: str) -> None:
    """Print progress dots."""
    if turn % 5 == 0:
        print(f"    Turn {turn}/50 ({mode})", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="benchmarks.run",
        description="OMP Long-Term Integrity Benchmark",
    )
    parser.add_argument(
        "--mode",
        choices=["simulated", "claude", "both"],
        default="simulated",
        help="Benchmark mode (default: simulated)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for simulated mode (default: 42)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write JSON results to file",
    )

    args = parser.parse_args()

    all_results: list[BenchmarkResult] = []

    # ── Simulated mode ──
    if args.mode in ("simulated", "both"):
        print("\n  Running deterministic simulation...\n", file=sys.stderr)
        sim_result, omp_result = run_simulated(seed=args.seed)
        all_results.extend([sim_result, omp_result])

        if not args.json:
            print(format_results([sim_result, omp_result]))

    # ── Claude mode ──
    if args.mode in ("claude", "both"):
        print("\n  Running Claude API benchmark...\n", file=sys.stderr)
        from benchmarks.claude_bench import run_claude_benchmark
        baseline, omp = run_claude_benchmark(on_progress=_progress)
        all_results.extend([baseline, omp])

        if not args.json:
            print(format_results([baseline, omp]))

    # ── Combined comparison ──
    if args.mode == "both" and not args.json:
        print("\n  Combined comparison (all modes):")
        print(format_results(all_results))

    # ── JSON output ──
    if args.json:
        output = {
            "benchmark": "OMP Long-Term Integrity Test",
            "results": [r.to_dict() for r in all_results],
        }
        print(json.dumps(output, indent=2))

    if args.output:
        output = {
            "benchmark": "OMP Long-Term Integrity Test",
            "results": [r.to_dict() for r in all_results],
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Results written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
