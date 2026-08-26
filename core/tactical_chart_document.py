"""Project multi-symbol tactical evidence into the shared Chart Document v1."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _chart_time(value: Any):
    digits = _digits(value)
    if len(digits) >= 14:
        dt = datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return str(value)


def _trading_date(value: Any) -> str:
    digits = _digits(value)
    if len(digits) < 8:
        raise ValueError(f"trading date를 해석할 수 없습니다: {value!r}")
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"


def _bars(market: Mapping[str, Any]) -> list[dict]:
    required = ("time", "open", "high", "low", "close", "volume")
    lengths = {key: len(market.get(key, [])) for key in required}
    if len(set(lengths.values())) != 1 or next(iter(lengths.values()), 0) < 2:
        raise ValueError(f"chart market 길이가 올바르지 않습니다: {lengths}")
    output = []
    for i, source_time in enumerate(market["time"]):
        output.append(
            {
                "tradingDate": _trading_date(source_time),
                "time": _chart_time(source_time),
                "sourceTime": str(source_time),
                "open": float(market["open"][i]),
                "high": float(market["high"][i]),
                "low": float(market["low"][i]),
                "close": float(market["close"][i]),
                "volume": float(market["volume"][i]),
            }
        )
    return output


def _normalized_close_series(market: Mapping[str, Any]) -> list[dict]:
    closes = [float(value) for value in market.get("close", [])]
    times = list(market.get("time", []))
    if len(closes) != len(times) or not closes:
        return []
    base = closes[0]
    if base <= 0:
        raise ValueError("relative chart normalization에는 양수 첫 close가 필요합니다.")
    return [
        {"time": _chart_time(t), "value": (close / base - 1.0) * 100.0}
        for t, close in zip(times, closes)
    ]


def _selected_symbols(result: Mapping[str, Any], *, limit: int) -> list[str]:
    ranking = list(result.get("ranking") or [])
    ordered = [str(item.get("symbol") or "") for item in ranking if item.get("symbol")]
    if not ordered:
        ordered = [
            str(item.get("symbol") or "")
            for item in result.get("results", [])
            if item.get("symbol")
        ]
    seen = []
    for symbol in ordered:
        if symbol and symbol not in seen:
            seen.append(symbol)
        if len(seen) >= max(1, int(limit)):
            break
    return seen


def _capture_region_times(market: Mapping[str, Any], capture_as_of: str) -> tuple[Any, Any]:
    """Return a non-zero actual-bar interval that begins at/after the cutoff.

    LightweightChartSurface renders vertical regions with fillRect(width), so a
    same-time from/to pair is invisible. We preserve the exact cutoff in meta,
    while geometry uses two strictly increasing real bar timestamps from the
    focus market. If that evidence cannot be proven, fail closed.
    """
    capture_digits = _digits(capture_as_of)
    if len(capture_digits) < 14:
        raise ValueError(f"capture cutoff은 YYYYMMDDHHMMSS여야 합니다: {capture_as_of!r}")
    capture_key = capture_digits[:14]
    timeline: list[tuple[str, Any]] = []
    for source_time in market.get("time", []):
        digits = _digits(source_time)
        if len(digits) < 14:
            raise ValueError(f"capture chart bar timestamp가 14자리가 아닙니다: {source_time!r}")
        timeline.append((digits[:14], source_time))
    if len(timeline) < 2:
        raise ValueError("capture cutoff evidence에는 실제 bar가 2개 이상 필요합니다.")
    if any(timeline[i][0] >= timeline[i + 1][0] for i in range(len(timeline) - 1)):
        raise ValueError("capture cutoff evidence bar 시간이 엄격 오름차순이 아닙니다.")
    start_index = next(
        (index for index, (stamp, _) in enumerate(timeline) if stamp >= capture_key),
        None,
    )
    if start_index is None or start_index + 1 >= len(timeline):
        raise ValueError(
            "capture cutoff 이후의 비영(非零) 실제 bar 구간을 만들 수 없습니다."
        )
    start_stamp, start_source = timeline[start_index]
    end_stamp, end_source = timeline[start_index + 1]
    if end_stamp <= start_stamp:
        raise ValueError("capture cutoff geometry가 0폭 또는 역방향입니다.")
    return _chart_time(start_source), _chart_time(end_source)


def build_tactical_chart_document(
    result: Mapping[str, Any],
    markets: Mapping[str, Mapping[str, Any]],
    *,
    focus_symbol: str = "",
    comparison_limit: int = 4,
) -> dict:
    """Build one audit document without using post-outcome labels for selection."""
    comparison = _selected_symbols(result, limit=comparison_limit)
    focus = str(focus_symbol or "").strip() or (comparison[0] if comparison else "")
    if not focus or focus not in markets:
        raise ValueError("tactical chart focus symbol의 시장 데이터가 없습니다.")
    if focus not in comparison:
        comparison = [focus] + [item for item in comparison if item != focus]
        comparison = comparison[: max(1, int(comparison_limit))]

    focus_market = markets[focus]
    bars = _bars(focus_market)
    panes = {"relative": {"height": 150}}
    series = []
    for symbol in comparison:
        market = markets.get(symbol)
        if not market:
            continue
        series.append(
            {
                "id": f"relative:{symbol}",
                "kind": "line",
                "pane": "relative",
                "options": {"inspectionLabel": f"{symbol} normalized %", "lineWidth": 2},
                "data": _normalized_close_series(market),
            }
        )

    result_by_symbol = {
        str(item.get("symbol")): item for item in result.get("results", [])
    }
    focus_row = result_by_symbol.get(focus, {})
    backtest = focus_row.get("backtest") or {}
    markers = []
    for marker in backtest.get("markers", []):
        if marker.get("time") is None:
            continue
        markers.append(
            {
                key: value
                for key, value in marker.items()
                if key in {"time", "position", "shape", "color", "text", "size"}
            }
        )

    capture_as_of = str((result.get("unit") or {}).get("metadata", {}).get("capture_as_of") or "")
    geometries = []
    capture_region = None
    if capture_as_of:
        from_time, to_time = _capture_region_times(focus_market, capture_as_of)
        capture_region = {"fromTime": from_time, "toTime": to_time}
        geometries.append(
            {
                "kind": "vertical-region",
                "fromTime": from_time,
                "toTime": to_time,
                "label": "capture cutoff interval",
            }
        )
    for window in (result.get("regime") or {}).get("windows", []):
        geometries.append(
            {
                "kind": "vertical-region",
                "fromTime": _chart_time(window["start"]),
                "toTime": _chart_time(window["end"]),
                "label": str(window.get("label") or "opportunity"),
            }
        )

    return {
        "version": "chart-document/v1",
        "bars": bars,
        "panes": panes,
        "series": series,
        "markers": markers,
        "references": [],
        "geometries": geometries,
        "meta": {
            "scenarioHash": result.get("scenario_hash"),
            "runHash": result.get("run_hash"),
            "focusSymbol": focus,
            "comparisonSymbols": comparison,
            "selectionBasis": "point_in_time_rank_only",
            "outcomeSelectionUsed": False,
            "captureCutoff": capture_as_of or None,
            "captureRegion": capture_region,
            "cohortSnapshotHash": (
                (result.get("unit") or {}).get("metadata", {}).get("cohort_snapshot_hash")
            ),
        },
    }
