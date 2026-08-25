"""
Main Entry Point - Assembles Core Modules and UI View
"""

import os
import json
import re
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# 90% 불변 코어 모듈 임포트
from core.db import (init_db, get_all_strategies, insert_strategy, update_strategy, delete_strategy,
                     get_categories, create_category, update_category, delete_category,
                     commit_artifact, get_artifact_versions, record_validation)
from core.transpiler import CodeTranspiler
from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntimeError
from core.kiwoom_rest import ENV_PATH, KiwoomAPIError, KiwoomRESTClient
from core.transpiler import TranspileError

# 10% 가변 프롬프트 모듈 임포트
from core.prompt_template import generate_full_llm_prompt, playbook_hash, playbook_text
from core.capabilities import DSL_VERSION, ARTIFACT_TYPES

# DB 초기화
init_db()

app = FastAPI(title="Enterprise Quant DSL Studio")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "core", "static")), name="static")

class StrategyModel(BaseModel):
    name: str
    description: Optional[str] = ""
    dsl_code: str
    source_code: Optional[str] = ""
    source_type: Optional[str] = "DSL"

class TranspileRequest(BaseModel):
    source_type: str
    source_code: str
    name: Optional[str] = "Converted_Strategy"

class SourceValidateRequest(BaseModel):
    source_type: str = "DSL"
    source_code: str
    name: str = "Validated_Strategy"

class PromptRequest(BaseModel):
    requirement: str

class BacktestRequest(BaseModel):
    dsl_code: str
    data_source: str = "synthetic"
    symbol: str = "005930"
    timeframe: str = "1d"
    settings: Dict[str, Any] = Field(default_factory=dict)

class CategoryModel(BaseModel):
    name: str
    artifact_type: str = "strategy"
    parent_id: Optional[int] = None

class PromptPackageRequest(BaseModel):
    artifact_id: Optional[int] = None
    artifact_type: str = "strategy"
    user_request: str
    current_dsl: str = ""
    source_type: str = "NATURAL_LANGUAGE"
    source_code: str = ""
    previous_error: str = ""

class ValidateChartRequest(PromptPackageRequest):
    llm_response: str
    prompt_text: str = ""
    data_source: str = "synthetic"
    symbol: str = "005930"
    timeframe: str = "1d"
    settings: Dict[str, Any] = Field(default_factory=dict)

class CommitArtifactRequest(BaseModel):
    artifact_id: Optional[int] = None
    name: str
    description: str = ""
    category_id: int
    artifact_type: str
    source_type: str = "NATURAL_LANGUAGE"
    source_code: str = ""
    user_request: str = ""
    prompt_text: str = ""
    llm_response: str = ""
    dsl_code: str
    validation: Dict[str, Any] = Field(default_factory=dict)

# -----------------------------------------------------------------------------
# REST API 라우터
# -----------------------------------------------------------------------------
@app.get("/api/strategies")
def read_strategies():
    return get_all_strategies()

