"""Independent production-oriented DSL Studio entrypoint.

No legacy app/UI is reused.  This surface measures the current DSL engine through
Parser -> Semantic -> Runtime -> BacktestEngine -> BrokerEmulator and exposes an
executable catalog for every registered DSL function plus core grammar/execution cases.
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
from core.dsl_feature_catalog import FEATURE_CASES, cases_by_category, intraday_market


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
        "feature_catalog_count": len(FEATURE_CASES),
        "deployment_authority": False,
    }


@app.post("/api/validate")
def validate_dsl(req: ValidateRequest):
    try:
        document = DSLParser.parse(req.dsl_code)
        DSLSemanticAnalyzer.analyze(document)
        return {"ok": True, "strategy": document.name, "timeframe": document.timeframe, "parser": "PASS", "semantic": "PASS"}
    except (DSLParseError, DSLSemanticError, ValueError) as exc:
        return {"ok": False, "error_type": type(exc).__name__, "message": str(exc)}


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
        raise HTTPException(status_code=400, detail={"error_type": type(exc).__name__, "message": str(exc)}) from exc


@app.get("/api/features")
def feature_catalog():
    categories = []
    for category, cases in cases_by_category().items():
        categories.append({
            "category": category,
            "count": len(cases),
            "features": [case.public_dict() for case in cases],
        })
    return {"count": len(FEATURE_CASES), "categories": categories}


def run_feature_case(feature_id: str) -> dict:
    case = FEATURE_CASES.get(feature_id)
    if case is None:
        return {"ok": False, "feature_id": feature_id, "stage": "CATALOG", "message": "등록되지 않은 feature"}
    validation = validate_dsl(ValidateRequest(dsl_code=case.dsl_code))
    if not validation.get("ok"):
        return {"ok": False, "feature_id": feature_id, "category": case.category, "stage": "PARSER_SEMANTIC", "validation": validation, "dsl_code": case.dsl_code}
    try:
        if case.fixture == "intraday":
            market = intraday_market(420)
            data_timeframe = "1m"
        else:
            market = synthetic_market(300)
            data_timeframe = "1d"
        result = BacktestEngine.run(
            case.dsl_code,
            settings=dict(case.settings or {}),
            market=market,
            data_timeframe=data_timeframe,
        )
        return {
            "ok": True,
            "feature_id": feature_id,
            "category": case.category,
            "title": case.title,
            "stage": "CORE_BACKTEST",
            "parser": "PASS",
            "semantic": "PASS",
            "backtest": "PASS",
            "fixture": case.fixture,
            "dsl_code": case.dsl_code,
            "metrics": result.get("metrics_numeric", {}),
            "signal_counts": result.get("diagnostics", {}).get("signal_counts", {}),
            "rejections": result.get("diagnostics", {}).get("rejections", {}),
            "closed_trades": result.get("closed_trades", []),
        }
    except Exception as exc:
        return {
            "ok": False,
            "feature_id": feature_id,
            "category": case.category,
            "title": case.title,
            "stage": "CORE_BACKTEST",
            "parser": "PASS",
            "semantic": "PASS",
            "backtest": "FAIL",
            "fixture": case.fixture,
            "dsl_code": case.dsl_code,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }


@app.post("/api/features/{feature_id}/run")
def run_catalog_feature(feature_id: str):
    result = run_feature_case(feature_id)
    if result.get("feature_id") == feature_id and result.get("stage") == "CATALOG":
        raise HTTPException(status_code=404, detail=result)
    return result


@app.post("/api/features/run-all")
def run_all_catalog_features():
    results = [run_feature_case(feature_id) for feature_id in FEATURE_CASES]
    passed = sum(1 for item in results if item.get("ok"))
    failed = [item for item in results if not item.get("ok")]
    return {
        "ok": not failed,
        "total": len(results),
        "passed": passed,
        "failed": len(failed),
        "failed_feature_ids": [item.get("feature_id") for item in failed],
        "results": results,
    }


LIVE_HTML = r"""<!doctype html>
<html lang='ko'>
<head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Quant DSL Live Studio</title>
<style>
:root{--bg:#090d13;--p:#121923;--p2:#0d131c;--line:#293548;--text:#e8eef7;--muted:#91a2b8;--blue:#4f8cff;--green:#43d17f;--red:#ff6f7d;--amber:#f4b64b}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,sans-serif}.shell{height:100vh;display:grid;grid-template-columns:300px minmax(0,1fr) 420px;grid-template-rows:68px minmax(0,1fr);grid-template-areas:'top top top' 'left main right'}.top{grid-area:top;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 18px;background:#0c1119}.top h2{margin:0;font-size:19px}.meta{color:var(--muted);font-size:11px}.left{grid-area:left;border-right:1px solid var(--line);overflow:auto;background:var(--p2);padding:12px}.main{grid-area:main;overflow:auto;padding:14px}.right{grid-area:right;border-left:1px solid var(--line);padding:14px;overflow:auto;background:var(--p2)}.card{background:var(--p);border:1px solid var(--line);border-radius:13px;padding:13px;margin-bottom:12px}.category{margin:10px 0 4px;color:#b6c5d8;font-weight:800;font-size:11px;text-transform:uppercase}.feature{width:100%;text-align:left;border:1px solid transparent;background:transparent;color:#cbd7e7;border-radius:8px;padding:8px;margin:2px 0;cursor:pointer;font-size:11px}.feature:hover,.feature.active{background:#17243a;border-color:#315383}.feature.pass{border-left:3px solid var(--green)}.feature.fail{border-left:3px solid var(--red)}textarea{width:100%;min-height:400px;background:#070b11;color:#dce8f7;border:1px solid #33445d;border-radius:10px;padding:12px;font:12px/1.5 Consolas,monospace;resize:vertical}button{background:var(--blue);color:white;border:0;border-radius:9px;padding:9px 12px;font-weight:750;cursor:pointer;margin-right:6px}.secondary{background:#26354a}.all{background:#805ad5}.ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}pre{white-space:pre-wrap;overflow:auto;background:#070b11;border-radius:10px;border:1px solid #202b3a;padding:11px;max-height:620px;font-size:11px}.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.metric{padding:9px;background:#0b1119;border:1px solid var(--line);border-radius:9px}.metric b{display:block;font-size:17px}.metric span{font-size:9px;color:var(--muted)}.desc{color:var(--muted);font-size:11px;line-height:1.5}.pill{font-size:10px;padding:5px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}@media(max-width:1100px){.shell{grid-template-columns:250px 1fr;grid-template-areas:'top top' 'left main'}.right{display:none}}
</style></head><body><div class='shell'>
<header class='top'><div><h2>Quant DSL Live Studio · Feature Verification</h2><div class='meta'>등록 기능 → 예제 DSL → Parser/Semantic → 실제 Core BacktestEngine</div></div><div><span class='pill' id='catalog-count'>catalog loading</span> <button class='all' onclick='runAll()'>전체 기능 실행</button></div></header>
<aside class='left'><div class='meta'>카테고리별 DSL 기능</div><div id='features'></div></aside>
<main class='main'><section class='card'><div style='display:flex;justify-content:space-between;gap:10px'><div><h3 id='title' style='margin:0 0 5px'>기능을 선택하세요</h3><div id='description' class='desc'>좌측에서 하나를 선택하면 해당 기능의 실제 실행 예제가 로드됩니다.</div></div><span id='fixture' class='pill'>-</span></div></section><section class='card'><textarea id='dsl'></textarea><p><button class='secondary' onclick='validateDSL()'>현재 DSL 검증</button><button onclick='evaluateDSL()'>현재 DSL Core 백테스트</button><button id='run-feature' onclick='runSelected()'>선택 기능 검증</button></p><div id='status' class='meta'>대기 중</div></section></main>
<aside class='right'><h3>검증 결과</h3><div class='summary'><div class='metric'><b id='total'>-</b><span>전체</span></div><div class='metric'><b id='passed'>-</b><span>PASS</span></div><div class='metric'><b id='failed'>-</b><span>FAIL</span></div></div><p class='desc'>synthetic/intraday fixture는 엔진 기능 계측용입니다. 수익성 또는 실전 데이터 진위를 주장하지 않습니다.</p><pre id='out'>대기 중</pre></aside>
</div><script>
const $=id=>document.getElementById(id);let catalog=null,selected=null,statusById={};
async function getj(url){const r=await fetch(url);const j=await r.json();if(!r.ok)throw j;return j}async function post(url,body={}){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw j;return j}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function render(){const root=$('features');root.innerHTML='';catalog.categories.forEach(cat=>{const h=document.createElement('div');h.className='category';h.textContent=`${cat.category} (${cat.count})`;root.appendChild(h);cat.features.forEach(f=>{const b=document.createElement('button');b.className='feature'+(selected?.feature_id===f.feature_id?' active':'')+(statusById[f.feature_id]?' '+statusById[f.feature_id]:'');b.textContent=f.feature_id;b.onclick=()=>selectFeature(f);root.appendChild(b)})})}
function selectFeature(f){selected=f;$('title').textContent=f.title;$('description').textContent=f.description;$('fixture').textContent=f.fixture;$('dsl').value=f.dsl_code;$('status').className='meta';$('status').textContent='예제 DSL 로드됨 · 아직 실행하지 않음';render()}
async function load(){catalog=await getj('/api/features');$('catalog-count').textContent=`${catalog.count} features`;render();const first=catalog.categories[0]?.features[0];if(first)selectFeature(first)}
async function validateDSL(){try{const j=await post('/api/validate',{dsl_code:$('dsl').value});$('status').className=j.ok?'ok':'bad';$('status').textContent=j.ok?'Parser / Semantic PASS':j.message;$('out').textContent=JSON.stringify(j,null,2)}catch(e){$('status').className='bad';$('out').textContent=JSON.stringify(e,null,2)}}
async function evaluateDSL(){try{const j=await post('/api/evaluate',{dsl_code:$('dsl').value,bars_count:300});$('status').className='ok';$('status').textContent='현재 DSL 실제 Core BacktestEngine PASS';$('out').textContent=JSON.stringify({evaluation:j.evaluation,strategy:j.strategy,metrics:j.metrics_numeric,diagnostics:j.diagnostics,closed_trades:j.closed_trades},null,2)}catch(e){$('status').className='bad';$('status').textContent='Core Backtest FAIL';$('out').textContent=JSON.stringify(e,null,2)}}
async function runSelected(){if(!selected)return;const j=await post(`/api/features/${encodeURIComponent(selected.feature_id)}/run`);statusById[selected.feature_id]=j.ok?'pass':'fail';$('status').className=j.ok?'ok':'bad';$('status').textContent=j.ok?'기능 전체 경로 PASS':`FAIL @ ${j.stage}`;$('out').textContent=JSON.stringify(j,null,2);render()}
async function runAll(){$('status').className='warn';$('status').textContent='전체 기능 실행 중...';const j=await post('/api/features/run-all');$('total').textContent=j.total;$('passed').textContent=j.passed;$('failed').textContent=j.failed;j.results.forEach(x=>statusById[x.feature_id]=x.ok?'pass':'fail');$('status').className=j.ok?'ok':'bad';$('status').textContent=j.ok?'전체 DSL 기능 PASS':`${j.failed}개 기능 실패 · 실패 항목을 좌측에서 확인`;$('out').textContent=JSON.stringify({ok:j.ok,total:j.total,passed:j.passed,failed:j.failed,failed_feature_ids:j.failed_feature_ids,failures:j.results.filter(x=>!x.ok)},null,2);render()}
load().catch(e=>{$('out').textContent=JSON.stringify(e,null,2)});
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return LIVE_HTML


if __name__ == "__main__":
    uvicorn.run("live_studio_main:app", host="127.0.0.1", port=8010, reload=False)
