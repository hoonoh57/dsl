"""Build frozen micro-research BattleCases from explicit market authority.

The generic provider deliberately does not discover a production universe or
invent a fallback source. Callers must supply exact symbol/date requests and a
concrete SessionMarketProvider. The Korean regular-session specialization adds
an explicit source/session contract without guessing a production table.
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


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _clock(value: Any, label: str) -> str:
    digits = _digits(value)
    if len(digits) < 6:
        raise ValueError(f"{label}은 HHMMSS 형식이어야 합니다.")
    clock = digits[:6]
    hh, mm, ss = int(clock[:2]), int(clock[2:4]), int(clock[4:6])
    if hh > 23 or mm > 59 or ss > 59:
        raise ValueError(f"{label}이 올바른 시각이 아닙니다: {value!r}")
    return clock


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
        day = _digits(self.session_date)
        if len(day) < 8:
            raise ValueError("BattleCaseRequest session_date는 YYYYMMDD 형식이어야 합니다.")
        cutoff = _digits(self.knowledge_cutoff)
        if len(cutoff) < 14:
            raise ValueError("BattleCaseRequest knowledge_cutoff은 YYYYMMDDHHMMSS여야 합니다.")
        if cutoff[:8] != day[:8]:
            raise ValueError("knowledge_cutoff 거래일이 session_date와 다릅니다.")
        if self.context is not None:
            self.context.validate_for(cutoff[:14])


@dataclass(frozen=True)
class KoreanRegularSessionContract:
    """Explicit KRX regular-session authority for one BattleCase batch.

    ``authority_id`` names the deployment/source authority selected by the
    caller. The engine never derives it from a guessed database/table name.
    Warm-up bars may come from prior dates, but every supplied bar must belong
    to the declared regular-session clock window.
    """

    authority_id: str
    session_open: str = "090000"
    session_close: str = "153000"
    minimum_session_bars: int = 2

    def validate(self) -> None:
        if not str(self.authority_id or "").strip():
            raise ValueError("Korean regular-session source authority_id가 필요합니다.")
        start = _clock(self.session_open, "session_open")
        end = _clock(self.session_close, "session_close")
        if start >= end:
            raise ValueError("Korean regular-session open은 close보다 빨라야 합니다.")
        if int(self.minimum_session_bars) < 1:
            raise ValueError("minimum_session_bars는 1 이상이어야 합니다.")

    @property
    def contract_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": "korean_regular_session/v1",
                "authority_id": str(self.authority_id).strip(),
                "session_open": _clock(self.session_open, "session_open"),
                "session_close": _clock(self.session_close, "session_close"),
                "minimum_session_bars": int(self.minimum_session_bars),
            }
        )


@dataclass(frozen=True)
class FrozenBattleCaseBatch:
    cases: tuple[BattleCase, ...]
    timeframe: str
    required_bars: int
    provider_name: str
    batch_hash: str
    source_authority: str = ""
    session_policy_hash: str = ""


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
        regular_session_contract: Optional[KoreanRegularSessionContract] = None,
    ):
        self.market_provider = market_provider
        self.timeframe = str(timeframe or "").strip()
        self.required_bars = int(required_bars)
        self.end_time = str(end_time or "").strip()
        self.settings = dict(settings or {})
        self.regular_session_contract = regular_session_contract
        if not self.timeframe:
            raise ValueError("BattleCaseProvider timeframe이 필요합니다.")
        if self.required_bars < 2:
            raise ValueError("BattleCaseProvider required_bars는 2 이상이어야 합니다.")
        if not self.end_time:
            raise ValueError("BattleCaseProvider end_time이 필요합니다.")
        if self.regular_session_contract is not None:
            self.regular_session_contract.validate()
            end_clock = _clock(self.end_time, "BattleCaseProvider end_time")
            session_open = _clock(self.regular_session_contract.session_open, "session_open")
            session_close = _clock(self.regular_session_contract.session_close, "session_close")
            if end_clock < session_open or end_clock > session_close:
                raise ValueError(
                    "BattleCaseProvider end_time은 Korean regular-session 범위 안이어야 합니다."
                )

    def _validate_regular_session_market(
        self,
        *,
        request: BattleCaseRequest,
        market: Mapping[str, Any],
    ) -> None:
        contract = self.regular_session_contract
        if contract is None:
            return

        meta = market.get("_meta") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("Korean regular-session market _meta가 Mapping이어야 합니다.")
        source = str(meta.get("source") or "").strip()
        instrument = str(meta.get("instrument") or "").strip()
        timeframe = str(meta.get("timeframe") or "").strip()
        if not source:
            raise ValueError("Korean regular-session market source metadata가 필요합니다.")
        if instrument != str(request.symbol).strip():
            raise ValueError(
                f"Korean regular-session market instrument 불일치: {instrument!r} != {request.symbol!r}"
            )
        if timeframe != self.timeframe:
            raise ValueError(
                f"Korean regular-session market timeframe 불일치: {timeframe!r} != {self.timeframe!r}"
            )

        raw_times = market.get("time")
        if not isinstance(raw_times, Sequence) or isinstance(raw_times, (str, bytes)):
            raise ValueError("Korean regular-session market time 배열이 필요합니다.")
        if len(raw_times) < self.required_bars:
            raise ValueError(
                f"Korean regular-session warm-up/history coverage 부족: "
                f"bars={len(raw_times)}, required={self.required_bars}"
            )

        day = _digits(request.session_date)[:8]
        session_open = _clock(contract.session_open, "session_open")
        session_close = _clock(contract.session_close, "session_close")
        requested_end = _clock(self.end_time, "BattleCaseProvider end_time")
        current_session_bars = 0
        for raw in raw_times:
            stamp = _digits(raw)
            if len(stamp) < 14:
                raise ValueError(
                    f"Korean regular-session bar timestamp는 YYYYMMDDHHMMSS여야 합니다: {raw!r}"
                )
            stamp = stamp[:14]
            clock = stamp[8:14]
            if clock < session_open or clock > session_close:
                raise ValueError(
                    f"Korean regular-session 범위 밖 bar가 있습니다: {stamp}"
                )
            if stamp[:8] == day:
                if clock > requested_end:
                    raise ValueError(
                        f"BattleCase requested end_time 이후 bar가 있습니다: {stamp} > {day}{requested_end}"
                    )
                current_session_bars += 1

        if current_session_bars < int(contract.minimum_session_bars):
            raise ValueError(
                f"Korean regular-session 당일 bar coverage 부족: "
                f"bars={current_session_bars}, required={contract.minimum_session_bars}"
            )

    def load(self, requests: Sequence[BattleCaseRequest]) -> FrozenBattleCaseBatch:
        frozen = tuple(requests)
        if not frozen:
            raise ValueError("BattleCaseRequest가 비어 있습니다.")
        if len({item.case_id for item in frozen}) != len(frozen):
            raise ValueError("BattleCaseRequest case_id에 중복이 있습니다.")
        cases = []
        for request in frozen:
            request.validate()
            day = _digits(request.session_date)[:8]
            market = self.market_provider.load_session(
                symbol=request.symbol,
                session_date=day,
                timeframe=self.timeframe,
                required_bars=self.required_bars,
                end_time=self.end_time,
            )
            self._validate_regular_session_market(request=request, market=market)
            context = request.context or BattlefieldContext.neutral(request.knowledge_cutoff)
            metadata = dict(request.metadata)
            if self.regular_session_contract is not None:
                metadata = {
                    **metadata,
                    "battlecase_source_authority": str(
                        self.regular_session_contract.authority_id
                    ).strip(),
                    "battlecase_session": "KRX_REGULAR",
                    "battlecase_session_policy_hash": self.regular_session_contract.contract_hash,
                }
            case = BattleCase(
                case_id=request.case_id,
                symbol=request.symbol,
                session_date=day,
                market=market,
                settings=dict(self.settings),
                knowledge_cutoff=request.knowledge_cutoff,
                battlefield_context=context,
                metadata=metadata,
            )
            case.validate()
            cases.append(case)

        contract = self.regular_session_contract
        contract_identity = None
        if contract is not None:
            contract_identity = {
                "authority_id": str(contract.authority_id).strip(),
                "contract_hash": contract.contract_hash,
            }
        identity = {
            "case_ids": [item.case_id for item in cases],
            "case_hashes": [item.case_hash for item in cases],
            "timeframe": self.timeframe,
            "required_bars": self.required_bars,
            "end_time": self.end_time,
            "settings": self.settings,
            "provider": type(self.market_provider).__name__,
            "regular_session_contract": contract_identity,
        }
        return FrozenBattleCaseBatch(
            cases=tuple(cases),
            timeframe=self.timeframe,
            required_bars=self.required_bars,
            provider_name=type(self.market_provider).__name__,
            batch_hash=_stable_hash(identity),
            source_authority=(str(contract.authority_id).strip() if contract is not None else ""),
            session_policy_hash=(contract.contract_hash if contract is not None else ""),
        )


class KoreanRegularSessionBattleCaseProvider(ExplicitBattleCaseProvider):
    """Strict E1 provider for explicitly-authorized KRX regular-session battles."""

    def __init__(
        self,
        market_provider: SessionMarketProvider,
        *,
        source_authority: str,
        timeframe: str,
        required_bars: int,
        end_time: str = "153000",
        session_open: str = "090000",
        session_close: str = "153000",
        minimum_session_bars: int = 2,
        settings: Optional[Mapping[str, Any]] = None,
    ):
        contract = KoreanRegularSessionContract(
            authority_id=source_authority,
            session_open=session_open,
            session_close=session_close,
            minimum_session_bars=minimum_session_bars,
        )
        super().__init__(
            market_provider,
            timeframe=timeframe,
            required_bars=required_bars,
            end_time=end_time,
            settings=settings,
            regular_session_contract=contract,
        )
