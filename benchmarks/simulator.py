"""
Deterministic Drift Simulator - Simulates LLM memory degradation.

Models the realistic ways an LLM "forgets" code over long conversations:
- Type swaps (str → string, dict → object)
- Parameter renames (user_id → userId, salt → seed)
- Default value drift (3600 → 3000, "user" → "default")
- Return type hallucinations (dict | None → Optional[dict])
- Function name mutations (verify_token → validate_token)
- Phantom functions (remembering deleted functions)

Error probability increases with turn number. Seeded RNG for reproducibility.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

from benchmarks.codebase import Turn, get_ground_truth


# ---------------------------------------------------------------------------
# Corruption strategies
# ---------------------------------------------------------------------------

TYPE_SWAPS = {
    "str": ["string", "String", "text"],
    "int": ["integer", "number", "Int"],
    "bool": ["boolean", "Bool", "flag"],
    "float": ["double", "number", "Float"],
    "list": ["array", "Array", "List"],
    "list[str]": ["list[string]", "list", "List[str]"],
    "frozenset[str]": ["set[str]", "frozenset", "list[str]"],
    "dict": ["object", "Dict", "mapping"],
    "dict | None": ["Optional[dict]", "dict", "dict | null"],
    "User | None": ["Optional[User]", "User", "dict | None", "user | None"],
    "str | None": ["Optional[str]", "string | None", "str"],
    "bytes": ["str", "bytearray", "Bytes"],
}

PARAM_RENAMES = {
    "user_id": ["userId", "uid", "user"],
    "token": ["tok", "jwt", "auth_token"],
    "password": ["passwd", "pwd", "pass_str"],
    "hashed": ["hash", "hash_value", "stored_hash"],
    "salt": ["seed", "nonce", "salt_value"],
    "expires_in": ["ttl", "expiry", "timeout"],
    "extend_by": ["ttl", "extension", "duration"],
    "strict": ["validate", "strict_mode", "enforce"],
    "role": ["user_role", "access_level", "role_name"],
    "scope": ["context", "namespace", "scope_name"],
    "secret_key": ["key", "secret", "api_key"],
    "algorithm": ["algo", "hash_algo", "method"],
    "audit_log": ["log", "audit", "log_action"],
    "permission": ["perm", "access", "right"],
    "iterations": ["rounds", "count", "iters"],
    "max_age": ["ttl", "max_ttl", "expiry"],
    "issuer": ["iss", "provider", "source"],
    "policy": ["mode", "strategy", "access_policy"],
    "default_scope": ["scope", "default_ns", "base_scope"],
}

DEFAULT_SWAPS = {
    "3600": ["3000", "1800", "7200"],
    "7200": ["3600", "36000", "7000"],
    "86400": ["3600", "43200", "86000"],
    "100000": ["10000", "1000", "50000"],
    '"user"': ['"default"', '"basic"', '"member"'],
    '"sha256"': ['"sha512"', '"md5"', '"sha384"'],
    '"default"': ['"global"', '"main"', '"base"'],
    '"omp"': ['"auth"', '"app"', '"system"'],
    '"rbac"': ['"acl"', '"abac"', '"simple"'],
    "True": ["False"],
    "False": ["True"],
}

PHANTOM_FUNCTIONS = [
    {"name": "validate_token", "qualified_name": "validate_token",
     "parameters": [("token", "str", None)], "return_type": "dict",
     "is_async": False, "is_static": False, "kind": "function"},
    {"name": "verify_password", "qualified_name": "verify_password",
     "parameters": [("password", "str", None), ("hashed", "str", None)],
     "return_type": "bool", "is_async": False, "is_static": False, "kind": "function"},
    {"name": "get_user_permissions", "qualified_name": "get_user_permissions",
     "parameters": [("user_id", "str", None)], "return_type": "list",
     "is_async": False, "is_static": False, "kind": "function"},
    {"name": "hash_password", "qualified_name": "hash_password",
     "parameters": [("password", "str", None)], "return_type": "str",
     "is_async": False, "is_static": False, "kind": "function"},
]


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


@dataclass
class DriftConfig:
    """Configuration for the drift simulator."""

    seed: int = 42
    base_error_rate: float = 0.03     # 3% chance per function at turn 1
    error_growth: float = 0.025       # Additional error rate per turn
    max_error_rate: float = 0.85      # Cap at 85%
    phantom_start_turn: int = 15      # Phantoms can appear after this turn
    phantom_probability: float = 0.08  # Per-turn probability of a phantom


class SimulatedLLM:
    """Simulates an LLM that gradually forgets/corrupts code memories.

    Usage:
        sim = SimulatedLLM(DriftConfig(seed=42))
        for turn in get_turns():
            ground_truth = get_ground_truth(turn)
            recalled = sim.recall(turn.number, ground_truth)
    """

    def __init__(self, config: DriftConfig | None = None):
        self.config = config or DriftConfig()
        self.rng = random.Random(self.config.seed)
        self._deleted_functions: list[dict] = []

    def _error_rate(self, turn: int) -> float:
        """Compute the per-function error probability at a given turn."""
        rate = self.config.base_error_rate + (turn - 1) * self.config.error_growth
        return min(rate, self.config.max_error_rate)

    def _corrupt_type(self, type_str: str | None) -> str | None:
        if type_str is None:
            return None
        if type_str in TYPE_SWAPS:
            return self.rng.choice(TYPE_SWAPS[type_str])
        return type_str

    def _corrupt_param_name(self, name: str) -> str:
        if name in PARAM_RENAMES:
            return self.rng.choice(PARAM_RENAMES[name])
        return name

    def _corrupt_default(self, default: str | None) -> str | None:
        if default is None:
            return None
        if default in DEFAULT_SWAPS:
            return self.rng.choice(DEFAULT_SWAPS[default])
        return default

    def _corrupt_function(self, fn: dict, turn: int) -> dict:
        """Apply random corruption to a function's remembered signature."""
        fn = copy.deepcopy(fn)
        error_rate = self._error_rate(turn)

        # Corrupt return type
        if self.rng.random() < error_rate:
            fn["return_type"] = self._corrupt_type(fn["return_type"])

        # Corrupt parameters
        new_params = []
        for pname, ptype, pdefault in fn["parameters"]:
            if self.rng.random() < error_rate * 0.7:
                pname = self._corrupt_param_name(pname)
            if self.rng.random() < error_rate * 0.8:
                ptype = self._corrupt_type(ptype)
            if self.rng.random() < error_rate * 0.5:
                pdefault = self._corrupt_default(pdefault)
            new_params.append((pname, ptype, pdefault))

        # Occasionally drop a parameter entirely
        if len(new_params) > 1 and self.rng.random() < error_rate * 0.3:
            drop_idx = self.rng.randint(0, len(new_params) - 1)
            new_params.pop(drop_idx)

        fn["parameters"] = new_params

        # Occasionally swap async flag
        if self.rng.random() < error_rate * 0.2:
            fn["is_async"] = not fn["is_async"]

        return fn

    def recall(self, turn: int, ground_truth: dict[str, dict]) -> dict[str, dict]:
        """Simulate LLM recall of function signatures at a given turn.

        Args:
            turn: The turn number (1-50).
            ground_truth: The actual signatures at this turn.

        Returns:
            A corrupted version of the ground truth representing LLM recall.
        """
        recalled: dict[str, dict] = {}
        error_rate = self._error_rate(turn)

        for qname, fn_info in ground_truth.items():
            # Chance of completely forgetting a function
            if self.rng.random() < error_rate * 0.15:
                continue

            # Apply corruption
            if self.rng.random() < error_rate:
                recalled[qname] = self._corrupt_function(fn_info, turn)
            else:
                recalled[qname] = copy.deepcopy(fn_info)

        # Phantom functions: "remember" things that were deleted earlier
        if turn >= self.config.phantom_start_turn:
            if self.rng.random() < self.config.phantom_probability * (turn / 50):
                phantom = self.rng.choice(PHANTOM_FUNCTIONS)
                if phantom["qualified_name"] not in ground_truth:
                    recalled[phantom["qualified_name"]] = copy.deepcopy(phantom)

        return recalled


class PerfectRecall:
    """The OMP baseline - always returns ground truth exactly.

    This represents what OMP provides: deterministic, zero-drift recall
    because the signatures come from Tree-sitter, not from LLM memory.
    """

    def recall(self, turn: int, ground_truth: dict[str, dict]) -> dict[str, dict]:
        return copy.deepcopy(ground_truth)
