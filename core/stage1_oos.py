from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, Optional

from core.backtest import BacktestEngine
from core.stage1_data_store import load_market_snapshot, save_market_snapshot
from core.strategy_factory import DataContract, StrategyFactory


def _json_safe(value: Any):
    """Return a strict-JSON-safe copy without changing engine-internal semantics.

    Backtest metrics may legitimately contain +/-Infinity (for example profit
    factor when there are gains and zero losses). Starlette/FastAPI emits strict
    JSON and rejects those floats during response serialization, which otherwise
    turns a successful OOS evaluation into HTTP 500 after the endpoint returns.
    """
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


class OOSRegistry:
    def __init__(self, factory: StrategyFactory):
        self.factory = factory
        self.store = factory.store
        conn = self.store.connect()
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS stage1_oos_splits (
            root_id INTEGER PRIMARY KEY,
            full_data_hash TEXT NOT NULL,
            train_data_hash TEXT NOT NULL,
            holdout_data_hash TEXT NOT NULL,
            holdout_fraction REAL NOT NULL,
            split_index INTEGER NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_oos_results (
            experiment_id INTEGER PRIMARY KEY,
            root_id INTEGER NOT NULL,
            holdout_data_hash TEXT NOT NULL,
            result_json TEXT NOT NULL,
            evaluated_at REAL NOT NULL
        );
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def split_market(market: Dict[str, Any], holdout_fraction: float):
        fraction = float(holdout_fraction)
        if not 0.05 <= fraction <= 0.5:
            raise ValueError("holdout_fraction은 0.05~0.5 범위여야 합니다.")
        size = len(market.get("close", []))
        if size < 60:
            raise ValueError("OOS split에는 최소 60 bars가 필요합니다.")
        split_index = int(math.floor(size * (1.0 - fraction)))
        if split_index < 30 or size - split_index < 20:
            raise ValueError("train/holdout 구간에 충분한 bars가 없습니다.")
        meta = dict(market.get("_meta") or {})

        def take(start, end, partition):
            payload = {key: list(market[key][start:end]) for key in ("time", "open", "high", "low", "close", "volume")}
            normalized, _ = DataContract.normalize(
                payload,
                instrument=str(meta.get("instrument", "UNKNOWN")),
                timeframe=str(meta.get("timeframe", "1d")),
                source=str(meta.get("source", "unknown")) + f"#{partition}",
                adjustment_policy=str(meta.get("adjustment_policy", "unspecified")),
                session=str(meta.get("session", "regular")),
                knowledge_cutoff=str(meta.get("knowledge_cutoff", "")),
            )
            normalized["_meta"]["partition"] = partition
            normalized["_meta"]["parent_data_hash"] = meta.get("data_hash", "")
            return normalized

        return take(0, split_index, "train"), take(split_index, size, "holdout"), split_index

    def bind_split(self, root_id: int, full_market: Dict[str, Any], train_market: Dict[str, Any],
                   holdout_market: Dict[str, Any], holdout_fraction: float, split_index: int):
        values = (save_market_snapshot(full_market), save_market_snapshot(train_market), save_market_snapshot(holdout_market))
        conn = self.store.connect()
        existing = conn.execute("SELECT * FROM stage1_oos_splits WHERE root_id=?", (root_id,)).fetchone()
        if existing:
            conn.close()
            current = dict(existing)
            expected = (values[0], values[1], values[2], float(holdout_fraction), int(split_index))
            actual = (current["full_data_hash"], current["train_data_hash"], current["holdout_data_hash"],
                      float(current["holdout_fraction"]), int(current["split_index"]))
            if actual != expected:
                raise ValueError("기존 root의 OOS split은 변경할 수 없습니다.")
            return current
        conn.execute("""INSERT INTO stage1_oos_splits(root_id,full_data_hash,train_data_hash,holdout_data_hash,
                     holdout_fraction,split_index,created_at) VALUES (?,?,?,?,?,?,?)""",
                     (root_id, values[0], values[1], values[2], float(holdout_fraction), int(split_index), time.time()))
        conn.commit()
        conn.close()
        return self.get_split(root_id)

    def get_split(self, root_id: int) -> Optional[dict]:
        conn = self.store.connect()
        row = conn.execute("SELECT * FROM stage1_oos_splits WHERE root_id=?", (root_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def evaluate(self, experiment_id: int):
        experiment = self.store.get_experiment(experiment_id)
        split = self.get_split(experiment["root_id"])
        if not split:
            raise ValueError("이 Experiment root에는 OOS holdout split이 없습니다.")
        if experiment["provenance"].get("data_hash") != split["train_data_hash"]:
            raise ValueError("Experiment가 등록된 train data hash에서 생성되지 않았습니다.")
        holdout = load_market_snapshot(split["holdout_data_hash"])
        raw_result = BacktestEngine.run(experiment["dsl_code"], settings=experiment["execution"], market=holdout,
                                        data_timeframe=experiment["provenance"].get("timeframe"))
        result = _json_safe(raw_result)
        conn = self.store.connect()
        conn.execute("""INSERT OR REPLACE INTO stage1_oos_results(experiment_id,root_id,holdout_data_hash,result_json,evaluated_at)
                        VALUES (?,?,?,?,?)""",
                     (experiment_id, experiment["root_id"], split["holdout_data_hash"],
                      json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False), time.time()))
        conn.commit()
        conn.close()
        return {"experiment_id": experiment_id, "root_id": experiment["root_id"], "split": split, "result": result}

    def result(self, experiment_id: int) -> Optional[dict]:
        conn = self.store.connect()
        row = conn.execute("SELECT * FROM stage1_oos_results WHERE experiment_id=?", (experiment_id,)).fetchone()
        conn.close()
        if not row:
            return None
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json"))
        return item

    def root_results(self, root_id: int):
        conn = self.store.connect()
        rows = conn.execute("SELECT * FROM stage1_oos_results WHERE root_id=? ORDER BY evaluated_at", (root_id,)).fetchall()
        conn.close()
        output = []
        for row in rows:
            item = dict(row)
            item["result"] = json.loads(item.pop("result_json"))
            output.append(item)
        return output
