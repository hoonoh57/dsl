from __future__ import annotations

from typing import Dict

from core.backtest import synthetic_market


def strategy_validation_market(bars_count: int = 200) -> Dict:
    """Return deterministic validation data without claiming a market timeframe.

    Strategy authoring validation must exercise the authoritative DSL runtime and
    broker path, but the built-in synthetic fixture is not authentic 1d/5m/etc.
    Removing only the timeframe claim keeps real backtest timeframe checks strict
    while allowing the same fixture to validate DSLs from different timeframes.
    """
    market = synthetic_market(bars_count)
    meta = dict(market.get("_meta") or {})
    meta.pop("timeframe", None)
    meta["source"] = "strategy_validation_fixture"
    market["_meta"] = meta
    return market
