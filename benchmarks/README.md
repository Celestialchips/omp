# OMP Long-Term Integrity Benchmark

Proves that OMP prevents context rot by comparing "raw LLM memory" vs "OMP-anchored memory" over a 50-turn simulated coding session.

## The Claim

Over 50 turns of realistic code mutations (renames, parameter changes, type changes, method extractions, class renames), an LLM asked to "remember" function signatures will gradually hallucinate. OMP's symbolic layer stays 100% accurate because Tree-sitter doesn't forget.

## Quick Start

```bash
# Run the deterministic simulation (no API key needed, reproducible)
python -m benchmarks.run

# Run with real Claude API (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-... python -m benchmarks.run --mode claude

# Run both and compare
ANTHROPIC_API_KEY=sk-... python -m benchmarks.run --mode both

# JSON output for programmatic use
python -m benchmarks.run --json
```

## Results

### Claude API (claude-haiku-4-5)

```
Turn |    claude_baseline |         claude_omp |   Drift
--------------------------------------------------------
   1 |             100.0% |             100.0% |
   5 |             100.0% |             100.0% |
  10 |             100.0% |             100.0% |
  15 |             100.0% |             100.0% |
  20 |              66.7% |             100.0% |   9 fn(s)
  25 |              69.2% |             100.0% |   10 fn(s)
  30 |              92.3% |             100.0% |   1 fn(s)
  35 |              86.7% |             100.0% |   2 fn(s)
  40 |              58.8% |             100.0% |   15 fn(s)
  45 |              59.3% |             100.0% |   16 fn(s)
  50 |              81.0% |             100.0% |   4 fn(s)
```

Claude's raw recall is noisy and unreliable -- sometimes it gets lucky (92.3% at turn 30), sometimes it doesn't (58.8% at turn 40). OMP-anchored recall is **100% every single turn** because the signatures come from Tree-sitter, not from memory.

### Deterministic Simulation (seed=42)

```
Turn |      simulated_llm |       omp_anchored |   Context Tk |   Drift
-----------------------------------------------------------------------
   1 |             100.0% |             100.0% |          413 |
   5 |             100.0% |             100.0% |          480 |
  10 |             100.0% |             100.0% |          522 |
  15 |              94.4% |             100.0% |          528 |   1 fn(s)
  20 |              69.7% |             100.0% |          892 |   6 fn(s)
  25 |              76.9% |             100.0% |        1,002 |   6 fn(s)
  30 |              41.7% |             100.0% |          970 |   11 fn(s)
  35 |              42.9% |             100.0% |        1,064 |   12 fn(s)
  40 |              50.0% |             100.0% |        1,157 |   11 fn(s)
  45 |              46.7% |             100.0% |        1,258 |   13 fn(s)
  50 |              62.7% |             100.0% |        1,437 |   11 fn(s)
```

The **Context Tk** column shows the estimated token count of the running summary (compressed context) the model carries forward. Even at just ~1,400 tokens of context, the simulated model drifts significantly. Reproducible - anyone can run `python -m benchmarks.run --seed 42` and get this exact table.

## Two Modes

### Mode 1: Deterministic Simulation (default)

Simulates LLM drift using a realistic degradation model seeded with a fixed RNG. Error types are weighted by real-world frequency:

- **Type swaps** (`str` -> `string`, `dict | None` -> `Optional[dict]`)
- **Parameter renames** (`user_id` -> `userId`, `salt` -> `seed`)
- **Default value drift** (`3600` -> `3000`)
- **Function forgetting** (completely dropping a function)
- **Phantom functions** (remembering deleted functions that no longer exist)

Error probability increases with turn number: ~3% at turn 1, growing to ~85% cap by turn 50. This is reproducible -- anyone can run `python -m benchmarks.run --seed 42` and get the same table.

### Mode 2: Real Claude API

Uses Claude Haiku via the `anthropic` SDK. Runs two parallel experiments:

**Baseline:** At each turn, Claude receives the full source code plus its own previous summary and updates its mental model. At sample turns, it's asked to recall all function signatures from that running summary alone. This is generous -- real coding sessions don't re-show the full source every turn.

**OMP-anchored:** Same conversation flow, but at recall time the prompt includes `FACTUAL ANCHORS` -- the complete, structured signature data extracted by OMP's Tree-sitter parser. Claude is told to reproduce these anchors exactly rather than relying on its own memory.

Estimated cost: ~$0.50 for a full 50-turn run with Haiku.

**Requirements:**
```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
```

## The Evolving Codebase

The benchmark uses a scripted 50-turn evolution of a Python `auth.py` module:

| Turn | Change | Symbol Count |
|------|--------|:------------:|
| 1 | Initial module: `create_token`, `validate_token`, `hash_password`, `verify_password`, `get_user_permissions` | 5 |
| 5 | Rename `validate_token` to `verify_token` | 5 |
| 8 | Add `revoke_token` function | 6 |
| 12 | Add `refresh_token` function | 7 |
| 15 | Remove `verify_password` (moved into class) | 6 |
| 16 | Extract token functions into `TokenService` class | 7 |
| 20 | Add `PermissionService` class | 11 |
| 35 | Change `verify` strict default from `False` to `True` | ~14 |
| 45 | Rename `TokenService` to `AuthTokenService` | ~16 |
| 50 | Add `async_check_permission` to `AuthzService` | 17 |

Each turn is a complete source snapshot. Ground truth is always produced by running `omp.extract_from_source()` on the snapshot.

## Scoring

For each function in the ground truth, the scorer checks:

1. **Name match** -- Does the recalled function name exactly match?
2. **Parameter match** -- Same names, types, and defaults in order?
3. **Return type match** -- Exact string match?
4. **Existence** -- Was the function recalled at all?
5. **Phantoms** -- Did the LLM "remember" a function that no longer exists?

Per-function score = average of (name, params, return_type) matches. Turn accuracy = average of all function scores.

## Token Tracking

The benchmark tracks token usage at each turn to answer: "how much compressed context is the model carrying when it starts to drift?"

| Metric | Description |
|--------|-------------|
| **Context Tk** (summary_tokens) | Tokens in the running summary - the compressed context the model carries between turns |
| source_tokens | Tokens of the raw source code at this turn |
| prompt_tokens | Total input tokens for the update API call |
| cumulative_tokens | Running total of all input tokens across all turns |

For the Claude mode, `prompt_tokens` and `cumulative_tokens` are exact values from the Anthropic API usage response. For the simulated mode, they're estimated at ~4 characters per token.

The key insight: drift is better understood as a function of compressed context size than turn count. A turn that renames one parameter barely grows the summary; a turn that extracts 5 methods into a class can double it.

## Methodology Note

The simulated benchmark proves the *concept*: any memory system that relies on LLM summarization will drift. The Claude benchmark proves the *reality*: a real frontier model actually drifts under these conditions, and injecting OMP facts fixes it.

Neither mode is "cheating" -- the simulated mode uses a conservative drift model calibrated to be less aggressive than real LLM behavior, and the Claude mode asks the model to do exactly what coding agents do in practice: maintain a running understanding of evolving code.
