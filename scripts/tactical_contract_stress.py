"""Deterministic tactical stress harness.

This harness uses explicit synthetic fixtures only for engine stress. It is not a
production data fallback and never participates in a real Tactical Unit run.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import math

from core.multi_symbol import (
    CommonPolicySpec,
    InstrumentTask,
    MultiSymbolAnalysisEngine,
    RegimeContext,
    TacticalUnitSpec,
)
from core.tactical_chart_document import build_tactical_chart_document
from core.tactical_cohort import CohortMember, CohortSnapshot


DSL = '''strategy "TacticalStress" {
    timeframe = "5m"
    up = close > open
    down = close < open
    long_entry = up
    long_exit = down
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(symbol: str, *, bars: int, phase: float = 0.0) -> dict:
    start = datetime(2026, 8, 25, 8, 0)
    times = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    price = 100.0 + phase
    for i in range(bars):
        t = start + timedelta(minutes=5 * i)
        wave = math.sin((i + phase) / 4.0) * 0.8
        drift = 0.04 * i
        close = 100.0 + phase + drift + wave
        open_ = price
        high = max(open_, close) + 0.3
        low = min(open_, close) - 0.3
        times.append(t.strftime("%Y%m%d%H%M%S"))
        opens.append(open_)
        highs.append(high)
        lows.append(low)
        closes.append(close)
        volumes.append(1000.0 + i * 7 + phase)
        price = close
    return {
        "time": times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "_meta": {"source": "stress_fixture", "timeframe": "5m", "instrument": symbol},
    }


def run(full: bool) -> None:
    symbol_count = 64 if full else 16
    bars = 96 if full else 48
    symbols = tuple(f"S{i:03d}" for i in range(symbol_count))
    tasks = [
        InstrumentTask(symbol, DSL, market(symbol, bars=bars, phase=i * 0.07))
        for i, symbol in enumerate(symbols)
    ]
    unit = TacticalUnitSpec(
        unit_id="STRESS_UNIT",
        unit_type="STRESS_FIXTURE",
        symbols=symbols,
        rank_by="strategy_return_pct",
        metadata={"fixture_only": True},
    )
    regime = RegimeContext("STRESS_REGIME", active=True, eligible_units=("STRESS_UNIT",))
    policy = CommonPolicySpec(entry_start_time=80500, max_entries_per_day=4)

    one = MultiSymbolAnalysisEngine.run(
        regime=regime,
        unit=unit,
        tasks=tasks,
        common_policy=policy,
        max_workers=1,
    )
    many = MultiSymbolAnalysisEngine.run(
        regime=regime,
        unit=unit,
        tasks=tasks,
        common_policy=policy,
        max_workers=min(8, symbol_count),
    )
    if one["scenario_hash"] != many["scenario_hash"]:
        raise AssertionError("worker count changed scenario_hash")
    if one["run_hash"] != many["run_hash"]:
        raise AssertionError("worker count changed run_hash")
    if [row["symbol"] for row in many["results"]] != list(symbols):
        raise AssertionError("parallel execution changed symbol result order")

    markets = {task.symbol: task.market for task in tasks}
    document = build_tactical_chart_document(many, markets, comparison_limit=4)
    if document["version"] != "chart-document/v1" or len(document["series"]) != 4:
        raise AssertionError("tactical chart contract stress failed")

    try:
        CohortSnapshot.create(
            unit_id="LEAK",
            as_of="20260825090500",
            members=(
                CohortMember(
                    "000001",
                    "20260825090500",
                    {"future_mfe": 12.0},
                ),
            ),
            source="stress_fixture",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("future outcome leaked into point-in-time cohort")

    broken = list(tasks)
    bad = dict(market("BROKEN", bars=bars, phase=1.0))
    bad["high"] = list(bad["high"])
    bad["high"][3] = bad["low"][3] - 1.0
    broken[-1] = InstrumentTask(symbols[-1], DSL, bad)
    try:
        MultiSymbolAnalysisEngine.run(
            regime=regime,
            unit=unit,
            tasks=broken,
            common_policy=policy,
            max_workers=min(8, symbol_count),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid symbol data did not fail the whole scenario")

    print(
        f"[PASS] Tactical contract stress completed: "
        f"symbols={symbol_count}, bars={bars}, workers={min(8, symbol_count)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    run(args.full)


if __name__ == "__main__":
    main()