@app.post("/api/strategies")
def create_strategy(item: StrategyModel):
    try:
        new_id = insert_strategy(item.name, item.description, item.dsl_code, item.source_type, item.source_code)
        return {"id": new_id, "message": "전략 등록 완료"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/strategies/{strat_id}")
def edit_strategy(strat_id: int, item: StrategyModel):
    update_strategy(strat_id, item.name, item.description, item.dsl_code, item.source_type, item.source_code)
    return {"message": "전략 수정 완료"}

@app.delete("/api/strategies/{strat_id}")
def remove_strategy(strat_id: int):
    delete_strategy(strat_id)
    return {"message": "전략 삭제 완료"}

@app.get("/api/tree")
def artifact_tree():
    return {"categories": get_categories(), "artifacts": get_all_strategies(), "types": ARTIFACT_TYPES}

@app.post("/api/categories")
def add_category(item: CategoryModel):
    try: return {"id": create_category(item.name, item.artifact_type, item.parent_id)}
    except Exception as exc: raise HTTPException(status_code=400, detail=str(exc))

@app.put("/api/categories/{category_id}")
def edit_category(category_id: int, item: CategoryModel):
    try: update_category(category_id,item.name,item.artifact_type,item.parent_id); return {"status":"success"}
    except Exception as exc: raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/api/categories/{category_id}")
def remove_category(category_id: int):
    try: delete_category(category_id); return {"status":"success"}
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

@app.get("/api/artifacts/{artifact_id}/versions")
def artifact_versions(artifact_id: int): return get_artifact_versions(artifact_id)

def extract_dsl(response: str) -> str:
    blocks=re.findall(r"```(?:dsl|local-dsl)?[ \t]*\r?\n(.*?)```",response,flags=re.I|re.S)
    candidates=blocks or [response]
    for candidate in candidates:
        start=re.search(r'''strategy\s+["'][^"']+["']\s*\{''',candidate)
        if start:
            text=candidate[start.start():].strip()
            depth=0
            for index,char in enumerate(text):
                if char=="{": depth+=1
                elif char=="}":
                    depth-=1
                    if depth==0:
                        extracted=text[:index+1]
                        return re.sub(r"(?m)^\s*```[^\r\n]*\s*$", "", extracted).strip()
            return re.sub(r"(?m)^\s*```[^\r\n]*\s*$", "", text).strip()
    raise ValueError("LLM 응답에서 완전한 strategy DSL 코드 블록을 찾지 못했습니다.")

def diagnostic(exc: Exception, dsl: str, stage: str) -> Dict[str, Any]:
    message=str(exc); line=column=None; expression=""
    match=re.search(r"(?:line|행)\s*(\d+)(?:[^\d]+(?:column|열)\s*(\d+))?",message,re.I)
    if match:
        line=int(match.group(1)); column=int(match.group(2)) if match.group(2) else None
        lines=dsl.splitlines(); expression=lines[line-1].strip() if 0<line<=len(lines) else ""
    return {"stage":stage,"error_code":type(exc).__name__.upper(),"message":message,
            "line":line,"column":column,"expression":expression,"dsl_version":DSL_VERSION}

def analyze_strategy_result(result: Dict[str, Any], evaluation_context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    """Build strategy-agnostic evidence for the next improvement iteration.

    This layer deliberately does not infer trading semantics (breakout, trend,
    mean reversion, etc.).  Those semantics belong to the supplied requirement
    and DSL, not to a generic performance reporter.
    """
    metrics=result["metrics"];counts=result.get("diagnostics",{}).get("signal_counts",{})
    number=lambda value:float(re.sub(r"[^0-9+\-.]","",str(value)) or 0)
    total_return=number(metrics.get("total_return",0));mdd=abs(number(metrics.get("mdd",0)))
    trades=int(number(metrics.get("trade_count",0)));closed=int(number(metrics.get("closed_trade_count",0)))
    win_rate=number(metrics.get("win_rate",0));ratio=total_return/mdd if mdd else (999.0 if total_return>0 else 0.0)
    issues=[];priorities=[]
    meaningful=[(name,value) for name,value in counts.items() if not name.startswith("__") and name not in {"short_entry","short_exit"}]
    first_zero=next((name for name,value in meaningful if value==0),None)
    if trades==0:
        issues.append(f"진입 거래가 0회입니다. 최초 0회 신호 단계: {first_zero or 'long_entry'}")
        priorities.append("신호 퍼널에서 최초로 0이 되는 지점을 현재 DSL의 선언 순서와 조건식으로 추적하세요.")
    elif closed<30:
        issues.append(f"청산 거래가 {closed}회뿐이라 성과 일반화 여부를 판단하기 어렵습니다.")
        priorities.append("성과 개선 주장보다 표본 부족을 먼저 다루고, 신호 손실 구간과 체결되지 않은 조건을 진단하세요.")
    if total_return<=0:
        issues.append(f"총수익률이 {total_return:+.2f}%로 양수가 아닙니다.")
        priorities.append("현재 DSL에서 손실을 만드는 진입·보유·청산 가설을 구분하고 가장 큰 한 가지 병목만 수정하세요.")
    if mdd and ratio<1.5:
        issues.append(f"수익률/MDD가 {ratio:.2f}로 위험 대비 성과가 낮습니다.")
        priorities.append("총수익률과 낙폭을 함께 평가하고 수익률만 높이는 변경을 개선으로 간주하지 마세요.")
    if trades and win_rate<40:
        issues.append(f"승률이 {win_rate:.1f}%로 낮습니다.")
        priorities.append("승률만으로 조건을 추가하지 말고 손익비와 거래 수 변화까지 함께 검증하세요.")
    if not issues:issues.append("현재 표본에서는 즉시 드러나는 치명적 병목이 없습니다.")
    return {
        "schema":"strategy_agnostic_evidence/v1",
        "verdict":"needs_improvement" if priorities else "promising",
        "evidence_quality":"insufficient" if closed < 30 else "provisional",
        "issues":issues,
        "diagnostic_priorities":priorities,
        "metrics":metrics,
        "signal_counts":counts,
        "signal_count_semantics":"각 변수의 독립적인 true 봉 수이며, 선언 순서만으로 순차 전환 퍼널이라고 단정하지 않는다.",
        "evaluation_context":evaluation_context or {
            "bars":result.get("diagnostics",{}).get("bars"),
            "execution_settings":result.get("settings",{})
        },
        "derived":{"return_to_mdd":round(ratio,3),"closed_trades":closed},
        "improvement_contract":[
            "전략 유형과 의도는 사용자 요청과 현재 DSL에서만 추론한다.",
            "지표·전략 이름에 특화된 규칙을 일반 규칙처럼 적용하지 않는다.",
            "관측된 증거로 설명 가능한 단일 병목 가설을 세우고 최소 변경한다.",
            "기간·임계값의 표본 맞춤 탐색보다 구조·상태·체결 의미 오류를 먼저 점검한다.",
            "기존 의도, 미래참조 금지, 지원 Capability 범위를 보존한다.",
            "변경 전후 신호 수·거래 수·수익률·MDD의 예상 영향을 DSL 변수 기준으로 설명 가능해야 한다."
        ],
        "warning":"이 자료는 전략별 처방이 아니라 관측 증거입니다. 동일 표본 성과만으로 개선을 확정하지 마세요."
    }

def load_market(data_source: str, symbol: str, timeframe: str):
    if data_source=="synthetic": return None
    if data_source=="kiwoom":
        client=KiwoomRESTClient(); return client.normalize_chart(client.chart(symbol,timeframe))
    raise ValueError("data_source는 synthetic 또는 kiwoom이어야 합니다.")

@app.post("/api/llm/prompt")
def build_llm_prompt(req: PromptPackageRequest):
    prompt=generate_full_llm_prompt(req.user_request,artifact_type=req.artifact_type,
        current_dsl=req.current_dsl,source_type=req.source_type,source_code=req.source_code,
        validation_error=req.previous_error or None)
    return {"prompt":prompt,"playbook_version":DSL_VERSION,"playbook_hash":playbook_hash()}

@app.post("/api/llm/validate-chart")
def validate_llm_chart(req: ValidateChartRequest):
    extracted=""; status="failed"; diag={}
    try:
        extracted=extract_dsl(req.llm_response)
        market=load_market(req.data_source,req.symbol,req.timeframe)
        result=BacktestEngine.run(extracted,settings=req.settings,market=market)
        status="validated"
        analysis=analyze_strategy_result(result, {
            "data_source":req.data_source,
            "symbol":req.symbol,
            "timeframe":req.timeframe,
            "bars":result.get("diagnostics",{}).get("bars"),
            "execution_settings":result.get("settings",{})
        })
        diag={"stage":"complete","message":"DSL 검증과 차트 삽입 데이터 생성에 성공했습니다.",
              "indicator_count":len(result["indicators"]),"trade_count":len(result["trades"]),
              "bars":result["diagnostics"]["bars"],"signal_counts":result["diagnostics"]["signal_counts"],
              "strategy_analysis":analysis}
        event_id=record_validation(artifact_id=req.artifact_id,artifact_type=req.artifact_type,
            user_request=req.user_request,prompt_text=req.prompt_text,llm_response=req.llm_response,extracted_dsl=extracted,status=status,
            diagnostic_json=json.dumps(diag,ensure_ascii=False),playbook_version=DSL_VERSION,playbook_hash=playbook_hash())
        return {"status":status,"valid":True,"dsl_code":extracted,"diagnostic":diag,"analysis":analysis,
                "event_id":event_id,"playbook_version":DSL_VERSION,"playbook_hash":playbook_hash(),"chart":result}
    except KiwoomAPIError as exc:
        diag={"stage":"market_data","error_code":"KIWOOM_CONNECTION_ERROR","message":str(exc),
              "line":None,"column":None,"expression":"","dsl_version":DSL_VERSION,
              "hint":"키움 REST 연결 상태와 .env의 KIWOOM_ENV/API 키 및 Windows 네트워크 권한을 확인하세요. DSL 수정 대상이 아닙니다."}
        event_id=record_validation(artifact_id=req.artifact_id,artifact_type=req.artifact_type,
            user_request=req.user_request,prompt_text=req.prompt_text,llm_response=req.llm_response,
            extracted_dsl=extracted,status="data_error",diagnostic_json=json.dumps(diag,ensure_ascii=False),
            playbook_version=DSL_VERSION,playbook_hash=playbook_hash())
        return {"status":"data_error","valid":False,"dsl_code":extracted,"diagnostic":diag,
                "repair_prompt":"","event_id":event_id,"playbook_version":DSL_VERSION,"playbook_hash":playbook_hash()}
    except Exception as exc:
        stage="extractor" if not extracted else ("runtime" if isinstance(exc,(DSLRuntimeError,ValueError)) else "backtest")
        diag=diagnostic(exc,extracted,stage)
        repair=generate_full_llm_prompt(req.user_request,artifact_type=req.artifact_type,current_dsl=req.current_dsl,
            source_type=req.source_type,source_code=req.source_code,validation_error=json.dumps(diag,ensure_ascii=False)+"\n실패 DSL:\n"+extracted)
        event_id=record_validation(artifact_id=req.artifact_id,artifact_type=req.artifact_type,
            user_request=req.user_request,prompt_text=req.prompt_text,llm_response=req.llm_response,extracted_dsl=extracted,status=status,
            diagnostic_json=json.dumps(diag,ensure_ascii=False),playbook_version=DSL_VERSION,playbook_hash=playbook_hash())
        return {"status":"failed","valid":False,"dsl_code":extracted,"diagnostic":diag,
                "repair_prompt":repair,"event_id":event_id,"playbook_version":DSL_VERSION,"playbook_hash":playbook_hash()}

@app.post("/api/artifacts/commit")
def save_artifact(req: CommitArtifactRequest):
    try:
        # Commit is a second safety gate; client-side preview status is never trusted.
        BacktestEngine.run(req.dsl_code)
        value=commit_artifact(req.artifact_id,name=req.name,description=req.description,category_id=req.category_id,
            artifact_type=req.artifact_type,source_type=req.source_type,source_code=req.source_code,
            dsl_code=req.dsl_code,user_request=req.user_request,prompt_text=req.prompt_text,llm_response=req.llm_response,
            validation_json=json.dumps(req.validation,ensure_ascii=False),playbook_version=DSL_VERSION,
            playbook_hash=playbook_hash())
        return {"id":value,"status":"saved","playbook_version":DSL_VERSION,"playbook_hash":playbook_hash()}
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@app.get("/api/playbook")
def official_playbook(): return {"version":DSL_VERSION,"hash":playbook_hash(),"content":playbook_text()}

@app.get("/api/playbook/issues")
def playbook_issues():
    """Operational failures retained for curated Playbook improvements."""
    import sqlite3
    from core.db import DB_PATH
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row
    rows=conn.execute("""SELECT id,artifact_type,user_request,status,diagnostic_json,playbook_version,
                         playbook_hash,created_at FROM validation_events WHERE status='failed'
                         ORDER BY id DESC LIMIT 200""").fetchall(); conn.close()
    return [dict(row) for row in rows]

@app.post("/api/transpile")
def transpile(req: TranspileRequest):
    try:
        if req.source_type == "KIWOOM":
            dsl = CodeTranspiler.from_kiwoom(req.source_code, req.name)
        elif req.source_type == "PINESCRIPT":
            dsl = CodeTranspiler.from_pinescript(req.source_code)
        else:
            raise HTTPException(status_code=400, detail="알 수 없는 소스 타입")
        return {"dsl_code": dsl, "status": "success"}
    except TranspileError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

def convert_source(source_type: str, source_code: str, name: str) -> Dict[str, Any]:
    kind = source_type.strip().upper()
    if not source_code.strip():
        raise ValueError("소스 코드가 비어 있습니다.")
    if kind in {"DSL", "OTHER"}:
        return {"dsl_code": source_code, "prompt": None, "stage": "converted"}
    if kind == "KIWOOM":
        return {"dsl_code": CodeTranspiler.from_kiwoom(source_code, name), "prompt": None, "stage": "converted"}
    if kind == "PINESCRIPT":
        return {"dsl_code": CodeTranspiler.from_pinescript(source_code), "prompt": None, "stage": "converted"}
    if kind in {"PROMPT", "LLM"}:
        return {"dsl_code": "", "prompt": generate_full_llm_prompt(source_code), "stage": "llm_required"}
    raise ValueError(f"지원하지 않는 소스 형식입니다: {source_type}")

@app.post("/api/source/validate")
def validate_source(req: SourceValidateRequest):
    try:
        converted = convert_source(req.source_type, req.source_code, req.name)
        if converted["stage"] == "llm_required":
            return {"status": "llm_required", "valid": False, **converted,
                    "message": "LLM 프롬프트가 생성되었습니다. 반환된 DSL을 로컬 DSL 형식으로 다시 검증하세요."}
        preview = BacktestEngine.run(converted["dsl_code"])
        return {"status": "success", "valid": True, **converted,
                "message": "변환 및 DSL 실행 검증에 성공했습니다.",
                "strategy": preview["strategy"], "indicator_count": len(preview["indicators"])}
    except (TranspileError, DSLRuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.post("/api/generate-prompt")
def generate_prompt(req: PromptRequest):
    prompt_text = generate_full_llm_prompt(req.requirement)
    return {"prompt": prompt_text}

@app.post("/api/backtest")
def run_backtest(payload: BacktestRequest):
    try:
        market = None
        if payload.data_source == "kiwoom":
            client = KiwoomRESTClient()
            market = client.normalize_chart(client.chart(payload.symbol, payload.timeframe))
        elif payload.data_source != "synthetic":
            raise HTTPException(status_code=400, detail="data_source는 synthetic 또는 kiwoom이어야 합니다.")
        return BacktestEngine.run(payload.dsl_code, settings=payload.settings, market=market)
    except (DSLRuntimeError, KiwoomAPIError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/kiwoom/status")
def kiwoom_status():
    config = KiwoomRESTClient().config
    return {"configured": bool(config.app_key and config.secret_key),
            "environment": "mock" if config.mock else "live", "dotenv_loaded": ENV_PATH.is_file(),
            "live_orders_enabled": False}

@app.get("/api/kiwoom/connectivity")
def kiwoom_connectivity():
    client = KiwoomRESTClient()
    result = {"environment": "mock" if client.config.mock else "live",
              "rest": {"connected": False}, "wss": {"connected": False}}
    try:
        token = client.authenticate()
        result["rest"] = {"connected": True, "message": token.get("return_msg", "OAuth 성공")}
    except Exception as exc:
        result["rest"]["message"] = str(exc)
        return result
    try:
        result["wss"] = client.test_websocket_login()
    except Exception as exc:
        result["wss"]["message"] = str(exc)
    return result

@app.get("/api/kiwoom/functions")
def kiwoom_functions():
    from core.transpiler import FUNCTION_MAP
    approximate = {"jma"}
    return {"count": len(FUNCTION_MAP), "functions": [
        {"kiwoom": name, "dsl": target, "compatibility": "approximate" if name in approximate else "implemented"}
        for name, target in sorted(FUNCTION_MAP.items())
    ]}

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    template_path = os.path.join(os.path.dirname(__file__), "core", "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    print("=== [Enterprise Quant DSL Studio Server Started] ===")
    print("Dashboard: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
