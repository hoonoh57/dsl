"""Provider-free exact-time context adapter for AXIS 1 backtests."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from axes.axis1_dsl.runtime.dsl_context import BINDING_POLICY, DSLContextSeriesBinding


BACKTEST_CONTEXT_POLICY = "EXACT_MARKET_BAR_TIMES_PREPARED_BINDING_NO_PROVIDER_CALL"


def prepare_backtest_parent_context(
    *,
    market: Mapping[str, Any],
    binding: DSLContextSeriesBinding | None,
) -> tuple[DSLContextSeriesBinding | None, dict[str, Any]]:
    """Validate an already-prepared immutable binding against backtest bars.

    AXIS 1 never owns or calls parent/context providers.  The supplied binding
    must already be typed and frozen, must target the same instrument, and its
    target times must exactly equal the market bars.  No nearest-time lookup,
    carry-forward, interpolation or defaulting is performed.
    """
    if binding is None:
        return None, {
            "supplied": False,
            "policy": BACKTEST_CONTEXT_POLICY,
            "binding_policy": BINDING_POLICY,
        }
    if not isinstance(binding, DSLContextSeriesBinding):
        raise ValueError("parent_context_binding은 DSLContextSeriesBinding이어야 합니다.")
    binding.validate()

    meta = market.get("_meta") or {}
    if not isinstance(meta, Mapping):
        raise ValueError("parent context backtest market _meta는 Mapping이어야 합니다.")
    instrument = str(meta.get("instrument") or "").strip()
    if not instrument:
        raise ValueError("parent context backtest에는 market _meta.instrument가 필요합니다.")
    if instrument != str(binding.target_symbol).strip():
        raise ValueError(
            f"parent context target_symbol과 market instrument가 다릅니다: "
            f"{binding.target_symbol!r} != {instrument!r}"
        )

    raw_times = market.get("time")
    if raw_times is None or isinstance(raw_times, (str, bytes)):
        raise ValueError("parent context backtest에는 market time 배열이 필요합니다.")
    target_times = tuple(str(item) for item in raw_times)
    if not target_times:
        raise ValueError("parent context backtest market time 배열이 비어 있습니다.")
    try:
        binding.validate_target_times(target_times)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"parent context backtest exact binding 오류: {exc}") from exc

    return binding, {
        "supplied": True,
        "policy": BACKTEST_CONTEXT_POLICY,
        "binding_policy": BINDING_POLICY,
        "target_symbol": binding.target_symbol,
        "frame_hash": binding.frame_hash,
        "registry_hash": binding.registry_hash,
        "binding_hash": binding.binding_hash,
        "bar_count": len(binding.target_times),
        "feature_ids": tuple(sorted(binding.feature_types)),
    }
