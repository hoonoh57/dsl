"""Exact-time parent-context adapter for BacktestEngine.

CTXBT1 keeps provider calculation outside Backtest.  It only converts an
already-precomputed DEPLOYMENT ParentContextFrame plus its matching PCTX1
registry into the immutable DSLContextSeriesBinding consumed by DSLRuntime.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.dsl_context import BINDING_POLICY, DSLContextSeriesBinding
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import ParentFeatureRegistry


BACKTEST_CONTEXT_POLICY = "EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL"


def prepare_backtest_parent_context(
    *,
    market: Mapping[str, Any],
    frame: ParentContextFrame | None,
    registry: ParentFeatureRegistry | None,
) -> tuple[DSLContextSeriesBinding | None, dict[str, Any]]:
    """Build one exact immutable DSL context binding for a backtest.

    Supplying only one of frame/registry is invalid.  When supplied, the market
    must identify the same target instrument and every market bar timestamp
    must exist as an exact point in the DEPLOYMENT frame.  No nearest lookup,
    carry-forward, provider call or default value is performed here.
    """

    if (frame is None) != (registry is None):
        raise ValueError("parent context backtest에는 frame과 registry를 함께 제공해야 합니다.")
    if frame is None:
        return None, {
            "supplied": False,
            "policy": BACKTEST_CONTEXT_POLICY,
            "binding_policy": BINDING_POLICY,
        }

    if not isinstance(frame, ParentContextFrame):
        raise ValueError("parent_context_frame은 ParentContextFrame이어야 합니다.")
    if not isinstance(registry, ParentFeatureRegistry):
        raise ValueError("parent_feature_registry는 ParentFeatureRegistry여야 합니다.")
    frame.validate()
    registry.validate()

    meta = market.get("_meta") or {}
    if not isinstance(meta, Mapping):
        raise ValueError("parent context backtest market _meta는 Mapping이어야 합니다.")
    instrument = str(meta.get("instrument") or "").strip()
    if not instrument:
        raise ValueError("parent context backtest에는 market _meta.instrument가 필요합니다.")
    if instrument != str(frame.target_symbol).strip():
        raise ValueError(
            f"parent context target_symbol과 market instrument가 다릅니다: "
            f"{frame.target_symbol!r} != {instrument!r}"
        )

    raw_times = market.get("time")
    if not isinstance(raw_times, Sequence) or isinstance(raw_times, (str, bytes)):
        raise ValueError("parent context backtest에는 market time 배열이 필요합니다.")
    target_times = tuple(str(item) for item in raw_times)
    if not target_times:
        raise ValueError("parent context backtest market time 배열이 비어 있습니다.")

    try:
        binding = DSLContextSeriesBinding.from_frame(
            frame=frame,
            registry=registry,
            target_times=target_times,
        )
    except (KeyError, TypeError, ValueError) as exc:
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
