"""Build frozen micro-research BattleCases from an explicit authoritative market provider.

This module deliberately does not discover a production universe or invent a
fallback source.  Callers must supply exact symbol/date requests and a concrete
SessionMarketProvider.  Universe discovery remains a separate authority layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Optional, Sequence

from core.battlefield_context import BattlefieldContext
from core.tactical_discovery import BattleCase
from core.tactical_market import SessionMarketProvider


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BattleCaseRequest:
    case_id: str
    symbol: str
    session_date: str
    knowledge_cutoff: str
    context: Optional[BattlefieldContext] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.case_id.strip() or not self.symbol.strip():
            raise ValueError("BattleCaseRequest case_id/symbol이 필요합니다.")
        day = "".join(ch for ch in str(self.session_date) if ch.isdigit())
        if len(day) < 8:
            raise ValueError("BattleCaseRequest session_date는 YYYYMMDD 형식이어야 합니다.")
        cutoff = "".join(ch for ch in str(self.knowledge_cutoff) if ch.isdigit())
        if len(cutoff) < 14:
            raise ValueError("BattleCaseRequest knowledge_cutoff은 YYYYMMDDHHMMSS여야 합니다.")
        if cutoff[:8] != day[:8]:
            raise ValueError("knowledge_cutoff 거래일이 session_date와 다릅니다.")
        if self.context is not None:
            self.context.validate_for(cutoff[:14])


@dataclass(frozen=True)
class FrozenBattleCaseBatch:
    cases: tuple[BattleCase, ...]
    timeframe: str
    required_bars: int
    provider_name: str
    batch_hash: str


class ExplicitBattleCaseProvider:
    """Load exact symbol/date battles through one configured market provider."""

    def __init__(
        self,
        market_provider: SessionMarketProvider,
        *,
        timeframe: str,
        required_bars: int,
        end_time: str = "153000",
        settings: Optional[Mapping[str, Any]] = None,
    ):
        self.market_provider = market_provider
        self.timeframe = str(timeframe or "").strip()
        self.required_bars = int(required_bars)
        self.end_time = str(end_time or "").strip()
        self.settings = dict(settings or {})
        if not self.timeframe:
            raise ValueError("BattleCaseProvider timeframe이 필요합니다.")
        if self.required_bars < 2:
            raise ValueError("BattleCaseProvider required_bars는 2 이상이어야 합니다.")
        if not self.end_time:
            raise ValueError("BattleCaseProvider end_time이 필요합니다.")

    def load(self, requests: Sequence[BattleCaseRequest]) -> FrozenBattleCaseBatch:
        frozen = tuple(requests)
        if not frozen:
            raise ValueError("BattleCaseRequest가 비어 있습니다.")
        if len({item.case_id for item in frozen}) != len(frozen):
            raise ValueError("BattleCaseRequest case_id에 중복이 있습니다.")
        cases = []
        for request in frozen:
            request.validate()
            day = "".join(ch for ch in str(request.session_date) if ch.isdigit())[:8]
            market = self.market_provider.load_session(
                symbol=request.symbol,
                session_date=day,
                timeframe=self.timeframe,
                required_bars=self.required_bars,
                end_time=self.end_time,
            )
            context = request.context or BattlefieldContext.neutral(request.knowledge_cutoff)
            case = BattleCase(
                case_id=request.case_id,
                symbol=request.symbol,
                session_date=day,
                market=market,
                settings=dict(self.settings),
                knowledge_cutoff=request.knowledge_cutoff,
                battlefield_context=context,
                metadata=dict(request.metadata),
            )
            case.validate()
            cases.append(case)
        identity = {
            "case_ids": [item.case_id for item in cases],
            "case_hashes": [item.case_hash for item in cases],
            "timeframe": self.timeframe,
            "required_bars": self.required_bars,
            "end_time": self.end_time,
            "settings": self.settings,
            "provider": type(self.market_provider).__name__,
        }
        return FrozenBattleCaseBatch(
            cases=tuple(cases),
            timeframe=self.timeframe,
            required_bars=self.required_bars,
            provider_name=type(self.market_provider).__name__,
            batch_hash=_stable_hash(identity),
        )
