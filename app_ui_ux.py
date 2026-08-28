"""UX-max alternate frontend for the existing local Quant DSL Studio.

Legacy app_ui.py and its root UI remain untouched. This module adds /ux plus a
UX-only deterministic DSL validation endpoint. Natural-language composition is
human-mediated by design: idea -> LLM request prompt -> human relay -> pasted
LLM result -> local DSL validation -> backtest.
"""
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from app_ui import app
from core.dsl_parser import DSLParser, DSLParseError
from core.dsl_semantic import DSLSemanticAnalyzer, DSLSemanticError


class UXValidateRequest(BaseModel):
    dsl_code: str


@app.post("/api/ux/validate", include_in_schema=False)
def ux_validate(req: UXValidateRequest):
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
    except (DSLParseError, DSLSemanticError) as exc:
        return {
            "ok": False,
            "parser": "FAIL" if isinstance(exc, DSLParseError) else "PASS",
            "semantic": "FAIL" if isinstance(exc, DSLSemanticError) else "NOT_RUN",
            "error": str(exc),
            "code": getattr(exc, "code", "DSL_ERROR"),
            "line": getattr(exc, "line", 1),
            "column": getattr(exc, "column", 1),
        }


UX_HTML = r'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quant DSL Studio · Human LLM UX</title>
<script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
<style>
:root{--bg:#090c12;--p:#111722;--p2:#161e2b;--line:#283348;--text:#eef3f8;--muted:#8fa0b8;--blue:#4f8cff;--green:#29c58b;--amber:#f2b84b;--red:#f06a76}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:13px Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,textarea,select{font:inherit}.shell{height:100vh;display:grid;grid-template-columns:250px 1fr;grid-template-rows:58px 1fr;grid-template-areas:"top top" "side main"}.top{grid-area:top;border-bottom:1px solid var(--line);background:#0d131d;display:flex;align-items:center;justify-content:space-between;padding:0 16px}.brand{font-weight:800}.brand small{display:block;color:var(--muted);font-weight:500;margin-top:2px}.side{grid-area:side;border-right:1px solid var(--line);background:#0d131d;overflow:auto;padding:12px}.main{grid-area:main;overflow:auto;padding:14px}.btn{border:1px solid var(--line);background:var(--p2);color:var(--text);border-radius:9px;padding:8px 11px;cursor:pointer;font-weight:700}.btn.primary{background:var(--blue);border-color:transparent}.btn.success{background:var(--green);border-color:transparent;color:#07130f}.btn.warn{background:#47391b;border-color:#735b25}.btn:disabled{opacity:.38;cursor:not-allowed}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.card{border:1px solid var(--line);background:var(--p);border-radius:12px;margin-bottom:12px}.pad{padding:14px}.title{font-size:15px;font-weight:800}.sub{color:var(--muted);font-size:11px;line-height:1.5}.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:12px}.step{border:1px solid var(--line);border-radius:10px;padding:9px;background:#0d141f}.step b{display:block;font-size:11px}.step span{font-size:9px;color:var(--muted)}.step.done{border-color:#275d49;background:#10251e}.step.active{border-color:#486da9;background:#17263d}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}.label{font-size:10px;color:var(--muted);margin-bottom:5px}.ta,input{width:100%;background:#080d14;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:10px;outline:none}.ta{min-height:150px;resize:vertical;font:12px/1.5 Consolas,monospace}.idea{font-family:inherit;min-height:120px}.llm-box{min-height:210px}.dsl{min-height:280px}.mode{padding:6px 9px;border-radius:999px}.mode.active{background:#1b3153;border-color:#476ea9}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:9px;flex-wrap:wrap}.status{padding:7px 10px;border-radius:999px;border:1px solid var(--line);font-size:10px;color:var(--muted)}.status.ok{color:#9be7c8;border-color:#275d49}.status.bad{color:#ffadb5;border-color:#69353d}.work{display:grid;grid-template-columns:1.25fr .75fr;gap:12px}.chart{height:420px;position:relative}.chart>div{width:100%;height:100%}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px}.metric{border:1px solid var(--line);border-radius:9px;padding:10px;background:#0c121b}.metric small{color:var(--muted)}.metric strong{display:block;margin-top:5px;font-size:15px}.console{white-space:pre-wrap;background:#070b11;border:1px solid var(--line);border-radius:9px;padding:10px;min-height:120px;font:10px/1.45 Consolas;color:#9aabc1}.strategy{padding:9px;border:1px solid transparent;border-radius:8px;cursor:pointer}.strategy:hover{background:var(--p)}.strategy.active{border-color:#355b92;background:#16243a}.strategy small{display:block;color:var(--muted);margin-top:3px}.search{margin:8px 0}.hr{height:1px;background:var(--line);margin:10px 0}.note{border-left:3px solid var(--amber);padding:8px 10px;background:#211b0e;color:#d9c89e;border-radius:6px;font-size:10px;line-height:1.45}@media(max-width:1000px){.shell{display:block;height:auto}.side{display:none}.grid2,.work{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.chart{height:340px}}
</style></head><body>
<div class="shell">
<header class="top"><div class="brand">Quant DSL Studio<small>Human-mediated LLM → deterministic local DSL</small></div><div class="row"><a href="/" style="color:#9fc0ff">기존 UI</a><span class="status">Core deterministic</span></div></header>
<aside class="side"><div class="title">내 전략</div><input id="search" class="search" placeholder="전략 검색" oninput="renderStrategies()"/><div class="row"><button class="btn primary" onclick="newStrategy()">+ 새 전략</button><button class="btn" onclick="loadStrategies()">↻</button></div><div class="hr"></div><div id="list"></div></aside>
<main class="main">
<section class="card pad"><div class="title">자연어 → LLM → 로컬 DSL</div><div class="sub">자연어를 앱이 곧바로 DSL로 합성하지 않습니다. 앱은 LLM에 보낼 요청 프롬프트를 만들고, 사용자가 직접 LLM에 전달한 뒤 결과를 다시 붙여넣습니다.</div>
<div class="steps"><div id="st1" class="step active"><b>1. 자연어 입력</b><span>전략 의도 작성</span></div><div id="st2" class="step"><b>2. LLM 요청 생성</b><span>복사 가능한 프롬프트</span></div><div id="st3" class="step"><b>3. 인간 매개</b><span>외부 LLM 전달/회수</span></div><div id="st4" class="step"><b>4. 로컬 DSL 검증</b><span>Parser + Semantic</span></div><div id="st5" class="step"><b>5. 백테스트</b><span>검증 성공 후 실행</span></div></div>
<div class="grid2"><div><div class="label">1) 자연어 전략 설명</div><textarea id="idea" class="ta idea" placeholder="예: 5일선이 20일선을 상향 돌파하고 RSI가 30 이하일 때 매수, 데드크로스 발생 시 전량 청산..."></textarea><div class="toolbar"><div class="row"><button class="btn" onclick="quick('5일선이 20일선을 상향 돌파하고 RSI 60 미만일 때 진입, 하향 돌파 시 청산')">이평 돌파</button><button class="btn" onclick="quick('RSI 30 이하 진입, RSI 70 이상 청산')">RSI 반전</button></div><button class="btn primary" onclick="buildPrompt()">LLM 요청 프롬프트 생성 →</button></div></div>
<div><div class="label">2) 외부 LLM에 보낼 요청 프롬프트</div><textarea id="llmPrompt" class="ta llm-box" readonly></textarea><div class="toolbar"><span class="sub">복사 후 ChatGPT/Gemini 등 원하는 LLM에 직접 전달</span><button class="btn" onclick="copyText('llmPrompt')">프롬프트 복사</button></div></div></div>
<div class="grid2"><div><div class="label">3) LLM 결과 붙여넣기</div><textarea id="llmResult" class="ta llm-box" placeholder="LLM이 반환한 로컬 DSL 결과를 그대로 붙여넣으세요. ```dsl 코드펜스가 있어도 제거합니다."></textarea><div class="toolbar"><span class="sub">외부 LLM 호출은 이 앱이 자동으로 수행하지 않습니다.</span><button class="btn warn" onclick="admitLLMResult()">로컬 DSL로 가져오기 →</button></div></div>
<div><div class="label">4) 실행 대상 로컬 DSL</div><textarea id="dsl" class="ta dsl" spellcheck="false"></textarea><div class="toolbar"><span id="validation" class="status">미검증</span><div class="row"><button class="btn" onclick="copyText('dsl')">DSL 복사</button><button class="btn primary" onclick="validateDSL()">Parser/Semantic 검증</button></div></div></div></div>
<div class="grid2"><div><div class="label">전략 이름</div><input id="name" placeholder="전략 이름"/></div><div><div class="label">설명</div><input id="desc" placeholder="전략 설명"/></div></div><div class="toolbar"><div class="note">LLM 출력은 실행 권한이 아닙니다. 로컬 DSL Parser/Semantic 검증을 통과한 텍스트만 백테스트 단계로 넘어갑니다.</div><div class="row"><button class="btn" onclick="saveStrategy()">저장</button><button id="runBtn" class="btn success" onclick="runBacktest()" disabled>검증 성공 후 백테스트</button></div></div></section>
<section class="work"><div class="card"><div class="pad title">백테스트 차트</div><div class="chart"><div id="chart"></div></div></div><div class="card pad"><div class="title">결과</div><div class="metrics"><div class="metric"><small>총 수익률</small><strong id="mret">-</strong></div><div class="metric"><small>MDD</small><strong id="mmdd">-</strong></div><div class="metric"><small>승률</small><strong id="mwin">-</strong></div><div class="metric"><small>거래 횟수</small><strong id="mtr">-</strong></div></div><div class="label" style="margin-top:12px">로그</div><div id="log" class="console">준비 완료.</div></div></section>
</main></div>
<script>
let strategies=[],currentId=null,validated=false,chart,candle,ma5,ma20,bbU,bbL;const $=id=>document.getElementById(id);
function writeLog(s){$('log').textContent=`${new Date().toLocaleTimeString()} ${s}\n`+$('log').textContent}
function step(n){for(let i=1;i<=5;i++){const e=$('st'+i);e.classList.toggle('done',i<n);e.classList.toggle('active',i===n)}}
function quick(t){$('idea').value=t;step(1)}
function buildPrompt(){const idea=$('idea').value.trim();if(!idea)return alert('자연어 전략 설명을 먼저 입력하세요.');const name=$('name').value.trim()||'LLM_Strategy';$('llmPrompt').value=`당신은 Quant DSL 2.0 전략 작성기입니다.\n\n사용자 전략 의도:\n${idea}\n\n요구사항:\n1. 아래 의도를 실행 가능한 로컬 DSL로만 변환하세요.\n2. 결과는 반드시 strategy "${name}" { ... } 형식이어야 합니다.\n3. 허용된 ta.* 함수와 order.* 명령만 사용하고 새로운 문법을 만들지 마세요.\n4. 설명문, 마크다운 표, 해설은 출력하지 말고 DSL 코드만 출력하세요.\n5. 불명확한 조건은 임의로 학습/추론 권한을 만들지 말고 보수적인 명시 조건으로 표현하세요.\n6. LLM은 주문 실행 권한이 없으며, 출력은 이후 로컬 Parser/Semantic 검증을 받아야 합니다.\n\n로컬 DSL만 출력하세요.`;step(2);writeLog('LLM 요청 프롬프트 생성')}
async function copyText(id){const t=$(id).value;await navigator.clipboard?.writeText(t);writeLog(`${id} 복사`);if(id==='llmPrompt')step(3)}
function stripFence(s){s=s.trim();const m=s.match(/^```(?:dsl|text)?\s*([\s\S]*?)\s*```$/i);return m?m[1].trim():s}
function admitLLMResult(){const s=stripFence($('llmResult').value);if(!s)return alert('LLM 결과를 붙여넣으세요.');$('dsl').value=s;validated=false;$('runBtn').disabled=true;$('validation').className='status';$('validation').textContent='미검증';step(4);writeLog('LLM 결과를 로컬 DSL 후보로 가져옴')}
async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opt});const d=await r.json();if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`);return d}
async function validateDSL(){const dsl=$('dsl').value.trim();if(!dsl)return alert('DSL이 없습니다.');const r=await api('/api/ux/validate',{method:'POST',body:JSON.stringify({dsl_code:dsl})});validated=!!r.ok;$('runBtn').disabled=!validated;$('validation').className='status '+(validated?'ok':'bad');$('validation').textContent=validated?`Parser PASS · Semantic PASS`:`${r.code||'DSL_ERROR'} · line ${r.line||1}`;writeLog(validated?'DSL 검증 PASS':`DSL 검증 FAIL: ${r.error||''}`);if(validated)step(5)}
function ensureChart(){if(chart)return;chart=LightweightCharts.createChart($('chart'),{autoSize:true,layout:{background:{color:'#0b1018'},textColor:'#8796aa'},grid:{vertLines:{color:'#182130'},horzLines:{color:'#182130'}}});candle=chart.addCandlestickSeries({upColor:'#29c58b',downColor:'#f06a76',borderVisible:false,wickUpColor:'#29c58b',wickDownColor:'#f06a76'});ma5=chart.addLineSeries({color:'#4f8cff',lineWidth:2});ma20=chart.addLineSeries({color:'#f2b84b',lineWidth:2});bbU=chart.addLineSeries({color:'#9d78ff',lineWidth:1,lineStyle:2});bbL=chart.addLineSeries({color:'#9d78ff',lineWidth:1,lineStyle:2})}
async function runBacktest(){if(!validated)return alert('먼저 Parser/Semantic 검증을 통과해야 합니다.');const r=await api('/api/backtest',{method:'POST',body:JSON.stringify({dsl_code:$('dsl').value})});ensureChart();candle.setData(r.candles||[]);ma5.setData(r.ma5||[]);ma20.setData(r.ma20||[]);bbU.setData(r.bb_upper||[]);bbL.setData(r.bb_lower||[]);if(r.markers&&candle.setMarkers)candle.setMarkers(r.markers);chart.timeScale().fitContent();const m=r.metrics||{};$('mret').textContent=m.total_return||'-';$('mmdd').textContent=m.mdd||'-';$('mwin').textContent=m.win_rate||'-';$('mtr').textContent=m.trade_count||'-';writeLog(`백테스트 완료 · ${m.engine_mode||''}`)}
async function loadStrategies(){strategies=await api('/api/strategies');renderStrategies()}
function renderStrategies(){const q=$('search').value.toLowerCase(),box=$('list');box.innerHTML='';strategies.filter(s=>!q||(`${s.name} ${s.description||''}`).toLowerCase().includes(q)).forEach(s=>{const e=document.createElement('div');e.className='strategy'+(s.id===currentId?' active':'');e.innerHTML=`<b>${s.name}</b><small>${s.description||'설명 없음'}</small>`;e.onclick=()=>{currentId=s.id;$('name').value=s.name||'';$('desc').value=s.description||'';$('dsl').value=s.dsl_code||'';validated=false;$('runBtn').disabled=true;$('validation').textContent='미검증';renderStrategies();step(4)};box.appendChild(e)})}
function newStrategy(){currentId=null;['idea','llmPrompt','llmResult','dsl','name','desc'].forEach(id=>$(id).value='');validated=false;$('runBtn').disabled=true;$('validation').textContent='미검증';renderStrategies();step(1)}
async function saveStrategy(){const name=$('name').value.trim(),dsl=$('dsl').value.trim();if(!name||!dsl)return alert('전략 이름과 DSL이 필요합니다.');const p={name,description:$('desc').value.trim(),dsl_code:dsl,source_type:'HUMAN_LLM'};if(currentId)await api(`/api/strategies/${currentId}`,{method:'PUT',body:JSON.stringify(p)});else{const r=await api('/api/strategies',{method:'POST',body:JSON.stringify(p)});currentId=r.id}await loadStrategies();writeLog('전략 저장 완료')}
$('dsl').addEventListener('input',()=>{validated=false;$('runBtn').disabled=true;$('validation').className='status';$('validation').textContent='수정됨 · 재검증 필요'});loadStrategies();
</script></body></html>'''


@app.get("/ux", response_class=HTMLResponse, include_in_schema=False)
def ux_index():
    return UX_HTML


if __name__ == "__main__":
    uvicorn.run("app_ui_ux:app", host="127.0.0.1", port=8000, reload=False)
