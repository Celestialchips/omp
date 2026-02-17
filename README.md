# Open Memory Protocol (OMP)

**The Deterministic Memory Layer for AI Coding Agents**

Current LLMs suffer from *Context Rot* - as conversations get longer, they forget critical syntax, misinterpret variable types, and hallucinate logic. OMP solves this by decoupling **Intent** from **Syntax**, creating a lossless, dual-track memory system that works with any LLM.

## The Problem

In long-running coding sessions, AI agents rely on summaries of previous work. This causes three cascading failures:

1. **Lossy Compression** - The LLM summarizes a 100-line file into 3 sentences. Important edge cases disappear.
2. **Observer Bias** - The model remembers its *interpretation* of the code, not the code itself.
3. **Syntax Hallucinations** - By turn 50, the agent "remembers" `validateUser(id)` as `checkUser(email)`, breaking your build.

## The Solution: Dual-Track Memory

OMP splits memory into two specialized streams that merge only at retrieval time:

| Track | Source | Stores | Veracity |
|-------|--------|--------|----------|
| **Symbolic** | Tree-sitter (deterministic parser) | Function signatures, AST hashes, dependency graphs, types | 100% Deterministic |
| **Semantic** | Observer LLM (lightweight) | User intent, architectural preferences, implicit constraints | Probabilistic |

The key insight: **an LLM is forbidden from rewriting the Symbolic Track**. It can only populate the Semantic Track. The Parser remains a rigid, unchangeable anchor of truth.

## Quick Start

```bash
pip install open-memory-protocol[all]
```

### Extract facts from code

```python
from omp import extract_from_source

result = extract_from_source("""
import jwt
from datetime import datetime

class AuthService:
    async def validate_token(self, token: str) -> dict | None:
        return jwt.decode(token, self.secret, algorithms=["HS256"])
""", "python")

# Deterministic facts - no hallucination possible
for fn in result.functions:
    print(fn.qualified_name, fn.active_pointer, fn.ast_hash)

for imp in result.imports:
    print(f"  depends on: {imp.module}")

# The Symbolic Layer (ready for your memory store)
print(result.to_symbolic_layer())
```

### Detect staleness

```python
from omp import extract_from_source, diff_extractions

old = extract_from_source("def foo(x: int) -> str: ...", "python")
new = extract_from_source("def foo(x: int, y: int) -> str: ...", "python")

report = diff_extractions(old, new)
print(report.is_stale)          # True
print(report.changed_functions)  # ['foo']
```

### Persist to SQLite

```python
from omp import extract_from_file, SQLiteStorage

with SQLiteStorage("memory.db") as store:
    result = extract_from_file("src/auth/provider.ts")
    store.save(result)

    # Later: retrieve the facts
    loaded = store.get_by_file("src/auth/provider.ts")
```

### Build Dual-Track Memory

```python
from omp import extract_from_source, reconcile, SemanticObservation

# 1. Parser extracts the facts (deterministic)
symbolic = extract_from_source(code, "typescript")

# 2. Observer LLM extracts the intent (probabilistic)
semantic = SemanticObservation(
    intent_summary="Refactoring auth for async DB lookups",
    implicit_constraints=["Must maintain backward compat"],
    user_preferences=["Prefers async/await over callbacks"],
)

# 3. Reconcile into a single Dual-Track entry
memory = reconcile(symbolic, semantic)
print(memory.to_json())
```

### Scan an entire project

```python
from omp import extract_project

project = extract_project("./my-app")
print(f"{project.total_functions} functions across {len(project.files)} files")
```

### Watch for file changes

```python
from omp import FileWatcher

watcher = FileWatcher("./my-app")
watcher.on_change(lambda event: print(f"{event.event_type}: {event.path}"))
watcher.start(interval=2.0)
```

## Supported Languages

| Language | Extension | Signatures | Imports | Classes | Interfaces |
|----------|-----------|:----------:|:-------:|:-------:|:----------:|
| Python | `.py` | Yes | Yes | Yes | - |
| TypeScript | `.ts` `.tsx` | Yes | Yes | Yes | Yes |
| JavaScript | `.js` `.jsx` | Yes | Yes | Yes | - |
| Go | `.go` | Yes | Yes | Structs | Yes |

## Architecture

```
  Code Change
       |
       v
  +-----------+         +-----------+
  | Tree-sitter|         | Observer  |
  | (Parser)   |         | (LLM)    |
  +-----------+         +-----------+
       |                      |
       v                      v
  Symbolic Layer         Semantic Layer
  (DETERMINISTIC)       (PROBABILISTIC)
  - signatures          - intent
  - ast_hash            - constraints
  - dependencies        - preferences
       |                      |
       +----------+-----------+
                  |
                  v
          Dual-Track Memory
          (Reconciled Entry)
                  |
                  v
          SQLite / Postgres
```

**Staleness Detection:** Every extraction includes an `ast_hash` per function and a `file_hash` per file. When the agent retrieves a memory, OMP compares hashes against the current file on disk. If they diverge, the memory is marked **stale** and a re-parse is triggered automatically - preventing Semantic Drift.

## CLI

```bash
# Extract a single file
omp src/auth/provider.ts

# JSON output
omp src/auth/provider.ts --json

# Symbolic layer only (Dual-Track schema format)
omp src/auth/provider.ts --symbolic

# Scan an entire project
omp ./my-app --project

# Exclude directories
omp ./my-app --project --exclude dist coverage
```

## Why This Beats Current Solutions

| Approach | Problem |
|----------|---------|
| **Standard RAG** | Embeds code as text. The embedding loses syntax precision. |
| **LLM Summarization** | Recursive summaries compound errors. By hop 3, the original code is gone. |
| **Mastra / Observational Memory** | Relies on LLM reflection - even a "Reflector Agent" can hallucinate `int` as `string`. |
| **OMP (Dual-Track)** | Parser produces facts that are *impossible* to hallucinate. The LLM only handles intent. |

## Development

```bash
git clone https://github.com/open-memory-protocol/omp.git
cd omp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
