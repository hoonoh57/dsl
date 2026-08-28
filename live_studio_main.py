"""Independent production-oriented DSL Studio entrypoint.

This module intentionally does NOT import or reuse app_ui.py.
It measures the current DSL engine directly through Parser/Semantic/Runtime/BacktestEngine.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from core.dsl_parser import DSLParser, DSLParseError
from core.dsl_semantic import DSLSemanticAnalyzer, DSLSemanticError
from core.backtest import BacktestEngine, synthetic_market


app = FastAPI(title="Quant DSL Live Studio")


class ValidateRequest(BaseModel):
    dsl_code: str


class EvaluateRequest(BaseModel):
    dsl_code: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    market: Optional[Dict[str, Any]] = None
    data_timeframe: Optional[str] = None
    bars_count: int = 200


@app.get("/api/capabilities")
def capabilities():
    return {
        "engine_path": "DSLParser -> DSLSemanticAnalyzer -> DSLRuntime -> BacktestEngine -> BrokerEmulator",
        "legacy_ui_reused": False,
        "legacy_demo_engine_reused": False,
        "synthetic_fixture_available": True,
        "caller_market_supported": True,
        "deployment_authority": False,
    }


@app.post("/api/validate")
def validate_dsl(req: ValidateRequest):
    try:
        document = DSLParser.parse(req.dsl_code)
        DSLSemanticAnalyzer.analyze(document)
        return {
            "ok": True,
            "strategy": document.name,
            "timeframe": document.timeframe,
            "parser": "PASS",
            "semantic": "PASS",
        }
    except (DSLParseError, DSLSemanticError, ValueError) as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    validation = validate_dsl(ValidateRequest(dsl_code=req.dsl_code))
    if not validation.get("ok"):
        raise HTTPException(status_code=400, detail=validation)

    try:
        market = req.market
        if market is None:
            market = synthetic_market(req.bars_count)
            data_claim = "SYNTHETIC_ENGINE_FIXTURE"
        else:
            market = dict(market)
            meta = dict(market.get("_meta") or {})
            if "source" not in meta:
                meta["source"] = "caller_supplied"
            market["_meta"] = meta
            data_claim = "CALLER_SUPPLIED_MARKET"

        result = BacktestEngine.run(
            req.dsl_code,
            bars_count=req.bars_count,
            settings=req.settings,
            market=market,
            data_timeframe=req.data_timeframe,
        )
        result["evaluation"] = {
            "engine": "core.backtest.BacktestEngine",
            "legacy_demo_engine": False,
            "data_claim": data_claim,
            "data_meta": dict((market or {}).get("_meta") or {}),
            "parser": "PASS",
            "semantic": "PASS",
            "deployment_authority": False,
        }
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail={
            "error_type": type(exc).__name__,
            "message": str(exc),
        }) from exc


LIVE_HTML = """<!doctype html>
<html lang='ko'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Quant DSL Live Studio</title>
<style>
body{margin:0;background:#0b0f15;color:#e7edf6;font-family:system-ui,sans-serif}
main{max-width:1500px;margin:auto;padding:18px}.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}
.card{background:#121923;border:1px solid #283446;border-radius:14px;padding:14px}textarea{width:100%;min-height:440px;background:#080c12;color:#dbe7f5;border:1px solid #33445c;border-radius:10px;padding:12px;font:13px/1.5 Consolas,monospace;box-sizing:border-box}
button{background:#4f8cff;color:#fff;border:0;border-radius:9px;padding:10px 14px;font-weight:700;cursor:pointer;margin-right:8px}.ok{color:#4ade80}.bad{color:#fb7185}pre{white-space:pre-wrap;overflow:auto;background:#080c12;border-radius:10px;padding:12px;max-height:520px}.meta{color:#93a4bb;font-size:12px}
</style>
</head>
<body><main>
<h2>Quant DSL Live Studio</h2><div class='meta'>Legacy UI와 분리된 최신 Core DSL 직접 평가기</div><br>
<div class='grid'><section class='card'><h3>DSL</h3><textarea id='dsl'>strategy "Live_SMA" {
    timeframe = "1d"
    ma_fast = ta.sma(close, 5)
    ma_slow = ta.sma(close, 20)
    entry_cond = ta.crossover(ma_fast, ma_slow)
    exit_cond = ta.crossunder(ma_fast, ma_slow)
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}</textarea><p><button onclick='validateDSL()'>검증</button><button onclick='evaluateDSL()'>Core 백테스트</button></p><div id='status'></div></section>
<section class='card'><h3>엔진 결과</h3><div class='meta'>synthetic fixture는 엔진 계측용입니다. 실전 평가는 caller-supplied OHLCV를 사용해야 합니다.</div><pre id='out'>대기 중</pre></section></div>
<script>
const $=x=>document.getElementById(x);
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw j;return j}
async function validateDSL(){try{const j=await post('/api/validate',{dsl_code:$('dsl').value});$('status').className=j.ok?'ok':'bad';$('status').textContent=j.ok?'Parser/Semantic PASS':j.message;$('out').textContent=JSON.stringify(j,null,2)}catch(e){$('status').className='bad';$('status').textContent='검증 실패';$('out').textContent=JSON.stringify(e,null,2)}}
async function evaluateDSL(){try{const j=await post('/api/evaluate',{dsl_code:$('dsl').value,bars_count:300});$('status').className='ok';$('status').textContent='실제 BacktestEngine 실행 PASS';$('out').textContent=JSON.stringify({evaluation:j.evaluation,strategy:j.strategy,metrics:j.metrics_numeric,diagnostics:j.diagnostics,trades:j.closed_trades},null,2)}catch(e){$('status').className='bad';$('status').textContent='실행 실패';$('out').textContent=JSON.stringify(e,null,2)}}
</script></main></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return LIVE_HTML


if __name__ == "__main__":
    uvicorn.run("live_studio_main:app", host="127.0.0.1", port=8010, reload=False)
