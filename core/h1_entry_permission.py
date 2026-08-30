from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from core.range_detector_equipment import RangeDetectorConfig, RangeDetectorEquipment


@dataclass(frozen=True)
class H1EntryPermissionResult:
    trade_permitted: np.ndarray
    reason_code: np.ndarray
    source: str
    detector_version: str


class H1EntryPermissionEquipment:
    """Minimal H1 permission adapter using only the selected ADX range guard.

    This object owns no DSL or broker semantics.  It converts the selected
    RangeDetectorEquipment ADX candidate into the boolean series already
    accepted by BacktestEngine.entry_gate.
    """

    SOURCE = "range_detector.adx"
    DETECTOR_VERSION = "h1_adx_gate/v1"

    @classmethod
    def evaluate(
        cls,
        market: Mapping[str, object],
        config: RangeDetectorConfig | None = None,
    ) -> H1EntryPermissionResult:
        result = RangeDetectorEquipment.evaluate(market, config)
        gate = np.asarray(result.permits["adx"], dtype=bool).copy()
        reasons = np.where(gate, "", "RANGE_ADX_BLOCKED")
        reasons = np.asarray(reasons, dtype="<U32")
        gate.setflags(write=False)
        reasons.setflags(write=False)
        return H1EntryPermissionResult(
            trade_permitted=gate,
            reason_code=reasons,
            source=cls.SOURCE,
            detector_version=cls.DETECTOR_VERSION,
        )
