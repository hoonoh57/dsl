"""Deterministic user-indicator calculations kept outside the built-in TA namespace."""
from __future__ import annotations

import numpy as np

from core.indicators import CoreTALib


NORMALIZED_MACD_COMPONENTS = frozenset({"macd", "signal", "hist", "hist_abs_pct"})


def normalized_macd_component(
    series,
    component: str,
    short: int = 12,
    long: int = 26,
    signal: int = 9,
    method: str = "exponential",
):
    """Return one observable component of the normalized-MACD user indicator.

    The DSL currently returns one numeric series per function call, so the same
    registered indicator is called with a component selector until tuple outputs
    are supported.  ``hist_abs_pct`` is the absolute MACD histogram normalized
    by the input price series in percent units.
    """
    source = np.asarray(series, dtype=np.float64)
    component_name = str(component).strip().lower()
    if component_name not in NORMALIZED_MACD_COMPONENTS:
        allowed = ", ".join(sorted(NORMALIZED_MACD_COMPONENTS))
        raise ValueError(f"user.macd_normalized component는 다음 중 하나여야 합니다: {allowed}")

    macd_line = CoreTALib.macd(source, int(short), int(long), method)
    signal_line = CoreTALib.ema(macd_line, int(signal))
    histogram = macd_line - signal_line

    if component_name == "macd":
        return macd_line
    if component_name == "signal":
        return signal_line
    if component_name == "hist":
        return histogram

    denominator = np.abs(source)
    return np.divide(
        np.abs(histogram) * 100.0,
        denominator,
        out=np.full_like(histogram, np.nan),
        where=denominator != 0,
    )
