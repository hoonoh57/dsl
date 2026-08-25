"""Append-only raw prompt/response provenance for the Stage 1 improvement loop."""
from __future__ import annotations
import json
import time
from typing import Optional

from core.strategy_factory import StrategyFactoryStore


class LLMExchangeMemory:
    def __init__(self, store: StrategyFactoryStore):
        self.store = store
        conn = store.connect()
        conn.execute("""CREATE TABLE IF NOT EXISTS stage1_llm_exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_id INTEGER NOT NULL,
            before_experiment_id INTEGER NOT NULL,
            after_experiment_id INTEGER,
            prompt_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            hypothesis TEXT,
            status TEXT NOT NULL,
            created_at REAL NOT NULL
        )""")
        conn.commit(); conn.close()

    def record(self, *, before_experiment_id: int, after_experiment_id: Optional[int], prompt_text: str,
               response_text: str, hypothesis: str = "", status: str = "RECORDED") -> int:
        before = self.store.get_experiment(before_experiment_id)
        if after_experiment_id is not None:
            after = self.store.get_experiment(after_experiment_id)
            if after["root_id"] != before["root_id"]:
                raise ValueError("LLM exchange before/after root가 다릅니다.")
        conn = self.store.connect()
        cur = conn.execute("""INSERT INTO stage1_llm_exchanges(root_id,before_experiment_id,after_experiment_id,
                           prompt_text,response_text,hypothesis,status,created_at) VALUES (?,?,?,?,?,?,?,?)""",
                           (before["root_id"], before_experiment_id, after_experiment_id,
                            prompt_text or "", response_text or "", hypothesis or "", status, time.time()))
        value = int(cur.lastrowid); conn.commit(); conn.close(); return value

    def recent(self, root_id: int, limit: int = 10) -> list[dict]:
        conn = self.store.connect()
        rows = conn.execute("SELECT * FROM stage1_llm_exchanges WHERE root_id=? ORDER BY id DESC LIMIT ?",
                            (root_id, max(1, min(int(limit), 100)))).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def prompt_history_context(self, root_id: int, limit: int = 6) -> str:
        rows = list(reversed(self.recent(root_id, limit)))
        if not rows:
            return "(이전 raw LLM exchange 없음)"
        compact = []
        for row in rows:
            compact.append({
                "exchange_id": row["id"],
                "before": row["before_experiment_id"],
                "after": row["after_experiment_id"],
                "hypothesis": row["hypothesis"],
                "status": row["status"],
                "prompt": row["prompt_text"],
                "response": row["response_text"],
            })
        return json.dumps(compact, ensure_ascii=False, indent=2)
