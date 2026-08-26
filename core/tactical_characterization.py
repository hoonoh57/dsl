"""Causal failure/opportunity characterization for micro-tactic engagements.

This module is descriptive evidence only.  It joins an actual tactic entry's
signal-time TacticalObservation to later realized outcome labels while keeping
those two domains physically separate.  It never mutates DSL, Runtime, Backtest
or Broker semantics and it does not produce a hidden universal score.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from statistics import mean
from typing import Any, Mapping, Sequence

from core.tactical_discovery import BattleCase
from core.tactical_failure import FailureAnalysisPolicy, TacticalFailureAnalyzer
from core.tactical_observation import JmaLocalObservationBuilder


SCHEMA_VERSION = "tactical_characterization/v1"


def _safe_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _safe_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _finite(name: str, value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"characterization 값이 유한하지 않습니다: {name}={value!r}")
    return number


def _timestamp(value: Any) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) < 14:
        raise ValueError(f"characterization timestamp는 YYYYMMDDHHMMSS여야 합니다: {value!r}")
    return digits[:14]


@dataclass(frozen=True)
class CharacterizationPolicy:
    """Compact descriptive axes for the first E4 tranche.

    The feature list is intentionally small.  It covers time position, trend /
    range geometry, volatility, liquidity proxy, overextension and primitive
    price structure without feeding the full raw observation into a learner.
    """

    feature_names: tuple[str, ...] = (
        "minutes_from_open",
        "jma_spread_atr",
        "sma60_slope_pct",
        "price_to_sma60_atr",
        "atr_pct",
        "volume_ratio",
        "higher_high_ratio",
        "higher_low_ratio",
    )
    quantile_bins: int = 3
    minimum_bin_support: int = 1

    def validate(self) -> None:
        if not self.feature_names:
            raise ValueError("characterization feature_names가 비어 있습니다.")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("characterization feature_names에 중복이 있습니다.")
        if self.quantile_bins < 2 or self.quantile_bins > 5:
            raise ValueError("quantile_bins는 2~5 범위여야 합니다.")
        if self.minimum_bin_support < 1:
            raise ValueError("minimum_bin_support는 1 이상이어야 합니다.")


class TacticalFailureOpportunityCharacterizer:
    """Join causal entry observations to later trade outcomes and summarize them."""

    @staticmethod
    def _trade_outcome_tags(trade: Mapping[str, Any], policy: FailureAnalysisPolicy) -> tuple[str, ...]:
        ret = _finite("return_pct", trade.get("return_pct", 0.0))
        mae = _finite("mae_pct", trade.get("mae_pct", 0.0))
        mfe = _finite("mfe_pct", trade.get("mfe_pct", 0.0))
        giveback = mfe - ret
        tags: list[str] = []
        if ret > 0.0:
            tags.append("PROFITABLE")
        if ret <= policy.loss_return_pct:
            tags.append("LOSS")
        if ret <= policy.severe_loss_return_pct:
            tags.append("SEVERE_LOSS")
        if mae <= policy.adverse_mae_threshold_pct:
            tags.append("ADVERSE_EXCURSION")
        if mfe > 0.0 and giveback >= policy.giveback_threshold_pct:
            tags.append("MFE_GIVEBACK")
        return tuple(tags)

    @staticmethod
    def _case_maps(profile: Mapping[str, Any], cases: Sequence[BattleCase]) -> tuple[dict[str, Mapping[str, Any]], dict[str, BattleCase]]:
        if str(profile.get("schema") or "") != "tactical_discovery/v1":
            raise ValueError("characterizer profile은 tactical_discovery/v1이어야 합니다.")
        rows = list(profile.get("results") or [])
        if not rows:
            raise ValueError("characterizer profile results가 비어 있습니다.")
        frozen_cases = tuple(cases)
        if not frozen_cases:
            raise ValueError("characterizer BattleCases가 비어 있습니다.")
        row_map: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            case_id = str(row.get("case_id") or "").strip()
            if not case_id or case_id in row_map:
                raise ValueError("characterizer profile case_id가 비어 있거나 중복되었습니다.")
            row_map[case_id] = row
        case_map: dict[str, BattleCase] = {}
        for case in frozen_cases:
            case.validate()
            if case.case_id in case_map:
                raise ValueError("characterizer BattleCase case_id가 중복되었습니다.")
            case_map[case.case_id] = case
        if set(row_map) != set(case_map):
            raise ValueError("characterizer profile과 BattleCase case_id 집합이 다릅니다.")
        for case_id, row in row_map.items():
            if str(row.get("case_hash") or "") != case_map[case_id].case_hash:
                raise ValueError(f"characterizer BattleCase identity가 profile과 다릅니다: {case_id}")
        return row_map, case_map

    @staticmethod
    def _quantile_cutpoints(values: Sequence[float], bins: int) -> tuple[float, ...]:
        ordered = sorted(float(value) for value in values)
        if not ordered:
            return ()
        cuts: list[float] = []
        n = len(ordered)
        for bucket in range(1, bins):
            position = (n - 1) * bucket / bins
            lower = int(math.floor(position))
            upper = int(math.ceil(position))
            if lower == upper:
                cut = ordered[lower]
            else:
                fraction = position - lower
                cut = ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction
            cuts.append(float(cut))
        return tuple(cuts)

    @staticmethod
    def _bin_label(value: float, cuts: Sequence[float]) -> str:
        index = 0
        while index < len(cuts) and value > cuts[index]:
            index += 1
        labels = ("LOW", "MID_LOW", "MID", "MID_HIGH", "HIGH")
        if len(cuts) == 2:
            return ("LOW", "MID", "HIGH")[index]
        if len(cuts) == 3:
            return ("LOW", "MID_LOW", "MID_HIGH", "HIGH")[index]
        if len(cuts) == 4:
            return labels[index]
        return f"BIN_{index + 1}"

    @classmethod
    def _feature_strata(cls, records: Sequence[Mapping[str, Any]], policy: CharacterizationPolicy) -> dict:
        output: dict[str, dict[str, Any]] = {}
        for feature in policy.feature_names:
            values = [_finite(feature, record["causal_features"][feature]) for record in records]
            cuts = cls._quantile_cutpoints(values, policy.quantile_bins)
            buckets: dict[str, list[Mapping[str, Any]]] = {}
            for record, value in zip(records, values):
                buckets.setdefault(cls._bin_label(value, cuts), []).append(record)
            rows = []
            for label, members in sorted(buckets.items()):
                if len(members) < policy.minimum_bin_support:
                    continue
                outcomes = [member["future_outcome"] for member in members]
                returns = [_finite("return_pct", outcome["return_pct"]) for outcome in outcomes]
                mfes = [_finite("mfe_pct", outcome["mfe_pct"]) for outcome in outcomes]
                maes = [_finite("mae_pct", outcome["mae_pct"]) for outcome in outcomes]
                givebacks = [_finite("giveback_pct", outcome["giveback_pct"]) for outcome in outcomes]
                tag_counts: dict[str, int] = {}
                for member in members:
                    for tag in member["outcome_tags"]:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                rows.append(
                    {
                        "bin": label,
                        "support": len(members),
                        "profitable_rate": sum(1 for value in returns if value > 0.0) / len(returns),
                        "average_return_pct": float(mean(returns)),
                        "average_mfe_pct": float(mean(mfes)),
                        "average_mae_pct": float(mean(maes)),
                        "average_giveback_pct": float(mean(givebacks)),
                        "outcome_tag_counts": dict(sorted(tag_counts.items())),
                    }
                )
            output[feature] = {"cutpoints": cuts, "bins": rows}
        return output

    @classmethod
    def characterize(
        cls,
        *,
        profile: Mapping[str, Any],
        cases: Sequence[BattleCase],
        family_id: str,
        generation_hash: str,
        resolution_mode: str = "JMA_TCR_5M",
        observation_builder: JmaLocalObservationBuilder | None = None,
        policy: CharacterizationPolicy = CharacterizationPolicy(),
        failure_policy: FailureAnalysisPolicy = FailureAnalysisPolicy(),
    ) -> dict:
        policy.validate()
        failure_policy.validate()
        family_id = str(family_id or "").strip()
        generation_hash = str(generation_hash or "").strip()
        resolution_mode = str(resolution_mode or "").strip()
        if not family_id or not generation_hash or not resolution_mode:
            raise ValueError("family_id/generation_hash/resolution_mode가 필요합니다.")
        row_map, case_map = cls._case_maps(profile, cases)
        builder = observation_builder or JmaLocalObservationBuilder()

        records: list[dict[str, Any]] = []
        no_trade_cases: list[str] = []
        for case_id in [str(row.get("case_id")) for row in profile["results"]]:
            row = row_map[case_id]
            case = case_map[case_id]
            backtest = dict(row.get("backtest") or {})
            trades = list(backtest.get("closed_trades") or [])
            if not trades:
                no_trade_cases.append(case_id)
                continue
            for trade in trades:
                signal_time = _timestamp(trade.get("signal_time"))
                entry_time = _timestamp(trade.get("entry_time"))
                if signal_time > entry_time:
                    raise ValueError(f"trade signal_time이 entry_time보다 미래입니다: {case_id}")
                observation = builder.build(
                    case=case,
                    timestamp=signal_time,
                    family_id=family_id,
                    generation_hash=generation_hash,
                    resolution_mode=resolution_mode,
                )
                missing = [name for name in policy.feature_names if name not in observation.features]
                if missing:
                    raise ValueError(f"characterization causal feature 누락: {missing}")
                causal_features = {
                    name: _finite(name, observation.features[name]) for name in policy.feature_names
                }
                ret = _finite("return_pct", trade.get("return_pct", 0.0))
                mfe = _finite("mfe_pct", trade.get("mfe_pct", 0.0))
                mae = _finite("mae_pct", trade.get("mae_pct", 0.0))
                outcome = {
                    "return_pct": ret,
                    "mfe_pct": mfe,
                    "mae_pct": mae,
                    "giveback_pct": mfe - ret,
                    "holding_bars": int(trade.get("holding_bars") or 0),
                    "exit_reason": str(trade.get("exit_reason") or ""),
                    "exit_time": _timestamp(trade.get("exit_time")),
                }
                outcome_tags = cls._trade_outcome_tags(trade, failure_policy)
                record_identity = {
                    "case_id": case_id,
                    "trade_id": int(trade.get("trade_id") or 0),
                    "observation_hash": observation.observation_hash,
                    "future_outcome": outcome,
                    "outcome_tags": outcome_tags,
                }
                records.append(
                    {
                        "case_id": case_id,
                        "case_hash": case.case_hash,
                        "symbol": case.symbol,
                        "trade_id": int(trade.get("trade_id") or 0),
                        "signal_time": signal_time,
                        "entry_time": entry_time,
                        "observation_hash": observation.observation_hash,
                        "market_prefix_hash": observation.market_prefix_hash,
                        "causal_features": causal_features,
                        "future_outcome": outcome,
                        "outcome_tags": outcome_tags,
                        "record_hash": _stable_hash(record_identity),
                    }
                )

        causal_identity = {
            "schema": SCHEMA_VERSION,
            "profile_case_set_hash": str(profile.get("case_set_hash") or ""),
            "family_id": family_id,
            "generation_hash": generation_hash,
            "resolution_mode": resolution_mode,
            "policy": policy.__dict__,
            "observations": [
                {
                    "case_id": record["case_id"],
                    "trade_id": record["trade_id"],
                    "signal_time": record["signal_time"],
                    "observation_hash": record["observation_hash"],
                    "market_prefix_hash": record["market_prefix_hash"],
                    "causal_features": record["causal_features"],
                }
                for record in records
            ],
        }
        labeled_identity = {
            "causal_dataset_hash": _stable_hash(causal_identity),
            "labels": [
                {
                    "case_id": record["case_id"],
                    "trade_id": record["trade_id"],
                    "future_outcome": record["future_outcome"],
                    "outcome_tags": record["outcome_tags"],
                }
                for record in records
            ],
        }
        failure_analysis = TacticalFailureAnalyzer.analyze(profile, failure_policy)
        strata = cls._feature_strata(records, policy) if records else {}
        return {
            "schema": SCHEMA_VERSION,
            "profile_run_hash": str(profile.get("run_hash") or ""),
            "case_set_hash": str(profile.get("case_set_hash") or ""),
            "family_id": family_id,
            "generation_hash": generation_hash,
            "resolution_mode": resolution_mode,
            "policy": {
                "feature_names": policy.feature_names,
                "quantile_bins": policy.quantile_bins,
                "minimum_bin_support": policy.minimum_bin_support,
                "failure_policy": dict(failure_policy.__dict__),
            },
            "records": records,
            "feature_strata": strata,
            "case_failure_analysis": failure_analysis,
            "summary": {
                "cases": len(case_map),
                "trade_records": len(records),
                "profitable_trades": sum(1 for record in records if "PROFITABLE" in record["outcome_tags"]),
                "losing_trades": sum(1 for record in records if "LOSS" in record["outcome_tags"]),
                "no_closed_trade_cases": len(no_trade_cases),
                "no_closed_trade_case_ids": tuple(no_trade_cases),
            },
            "causal_dataset_hash": _stable_hash(causal_identity),
            "labeled_dataset_hash": _stable_hash(labeled_identity),
            "characterization_hash": _stable_hash(
                {
                    "labeled_dataset_hash": _stable_hash(labeled_identity),
                    "feature_strata": strata,
                    "failure_hash": failure_analysis["failure_hash"],
                }
            ),
            "selection_policy": "DESCRIPTIVE_NO_HIDDEN_UNIVERSAL_SCORE",
            "causality_policy": "SIGNAL_TIME_FEATURES_FUTURE_OUTCOMES_LABEL_ONLY",
        }
