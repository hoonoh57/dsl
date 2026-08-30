"""JSON-safe public wrapper for the trusted v2 invariant implementation.

The executable invariant logic is preserved byte-for-byte in
``dsl_feature_invariants_impl``. This wrapper only normalizes report values at
the module API boundary so FastAPI can serialize deterministic diagnostics.
"""
from __future__ import annotations

import math

from core import dsl_feature_invariants_impl as _impl


for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_invariant(invariant_id: str) -> dict:
    return _json_safe(_impl.run_invariant(invariant_id))


def run_all_invariants() -> dict:
    return _json_safe(_impl.run_all_invariants())
