"""Resumable deterministic Parameter Seeker sessions for Stage 1 UI/API.

The synchronous ParameterSeeker remains the small/test path. This service owns
long-running product searches: deterministic candidate plans, batch progress,
cancel/resume, cross-session evaluation cache, and finalized post-Seeker
Improvement Episodes for LLM structural candidates.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import time

from core.backtest import BacktestEngine
from core.stage1_data_store import load_market_snapshot
from core.strategy_factory import (
    ParameterSeeker,
    ParameterSpec,
    ResultAnalyzer,
    StrategyFactory,
    stable_hash,
)


class ResumableSeekerService:
    def __init__(self, factory: StrategyFactory):
        self.factory = factory
        self.store = factory.store
        conn = self.store.connect()
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS stage1_seek_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_experiment_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            objective TEXT NOT NULL,
            seed INTEGER NOT NULL,
            specs_json TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            cursor INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            best_candidate_hash TEXT,
            best_score REAL,
            result_experiment_id INTEGER,
            error_text TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_seek_session_candidates (
            session_id INTEGER NOT NULL,
            ordinal INTEGER NOT NULL,
            candidate_hash TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            score REAL NOT NULL,
            cache_hit INTEGER NOT NULL,
            created_at REAL NOT NULL,
            PRIMARY KEY(session_id, ordinal)
        );
        CREATE TABLE IF NOT EXISTS stage1_evaluation_cache (
            candidate_hash TEXT PRIMARY KEY,
            dsl_code TEXT NOT NULL,
            settings_json TEXT NOT NULL,
            data_hash TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        """)
        conn.commit(); conn.close()

    @staticmethod
    def _json(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _return_pct(experiment: dict) -> float:
        return float(experiment.get("result", {}).get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)

    def create(self, *, parent_experiment_id: int, parameter_specs: list[dict], method="grid",
               objective="MAX_RETURN", seed=42, max_candidates=5000) -> dict:
        parent = self.store.get_experiment(parent_experiment_id)
        specs = [ParameterSpec.from_payload(item) for item in parameter_specs]
        if not specs:
            raise ValueError("parameter space가 비어 있습니다.")
        method = method.lower()
        if method not in {"grid", "random"}:
            raise ValueError("resumable seeker는 grid/random만 지원합니다.")
        total = math.prod(len(spec.values) for spec in specs)
        if total <= 0:
            raise ValueError("candidate space가 비어 있습니다.")
        combos = list(itertools.product(*(spec.values for spec in specs)))
        if method == "random":
            random.Random(seed).shuffle(combos)
        if len(combos) > max_candidates:
            if method == "grid":
                raise ValueError(f"grid candidate {len(combos)}개가 max_candidates={max_candidates}를 초과합니다.")
            combos = combos[:max_candidates]
        plan = [list(values) for values in combos]
        now = time.time(); conn = self.store.connect()
        cur = conn.execute("""INSERT INTO stage1_seek_sessions(parent_experiment_id,method,objective,seed,specs_json,plan_json,
                            cursor,status,created_at,updated_at) VALUES (?,?,?,?,?,?,0,'READY',?,?)""",
                           (parent["id"], method, objective, int(seed), self._json(parameter_specs), self._json(plan), now, now))
        session_id = int(cur.lastrowid); conn.commit(); conn.close()
        return self.get(session_id)

    def get(self, session_id: int) -> dict:
        conn = self.store.connect()
        row = conn.execute("SELECT * FROM stage1_seek_sessions WHERE id=?", (session_id,)).fetchone()
        conn.close()
        if not row: raise ValueError(f"seeker session이 없습니다: {session_id}")
        item = dict(row); plan = json.loads(item.pop("plan_json")); item["specs"] = json.loads(item.pop("specs_json"))
        item["total_candidates"] = len(plan); item["remaining"] = max(0, len(plan) - int(item["cursor"]));
        item["progress_pct"] = 100.0 if not plan else float(item["cursor"]) / len(plan) * 100.0
        return item

    def cancel(self, session_id: int):
        session = self.get(session_id)
        if session["status"] in {"COMPLETED", "FAILED"}: return session
        conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='CANCELED',updated_at=? WHERE id=?",
                                                  (time.time(), session_id)); conn.commit(); conn.close(); return self.get(session_id)

    def resume(self, session_id: int):
        session = self.get(session_id)
        if session["status"] == "COMPLETED": return session
        if session["status"] == "FAILED": raise ValueError("FAILED session은 새 session으로 재시작해야 합니다.")
        conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='READY',updated_at=? WHERE id=?",
                                                  (time.time(), session_id)); conn.commit(); conn.close(); return self.get(session_id)

    def candidates(self, session_id: int, limit=50):
        conn = self.store.connect()
        rows = conn.execute("SELECT * FROM stage1_seek_session_candidates WHERE session_id=? ORDER BY score DESC,ordinal LIMIT ?",
                            (session_id, max(1, min(int(limit), 500)))).fetchall(); conn.close()
        output = []
        for row in rows:
            item = dict(row); item["parameters"] = json.loads(item.pop("parameters_json")); output.append(item)
        return output

    def _cached(self, candidate_hash: str):
        conn = self.store.connect(); row = conn.execute("SELECT result_json FROM stage1_evaluation_cache WHERE candidate_hash=?", (candidate_hash,)).fetchone(); conn.close()
        return json.loads(row["result_json"]) if row else None

    def _cache(self, candidate_hash: str, dsl_code: str, settings: dict, data_hash: str, result: dict):
        conn = self.store.connect(); conn.execute("""INSERT OR IGNORE INTO stage1_evaluation_cache(candidate_hash,dsl_code,settings_json,data_hash,result_json,created_at)
            VALUES (?,?,?,?,?,?)""", (candidate_hash, dsl_code, self._json(settings), data_hash, self._json(result), time.time())); conn.commit(); conn.close()

    def process(self, session_id: int, batch_size=25) -> dict:
        session = self.get(session_id)
        if session["status"] == "CANCELED": return {"session": session, "top": self.candidates(session_id)}
        if session["status"] == "COMPLETED": return {"session": session, "top": self.candidates(session_id), "experiment": self._result_experiment(session)}
        parent = self.store.get_experiment(session["parent_experiment_id"])
        market = load_market_snapshot(parent["provenance"]["data_hash"])
        specs = [ParameterSpec.from_payload(item) for item in session["specs"]]
        conn = self.store.connect(); raw = conn.execute("SELECT plan_json FROM stage1_seek_sessions WHERE id=?", (session_id,)).fetchone(); conn.close()
        plan = json.loads(raw["plan_json"])
        cursor = int(session["cursor"]); end = min(len(plan), cursor + max(1, min(int(batch_size), 500)))
        try:
            conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='RUNNING',updated_at=? WHERE id=?", (time.time(), session_id)); conn.commit(); conn.close()
            for ordinal in range(cursor, end):
                current = self.get(session_id)
                if current["status"] == "CANCELED": break
                values = tuple(float(value) for value in plan[ordinal])
                candidate_dsl, settings, parameters = ParameterSeeker._candidate_payload(parent["dsl_code"], parent["execution"], specs, values)
                candidate_hash = stable_hash({"dsl":candidate_dsl,"settings":settings,"data_hash":parent["provenance"]["data_hash"]})
                result = self._cached(candidate_hash); cache_hit = 1
                if result is None:
                    result = BacktestEngine.run(candidate_dsl, settings=settings, market=market, data_timeframe=parent["provenance"]["timeframe"])
                    self._cache(candidate_hash, candidate_dsl, settings, parent["provenance"]["data_hash"], result); cache_hit = 0
                score = ParameterSeeker._score(result, session["objective"])
                conn = self.store.connect()
                conn.execute("""INSERT OR IGNORE INTO stage1_seek_session_candidates(session_id,ordinal,candidate_hash,parameters_json,score,cache_hit,created_at)
                                VALUES (?,?,?,?,?,?,?)""", (session_id, ordinal, candidate_hash, self._json(parameters), score, cache_hit, time.time()))
                best = conn.execute("SELECT candidate_hash,score FROM stage1_seek_session_candidates WHERE session_id=? ORDER BY score DESC,ordinal LIMIT 1", (session_id,)).fetchone()
                conn.execute("UPDATE stage1_seek_sessions SET cursor=?,best_candidate_hash=?,best_score=?,updated_at=? WHERE id=?",
                             (ordinal + 1, best["candidate_hash"], best["score"], time.time(), session_id))
                conn.commit(); conn.close()
            session = self.get(session_id)
            if session["cursor"] >= session["total_candidates"]:
                experiment = self._finalize(session_id)
                return {"session": self.get(session_id), "top": self.candidates(session_id), "experiment": experiment}
            conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='READY',updated_at=? WHERE id=? AND status!='CANCELED'", (time.time(), session_id)); conn.commit(); conn.close()
            return {"session": self.get(session_id), "top": self.candidates(session_id)}
        except Exception as exc:
            conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='FAILED',error_text=?,updated_at=? WHERE id=?", (str(exc), time.time(), session_id)); conn.commit(); conn.close(); raise

    def _result_experiment(self, session: dict):
        if not session.get("result_experiment_id"): return None
        return self.store.get_experiment(int(session["result_experiment_id"]))

    def _finalize_structural_episode(self, parent: dict, child: dict):
        if parent.get("operation") != "LLM_STRUCTURAL" or not parent.get("parent_id"):
            return None
        before = self.store.get_experiment(int(parent["parent_id"]))
        before_return = self._return_pct(before)
        after_return = self._return_pct(child)
        verdict = "ACCEPTED_IMPROVEMENT" if after_return > before_return else "REJECTED_NO_GAIN"
        reason = f"after_seeker return {before_return:.4f}% -> {after_return:.4f}%"
        return self.store.create_episode(
            before_id=before["id"],
            after_id=child["id"],
            observation=json.dumps(before.get("analysis", {}).get("findings", []), ensure_ascii=False),
            hypothesis=str(parent.get("hypothesis") or ""),
            proposal=parent["dsl_code"],
            expected_effect=str(parent.get("expected_effect") or ""),
            verdict=verdict,
            reason=reason,
        )

    def _finalize(self, session_id: int):
        session = self.get(session_id)
        if session.get("result_experiment_id"): return self._result_experiment(session)
        parent = self.store.get_experiment(session["parent_experiment_id"])
        conn = self.store.connect()
        best = conn.execute("SELECT * FROM stage1_seek_session_candidates WHERE session_id=? ORDER BY score DESC,ordinal LIMIT 1", (session_id,)).fetchone()
        cache = conn.execute("SELECT * FROM stage1_evaluation_cache WHERE candidate_hash=?", (best["candidate_hash"],)).fetchone() if best else None
        conn.close()
        if not best or not cache: raise ValueError("완료된 seeker session에 best candidate가 없습니다.")
        result = json.loads(cache["result_json"]); parameters = json.loads(best["parameters_json"]); dsl_code = cache["dsl_code"]; settings = json.loads(cache["settings_json"])
        top = self.candidates(session_id, 20); scores = [float(item["score"]) for item in top]
        search_summary = {"session_id":session_id,"method":session["method"],"objective":session["objective"],
            "evaluated":session["total_candidates"],"best_score":float(best["score"]),"best_parameters":parameters,
            "neighborhood":scores[:7],"spike_ratio":abs(scores[0])/max(1e-9,abs(scores[1])) if len(scores)>1 and abs(scores[0])>abs(scores[1]) else 1.0,
            "cache_hits":sum(int(item["cache_hit"]) for item in top)}
        analysis = ResultAnalyzer.analyze(result, search_summary)
        child = self.store.create_experiment(parent_id=parent["id"], operation="SEEKER_BEST", strategy_name=parent["strategy_name"],
            intent=parent["intent"], dsl_code=dsl_code, parameters=parameters, execution=settings, provenance=parent["provenance"], result=result, analysis=analysis)
        finalized_episode_id = self._finalize_structural_episode(parent, child)
        conn = self.store.connect(); conn.execute("UPDATE stage1_seek_sessions SET status='COMPLETED',result_experiment_id=?,updated_at=? WHERE id=?",
                                                  (child["id"], time.time(), session_id)); conn.commit(); conn.close()
        if finalized_episode_id is not None:
            child = dict(child)
            child["finalized_episode_id"] = finalized_episode_id
        return child
