"""Similarity checks for repeated/rejected structural hypotheses."""
from __future__ import annotations
import re
from typing import Iterable

from core.strategy_factory import StrategyFactoryStore


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_가-힣]+", text or "") if len(token) > 1}


def similarity(a: str, b: str) -> float:
    left, right = _tokens(a), _tokens(b)
    if not left and not right: return 1.0
    if not left or not right: return 0.0
    return len(left & right) / len(left | right)


class HypothesisMemory:
    def __init__(self, store: StrategyFactoryStore): self.store = store

    def similar_prior(self, root_id: int, hypothesis: str, threshold: float = 0.55, limit: int = 100) -> list[dict]:
        rows = self.store.episodes_for_root(root_id, limit)
        output = []
        for row in rows:
            score = similarity(hypothesis, row.get("hypothesis", ""))
            if score >= threshold:
                output.append({"episode_id": row["id"], "similarity": score, "prior_hypothesis": row.get("hypothesis", ""),
                               "verdict": row.get("verdict"), "reason": row.get("reason")})
        output.sort(key=lambda item: item["similarity"], reverse=True)
        return output

    def rejected_memory(self, root_id: int, limit: int = 50) -> list[dict]:
        return [row for row in self.store.episodes_for_root(root_id, limit)
                if str(row.get("verdict", "")).startswith("REJECTED") or row.get("verdict") in {"INVALID_DSL","ENGINE_BLOCKED"}]
