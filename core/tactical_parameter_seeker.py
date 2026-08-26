"""Deterministic numeric parameter search across one frozen BattleCase set.

E3 keeps tactic structure fixed.  Only declared numeric DSL ``input`` values may
change; execution settings and BattleCases remain frozen so every candidate is
measured under the same case_set_hash/context policy.

There is intentionally no hidden universal score.  Candidate profiles are
compared by TacticalCompetitionEngine metric leaderboards and Pareto evidence.
"""
from __future__ import annotations

from dataclasses import asdict
import itertools
import math
import random
from typing import Any, Mapping, Sequence

from core.strategy_factory import ParameterSpec, apply_dsl_parameters, stable_hash
from core.tactical_competition import TacticalCompetitionEngine
from core.tactical_discovery import BattleCase, TacticCandidate, TacticalDiscoveryEngine


SCHEMA_VERSION = "tactical_parameter_seek/v1"


class MultiBattleParameterSeeker:
    """Seek numeric DSL inputs while keeping structure and battle contract fixed."""

    @staticmethod
    def _validate_specs(specs: Sequence[ParameterSpec]) -> tuple[ParameterSpec, ...]:
        frozen = tuple(specs)
        if not frozen:
            raise ValueError("Multi-Battle Parameter Seeker parameter space가 비어 있습니다.")
        names = [str(spec.name).strip() for spec in frozen]
        if any(not name for name in names) or len(set(names)) != len(names):
            raise ValueError("parameter name은 비어 있거나 중복될 수 없습니다.")
        for spec in frozen:
            if spec.target != "dsl":
                raise ValueError(
                    "E3 Multi-Battle Parameter Seeker는 frozen BattleCase 계약을 보존하기 위해 DSL input만 조정합니다."
                )
            if not spec.values:
                raise ValueError(f"parameter candidate가 비어 있습니다: {spec.name}")
            values = tuple(float(value) for value in spec.values)
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"parameter candidate에 NaN/Infinity가 있습니다: {spec.name}")
            if len(set(values)) != len(values):
                raise ValueError(f"parameter candidate 값에 중복이 있습니다: {spec.name}")
        return frozen

    @staticmethod
    def _plan(
        specs: tuple[ParameterSpec, ...],
        *,
        method: str,
        seed: int,
        max_candidates: int,
    ) -> tuple[tuple[float, ...], ...]:
        method = str(method or "").strip().lower()
        if method not in {"grid", "random"}:
            raise ValueError("E3 Multi-Battle Parameter Seeker는 grid/random만 지원합니다.")
        max_candidates = int(max_candidates)
        if max_candidates < 2:
            raise ValueError("max_candidates는 2 이상이어야 합니다.")
        total_space = math.prod(len(spec.values) for spec in specs)
        if total_space < 2:
            raise ValueError("parameter search에는 서로 다른 candidate가 최소 2개 필요합니다.")

        if method == "grid":
            if total_space > max_candidates:
                raise ValueError(
                    f"grid candidate {total_space}개가 max_candidates={max_candidates}를 초과합니다."
                )
            return tuple(
                tuple(float(value) for value in values)
                for values in itertools.product(*(spec.values for spec in specs))
            )

        rng = random.Random(int(seed))
        count = min(total_space, max_candidates)
        if total_space <= max_candidates:
            combinations = [
                tuple(float(value) for value in values)
                for values in itertools.product(*(spec.values for spec in specs))
            ]
            rng.shuffle(combinations)
            return tuple(combinations)

        seen: set[tuple[float, ...]] = set()
        combinations: list[tuple[float, ...]] = []
        while len(combinations) < count:
            values = tuple(float(rng.choice(spec.values)) for spec in specs)
            if values in seen:
                continue
            seen.add(values)
            combinations.append(values)
        return tuple(combinations)

    @staticmethod
    def _candidate(
        base_candidate: TacticCandidate,
        specs: tuple[ParameterSpec, ...],
        values: tuple[float, ...],
    ) -> tuple[TacticCandidate, dict[str, float]]:
        parameters = {spec.name: float(value) for spec, value in zip(specs, values)}
        candidate_dsl = apply_dsl_parameters(base_candidate.dsl_code, parameters)
        parameter_hash = stable_hash(parameters)
        metadata = dict(base_candidate.metadata)
        metadata.update(
            {
                "parameter_seek_parent_hash": base_candidate.candidate_hash,
                "parameter_values": parameters,
                "parameter_hash": parameter_hash,
            }
        )
        candidate = TacticCandidate(
            candidate_id=f"{base_candidate.candidate_id}::P::{parameter_hash[:12]}",
            dsl_code=candidate_dsl,
            complexity_units=int(base_candidate.complexity_units),
            metadata=metadata,
        )
        candidate.validate()
        return candidate, parameters

    @classmethod
    def run(
        cls,
        *,
        base_candidate: TacticCandidate,
        cases: Sequence[BattleCase],
        specs: Sequence[ParameterSpec],
        method: str = "grid",
        seed: int = 42,
        max_candidates: int = 5000,
        max_workers: int = 4,
        require_neutral_context: bool = True,
        require_uniform_settings: bool = True,
    ) -> dict:
        base_candidate.validate()
        frozen_cases = tuple(cases)
        if not frozen_cases:
            raise ValueError("Multi-Battle Parameter Seeker BattleCase가 비어 있습니다.")
        frozen_specs = cls._validate_specs(specs)
        plan = cls._plan(
            frozen_specs,
            method=method,
            seed=int(seed),
            max_candidates=int(max_candidates),
        )

        rows: list[dict[str, Any]] = []
        profiles: list[Mapping[str, Any]] = []
        seen_candidate_hashes: set[str] = set()
        expected_case_set_hash: str | None = None
        expected_context_policy_hash: str | None = None

        for values in plan:
            candidate, parameters = cls._candidate(base_candidate, frozen_specs, values)
            if candidate.candidate_hash in seen_candidate_hashes:
                raise ValueError("서로 다른 parameter 조합이 동일 candidate identity를 만들었습니다.")
            seen_candidate_hashes.add(candidate.candidate_hash)

            profile = TacticalDiscoveryEngine.evaluate(
                candidate=candidate,
                cases=frozen_cases,
                max_workers=int(max_workers),
                require_neutral_context=bool(require_neutral_context),
                require_uniform_settings=bool(require_uniform_settings),
            )
            case_set_hash = str(profile.get("case_set_hash") or "")
            context_policy_hash = stable_hash(dict(profile.get("context_policy") or {}))
            if expected_case_set_hash is None:
                expected_case_set_hash = case_set_hash
                expected_context_policy_hash = context_policy_hash
            elif case_set_hash != expected_case_set_hash or context_policy_hash != expected_context_policy_hash:
                raise ValueError("parameter candidate 간 frozen BattleCase/context policy가 달라졌습니다.")

            rows.append(
                {
                    "candidate_hash": candidate.candidate_hash,
                    "candidate_id": candidate.candidate_id,
                    "parameters": parameters,
                    "profile_run_hash": profile["run_hash"],
                }
            )
            profiles.append(profile)

        competition = TacticalCompetitionEngine.compare(profiles)
        by_hash = {row["candidate_hash"]: row for row in rows}
        pareto_parameters = [
            {
                "candidate_hash": candidate_hash,
                "parameters": dict(by_hash[candidate_hash]["parameters"]),
            }
            for candidate_hash in competition["pareto_frontier"]
        ]
        leaderboards = {
            metric: [
                {
                    "candidate_hash": candidate_hash,
                    "parameters": dict(by_hash[candidate_hash]["parameters"]),
                }
                for candidate_hash in candidate_hashes
            ]
            for metric, candidate_hashes in competition["leaderboards"].items()
        }

        space = [asdict(spec) for spec in frozen_specs]
        seek_identity = {
            "schema": SCHEMA_VERSION,
            "base_candidate_hash": base_candidate.candidate_hash,
            "case_set_hash": expected_case_set_hash,
            "context_policy": dict(competition["context_policy"]),
            "method": str(method).strip().lower(),
            "seed": int(seed),
            "space": space,
            "candidate_hashes": [row["candidate_hash"] for row in rows],
            "profile_run_hashes": [row["profile_run_hash"] for row in rows],
            "competition_hash": competition["comparison_hash"],
        }
        return {
            "schema": SCHEMA_VERSION,
            "base_candidate": {
                "candidate_id": base_candidate.candidate_id,
                "candidate_hash": base_candidate.candidate_hash,
                "complexity_units": int(base_candidate.complexity_units),
            },
            "case_set_hash": expected_case_set_hash,
            "context_policy": dict(competition["context_policy"]),
            "method": str(method).strip().lower(),
            "seed": int(seed),
            "space": space,
            "total_space": math.prod(len(spec.values) for spec in frozen_specs),
            "evaluated": len(rows),
            "candidates": rows,
            "profiles": profiles,
            "pareto_parameters": pareto_parameters,
            "leaderboards": leaderboards,
            "competition": competition,
            "selection_policy": "PARETO_NO_HIDDEN_UNIVERSAL_SCORE",
            "seek_hash": stable_hash(seek_identity),
        }
