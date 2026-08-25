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

    bars = _bars(markets[focus])
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
    if capture_as_of:
        capture_time = _chart_time(capture_as_of)
        geometries.append(
            {
                "kind": "vertical-region",
                "fromTime": capture_time,
                "toTime": capture_time,
                "label": "capture cutoff",
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
            "cohortSnapshotHash": (
                (result.get("unit") or {}).get("metadata", {}).get("cohort_snapshot_hash")
            ),
        },
    }
