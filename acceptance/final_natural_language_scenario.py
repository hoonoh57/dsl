"""Representative final natural-language end-to-end acceptance scenario.

This module is an acceptance fixture, not product execution authority.  It uses
only already-versioned public project surfaces to prove that the final target can
be represented without adding a strategy-specific shortcut to any AXIS core.

The scenario deliberately keeps the ambiguous phrase "profit secured" as a
material human-approved assumption.  Historical EMA120 breakout/reference
search is represented as already-precomputed AXIS 2 point-in-time evidence;
AXIS 1 receives only the selected instrument and an exact read-only reference
Histogram context series.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from typing import Any

from authoring.external_llm.manifest import AuthoringManifest, build_authoring_manifest
from authoring.external_llm.prompt_builder import build_initial_prompt
from authoring.external_llm.validator import ValidationReport, validate_external_draft
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding
from axes.axis2_selection.engine.selection import SelectionSpec
from axes.axis2_selection.snapshots.exact_asof import PointInTimeSnapshot
from axes.axis3_monetization.crud.versioned_store import VersionedArtifactStore
from bridges.contracts.three_axis_e2e import THREE_AXIS_E2E_REQUEST_SCHEMA
from bridges.three_axis_e2e_bridge import execute_three_axis_request


REQUEST_ID = "final-natural-language-001"
AS_OF = "20260901090000"
SOURCE_REF = "pit:selection-final/v1"
FEATURE_VERSION = "selection-final-features/v1"
CONDITION_VERSION_LABEL = "cond-final-v1"
PROFIT_ASSUMPTION_ID = "A1"

FINAL_USER_REQUEST = (
    "최근 10일 이내 EMA120을 돌파하면서 기준 Histogram 강도를 기록한 종목 중 현재 다시 "
    "EMA120을 돌파하고 현재 Histogram 강도가 기준 이상인 종목을 선별한다. 선별 종목은 15분봉에서 "
    "종가가 EMA120 위이고 Histogram이 기준 이상이며 MACD 상향돌파 또는 JMA 상승전환이면 매수한다. "
    "수익확보 전에는 EMA120 위에서 JMA 하락전환만으로 매도하지 않고, 수익확보 후 JMA 하락전환이면 매도한다."
)

FEATURE_IDS = (
    "selection.ema120_breakout_within_10d",
    "selection.current_ema120_rebreakout",
    "selection.current_hist_ge_reference",
    "selection.reference_hist",
    "selection.hist_normalized",
)

FINAL_DSL = '''strategy "FinalNaturalLanguageAcceptance" {
    timeframe = "15m"
    input profit_target_pct = 2.0

    ema120 = ta.ema(close, 120)
    macd_line = user.macd_normalized(close, "macd", 12, 26, 9, "exponential")
    macd_signal = user.macd_normalized(close, "signal", 12, 26, 9, "exponential")
    hist_strength = user.macd_normalized(close, "hist_abs_pct", 12, 26, 9, "exponential")
    reference_hist = ctx.selection.reference_hist
    jma = ta.jma(close, 7, 0, 2)
    jma_rising = jma > jma[1]
    jma_turn_up = state.edge(jma_rising)
    jma_turn_down = state.falling_edge(jma_rising)
    macd_turn_up = ta.crossover(macd_line, macd_signal)
    entry_setup = close > ema120 and hist_strength >= reference_hist and (macd_turn_up or jma_turn_up)

    state in_trade = false
    state entry_price = 0
    state profit_secured = false
    state entry_now = false
    state exit_now = false
    state exit_blocked_now = false

    on_bar {
        set entry_now = false
        set exit_now = false
        set exit_blocked_now = false

        if (not in_trade and entry_setup) {
            set in_trade = true
            set entry_price = close
            set profit_secured = false
            set entry_now = true
        }

        if (in_trade and not profit_secured and entry_price > 0 and ((close / entry_price - 1) * 100 >= profit_target_pct)) {
            set profit_secured = true
        }

        if (in_trade and jma_turn_down) {
            if (not profit_secured and close > ema120) {
                set exit_blocked_now = true
            }
            if (profit_secured or close <= ema120) {
                set in_trade = false
                set exit_now = true
                set entry_price = 0
                set profit_secured = false
            }
        }
    }

    on(entry_now) { order.buy(type = "MARKET") }
    on(exit_now) { order.close_long() }
}'''


def build_manifest() -> AuthoringManifest:
    return build_authoring_manifest(
        feature_ids=FEATURE_IDS,
        data_source_ids=(SOURCE_REF,),
        context_feature_types={"selection.reference_hist": "NUMBER"},
    )


def build_external_draft() -> dict[str, Any]:
    return {
        "schema_version": "external_strategy_draft/v1",
        "request_id": REQUEST_ID,
        "intent_summary": (
            "Use exact point-in-time EMA120 breakout/reference Histogram evidence for candidate selection, "
            "then execute a 15m EMA120/Histogram/MACD/JMA strategy with profit-state exit permission."
        ),
        "assumptions": [
            {
                "id": PROFIT_ASSUMPTION_ID,
                "text": "수익확보 기준은 매수 신호 종가 대비 +2.0%로 정의한다.",
                "material": True,
            }
        ],
        "unresolved_questions": [],
        "needs_capability": [],
        "selection_plan": {
            "as_of_policy": "point_in_time",
            "lookback": {
                "trading_days": 10,
                "event": "EMA120_BREAKOUT",
                "lookup_mode": "exact_precomputed_evidence",
            },
            "universe": {"data_source_id": SOURCE_REF},
            "filters": [
                {
                    "feature_id": "selection.ema120_breakout_within_10d",
                    "operator": "EQ",
                    "value": True,
                    "data_source_id": SOURCE_REF,
                },
                {
                    "feature_id": "selection.current_ema120_rebreakout",
                    "operator": "EQ",
                    "value": True,
                    "data_source_id": SOURCE_REF,
                },
                {
                    "feature_id": "selection.current_hist_ge_reference",
                    "operator": "EQ",
                    "value": True,
                    "data_source_id": SOURCE_REF,
                },
                {
                    "feature_id": "selection.reference_hist",
                    "operator": "GT",
                    "value": 0.0,
                    "data_source_id": SOURCE_REF,
                },
            ],
            "rankings": [
                {
                    "feature_id": "selection.hist_normalized",
                    "metric": "RANK",
                    "direction": "ASC",
                    "peer_group_id": "HIGH_BETA",
                    "data_source_id": SOURCE_REF,
                }
            ],
            "candidate_output": {"top_n": 2},
            "evidence_required": [
                "selection.reference_hist",
                "selection.hist_normalized",
            ],
        },
        "strategy_plan": {
            "timeframe": "15m",
            "inputs": {"profit_target_pct": 2.0},
            "entry": [
                "close > EMA120",
                "hist_strength >= selection.reference_hist",
                "MACD crossover OR JMA turn-up",
            ],
            "exit": [
                "block JMA turn-down while profit is not secured and close > EMA120",
                "allow JMA turn-down after profit is secured or close <= EMA120",
            ],
            "risk": [],
            "state": ["in_trade", "entry_price", "profit_secured"],
            "context_dependencies": [
                {
                    "context_id": "selection.reference_hist",
                    "value_type": "NUMBER",
                    "binding": "exact_read_only",
                }
            ],
        },
        "dsl_code": FINAL_DSL,
        "projection_requests": [
            "ema120",
            "hist_strength",
            "reference_hist",
            "jma",
            "entry_setup",
            "exit_blocked_now",
            "exit_now",
        ],
        "data_dependencies": [
            {"data_source_id": SOURCE_REF},
            {"feature_id": "selection.reference_hist"},
        ],
        "rationale": [
            "Cross-symbol/history event search stays in precomputed AXIS 2 evidence.",
            "AXIS 1 receives only the selected symbol and exact candidate reference value.",
        ],
    }


def _provenance() -> dict[str, Any]:
    return {
        "source_ref": SOURCE_REF,
        "observed_as_of": "20260901085900",
        "knowledge_cutoff": AS_OF,
        "formula_version": FEATURE_VERSION,
    }


def _feature_row(
    symbol: str,
    feature_id: str,
    value_type: str,
    value: Any,
    *,
    rank: int | None = None,
    percentile: float | None = None,
    eligible_count: int = 5,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "symbol": symbol,
        "feature_id": feature_id,
        "value_type": value_type,
        "value": value,
        "validity": "VALID",
        "provenance": _provenance(),
    }
    if rank is not None:
        row["ranking"] = {
            "ranking_method": "DESCENDING_DENSE_V1",
            "eligible_count": eligible_count,
            "rank": rank,
            "percentile": float(percentile),
            "peer_group_id": "HIGH_BETA",
        }
    return row


def build_snapshot() -> PointInTimeSnapshot:
    # The first three symbols satisfy the semantic filters; EEE is removed by
    # top-N, CCC fails the current re-breakout condition, and DDD fails the
    # recent-breakout condition.  No feature is computed by the selector.
    symbol_rows = {
        "AAA": (True, True, True, 0.040, 0.180, 1, 100.0),
        "BBB": (True, True, True, 0.050, 0.160, 2, 80.0),
        "EEE": (True, True, True, 0.060, 0.140, 3, 60.0),
        "CCC": (True, False, True, 0.030, 0.120, 4, 40.0),
        "DDD": (False, True, True, 0.020, 0.100, 5, 20.0),
    }
    rows: list[dict[str, Any]] = []
    for symbol, values in symbol_rows.items():
        recent, rebreak, hist_ge_ref, reference_hist, hist_strength, rank, percentile = values
        rows.extend(
            [
                _feature_row(symbol, "selection.ema120_breakout_within_10d", "BOOLEAN", recent),
                _feature_row(symbol, "selection.current_ema120_rebreakout", "BOOLEAN", rebreak),
                _feature_row(symbol, "selection.current_hist_ge_reference", "BOOLEAN", hist_ge_ref),
                _feature_row(symbol, "selection.reference_hist", "NUMBER", reference_hist),
                _feature_row(
                    symbol,
                    "selection.hist_normalized",
                    "NUMBER",
                    hist_strength,
                    rank=rank,
                    percentile=percentile,
                ),
            ]
        )
    return PointInTimeSnapshot.from_dict(
        {
            "schema_version": "axis2_point_in_time_snapshot/v1",
            "snapshot_id": "final-natural-language-snapshot-0900",
            "as_of": AS_OF,
            "knowledge_cutoff": AS_OF,
            "universe_id": "HIGH_BETA-FINAL-v1",
            "feature_version": FEATURE_VERSION,
            "source_refs": [SOURCE_REF],
            "rows": rows,
        }
    )


def build_selection_spec(snapshot: PointInTimeSnapshot) -> SelectionSpec:
    return SelectionSpec.from_dict(
        {
            "schema_version": "axis2_selection_spec/v1",
            "selection_id": "final-natural-language-selection",
            "condition_version": CONDITION_VERSION_LABEL,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "as_of": snapshot.as_of,
            "knowledge_cutoff": snapshot.knowledge_cutoff,
            "filters": [
                {
                    "rule_id": "recent-ema120-breakout",
                    "feature_id": "selection.ema120_breakout_within_10d",
                    "metric": "VALUE",
                    "operator": "EQ",
                    "operand": True,
                    "peer_group_id": None,
                },
                {
                    "rule_id": "current-ema120-rebreakout",
                    "feature_id": "selection.current_ema120_rebreakout",
                    "metric": "VALUE",
                    "operator": "EQ",
                    "operand": True,
                    "peer_group_id": None,
                },
                {
                    "rule_id": "current-hist-ge-reference",
                    "feature_id": "selection.current_hist_ge_reference",
                    "metric": "VALUE",
                    "operator": "EQ",
                    "operand": True,
                    "peer_group_id": None,
                },
                {
                    "rule_id": "reference-hist-present",
                    "feature_id": "selection.reference_hist",
                    "metric": "VALUE",
                    "operator": "GT",
                    "operand": 0.0,
                    "peer_group_id": None,
                },
            ],
            "sort": {
                "feature_id": "selection.hist_normalized",
                "metric": "RANK",
                "direction": "ASC",
                "peer_group_id": "HIGH_BETA",
            },
            "top_n": 2,
            "symbol_scope": None,
        }
    )


def _market_times(size: int) -> list[str]:
    start = datetime(2026, 9, 1, 9, 0, 0)
    return [(start + timedelta(minutes=15 * index)).strftime("%Y%m%d%H%M%S") for index in range(size)]


def build_market(symbol: str) -> dict[str, Any]:
    # Long flat warmup keeps EMA120 stable.  The tail intentionally creates:
    # entry -> pre-profit JMA turn-down (blocked) -> +2% secured -> JMA turn-down exit.
    close = [100.0] * 130 + [
        99.5,
        99.0,
        98.5,
        99.0,
        100.0,
        101.0,
        100.5,
        100.2,
        100.8,
        101.5,
        102.5,
        103.0,
        102.8,
        102.0,
        101.5,
    ]
    times = _market_times(len(close))
    open_ = [value - 0.05 for value in close]
    high = [max(o, c) + 0.30 for o, c in zip(open_, close)]
    low = [min(o, c) - 0.30 for o, c in zip(open_, close)]
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": [1000.0 + index for index in range(len(close))],
        "meta": {
            "instrument": symbol,
            "timeframe": "15m",
            "source": "final-natural-language-acceptance-fixture",
        },
    }


def reference_hist_for(snapshot: PointInTimeSnapshot, symbol: str) -> float:
    rows = [
        row
        for row in snapshot.rows
        if row.symbol == symbol and row.feature_id == "selection.reference_hist"
    ]
    if len(rows) != 1 or rows[0].validity != "VALID":
        raise ValueError(f"exact reference Histogram evidence missing: {symbol}")
    return float(rows[0].value)


def build_parent_context(
    *,
    symbol: str,
    market: dict[str, Any],
    snapshot: PointInTimeSnapshot,
    manifest: AuthoringManifest,
) -> dict[str, Any]:
    reference_hist = reference_hist_for(snapshot, symbol)
    frame_material = f"{snapshot.snapshot_hash}|{symbol}|selection.reference_hist|{reference_hist:.12f}"
    frame_hash = hashlib.sha256(frame_material.encode("utf-8")).hexdigest()
    binding = DSLContextSeriesBinding.from_prepared(
        target_symbol=symbol,
        target_times=market["time"],
        frame_hash=frame_hash,
        registry_hash=manifest.manifest_hash,
        feature_types={"selection.reference_hist": "NUMBER"},
        feature_values={
            "selection.reference_hist": [reference_hist for _ in market["time"]]
        },
    )
    return binding.public_dict()


@dataclass
class FinalNaturalLanguageScenario:
    manifest: AuthoringManifest
    prompt: str
    draft: dict[str, Any]
    blocked_report: ValidationReport
    accepted_report: ValidationReport
    snapshot: PointInTimeSnapshot
    selection_spec: SelectionSpec
    store: VersionedArtifactStore
    request: dict[str, Any]

    def execute(self) -> dict[str, Any]:
        return execute_three_axis_request(self.store, self.request)

    def close(self) -> None:
        self.store.close()


def build_scenario() -> FinalNaturalLanguageScenario:
    manifest = build_manifest()
    draft = build_external_draft()
    prompt = build_initial_prompt(
        request_id=REQUEST_ID,
        user_request=FINAL_USER_REQUEST,
        manifest=manifest,
    )
    blocked = validate_external_draft(
        draft,
        request_id=REQUEST_ID,
        manifest=manifest,
    )
    if blocked.final_status != "BLOCKED_USER_CLARIFICATION":
        raise RuntimeError(f"material assumption did not block acceptance: {blocked.final_status}")
    accepted = validate_external_draft(
        draft,
        request_id=REQUEST_ID,
        manifest=manifest,
        accepted_assumption_ids=(PROFIT_ASSUMPTION_ID,),
    )
    if accepted.final_status != "ACCEPTED_DRAFT":
        raise RuntimeError(
            f"representative structured draft is not deterministically accepted: {accepted.final_status}"
        )

    snapshot = build_snapshot()
    selection_spec = build_selection_spec(snapshot)
    store = VersionedArtifactStore()
    condition = store.create_condition(
        condition_id="condition-final-natural-language",
        name="Recent EMA120 breakout with reference Histogram",
        selection_spec=selection_spec.public_dict(),
        created_at="20260901090500",
    )
    strategy = store.create_strategy(
        strategy_id="strategy-final-natural-language",
        name="15m EMA120 Histogram MACD JMA profit-permission",
        timeframe="15m",
        dsl_code=draft["dsl_code"],
        settings={
            "commission_pct": 0.0,
            "sell_tax_pct": 0.0,
            "slippage_pct": 0.0,
            "allocation_pct": 100.0,
        },
        condition_refs=[
            {"condition_id": condition.condition_id, "version": condition.version}
        ],
        created_at="20260901090600",
    )
    store.transition(
        "CONDITION",
        condition.condition_id,
        condition.version,
        to_status="PROMOTED",
        reason="final acceptance exact PIT condition",
        event_time="20260901090700",
    )
    store.transition(
        "STRATEGY",
        strategy.strategy_id,
        strategy.version,
        to_status="PROMOTED",
        reason="final acceptance deterministic DSL validation",
        event_time="20260901090701",
    )

    execution_inputs: dict[str, Any] = {}
    for symbol in ("AAA", "BBB", "EEE", "CCC", "DDD"):
        market = build_market(symbol)
        execution_inputs[symbol] = {
            "market": market,
            "entry_gate": None,
            "parent_context": build_parent_context(
                symbol=symbol,
                market=market,
                snapshot=snapshot,
                manifest=manifest,
            ),
        }

    request = {
        "schema": THREE_AXIS_E2E_REQUEST_SCHEMA,
        "meta": {
            "request_id": "final-e2e-request-001",
            "source_axis": "EXTERNAL",
            "target_axis": "AXIS3",
            "operation": "SELECT_PLAN_BACKTEST",
            "contract_version": "v1",
        },
        "run_id": "final-e2e-run-001",
        "strategy_ref": {
            "strategy_id": strategy.strategy_id,
            "version": strategy.version,
            "artifact_hash": strategy.artifact_hash,
        },
        "condition_ref": {
            "condition_id": condition.condition_id,
            "version": condition.version,
            "artifact_hash": condition.artifact_hash,
        },
        "snapshot": snapshot.public_dict(),
        "selection_spec": selection_spec.public_dict(),
        "execution_inputs": execution_inputs,
    }
    return FinalNaturalLanguageScenario(
        manifest=manifest,
        prompt=prompt,
        draft=draft,
        blocked_report=blocked,
        accepted_report=accepted,
        snapshot=snapshot,
        selection_spec=selection_spec,
        store=store,
        request=request,
    )
