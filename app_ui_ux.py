"""UX-max alternate frontend for the existing local Quant DSL Studio.

This module intentionally reuses the legacy FastAPI app and APIs from app_ui.py.
The legacy root (/) remains untouched; the new experience is exposed at /ux.
"""
from fastapi.responses import HTMLResponse
import uvicorn

from app_ui import app


UX_HTML = r'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Quant DSL Studio · UX</title>
<script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
<style>
:root{
  --bg:#090c12;--panel:#111722;--panel2:#151d2a;--panel3:#0d131d;--line:#273244;
  --text:#edf2f7;--muted:#8ea0b8;--blue:#4f8cff;--green:#28c58b;--red:#f1606d;
  --purple:#9d78ff;--amber:#f5b84b;--radius:14px;--shadow:0 16px 40px rgba(0,0,0,.24)
}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
button,input,textarea,select{font:inherit}button{cursor:pointer}
body{overflow:hidden}
.shell{height:100vh;display:grid;grid-template-columns:280px minmax(0,1fr) 310px;grid-template-rows:64px minmax(0,1fr);grid-template-areas:"top top top" "left main right"}
.top{grid-area:top;display:flex;align-items:center;justify-content:space-between;padding:0 18px;border-bottom:1px solid var(--line);background:rgba(13,19,29,.96);backdrop-filter:blur(12px);z-index:4}
.brand{display:flex;align-items:center;gap:12px}.brand-mark{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--blue),var(--purple));display:grid;place-items:center;font-weight:800}.brand h1{font-size:15px;margin:0}.brand small{display:block;color:var(--muted);font-size:11px;margin-top:2px}
.top-actions{display:flex;align-items:center;gap:8px}.status-pill,.shortcut{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:999px;padding:7px 10px;font-size:11px}.status-pill strong{color:var(--green)}
.btn{border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:10px;padding:9px 12px;font-weight:700;font-size:12px}.btn:hover{filter:brightness(1.1)}.btn.primary{background:var(--blue);border-color:transparent}.btn.success{background:var(--green);border-color:transparent;color:#06140f}.btn.danger{color:#ffb7bf}.btn.ghost{background:transparent}
.left{grid-area:left;border-right:1px solid var(--line);background:var(--panel3);display:flex;flex-direction:column;min-height:0}.left-head{padding:15px;border-bottom:1px solid var(--line)}.section-title{font-size:12px;font-weight:800;margin-bottom:8px}.subtle{color:var(--muted);font-size:11px;line-height:1.5}.search{width:100%;border:1px solid var(--line);background:#0a1019;color:var(--text);border-radius:10px;padding:10px 11px;outline:none;margin-top:10px}.left-actions{display:grid;grid-template-columns:1fr auto;gap:8px;margin-top:8px}.strategy-list{list-style:none;margin:0;padding:8px;overflow:auto}.strategy{padding:11px;border:1px solid transparent;border-radius:11px;margin-bottom:5px;cursor:pointer}.strategy:hover{background:var(--panel)}.strategy.active{background:#172238;border-color:#31548c}.strategy .name{font-size:12px;font-weight:750}.strategy .meta{font-size:10px;color:var(--muted);margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.main{grid-area:main;min-width:0;min-height:0;overflow:auto;padding:16px;display:grid;grid-template-rows:auto auto minmax(340px,1fr);gap:14px}.card{background:linear-gradient(180deg,var(--panel),#0f151f);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}
.composer{padding:16px}.composer-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.composer-head h2{font-size:17px;margin:0 0 5px}.mode-row{display:flex;gap:6px;flex-wrap:wrap}.mode{border:1px solid var(--line);background:var(--panel2);color:var(--muted);padding:7px 10px;border-radius:999px;font-size:11px}.mode.active{color:white;border-color:#466ba8;background:#1d3151}.prompt{width:100%;min-height:104px;resize:vertical;border:1px solid #30425d;background:#09111d;color:var(--text);border-radius:12px;padding:13px 14px;outline:none;line-height:1.55;margin-top:12px}.prompt:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(79,140,255,.12)}
.quick-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:9px}.chip{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:6px 9px;font-size:10px}.chip:hover{color:#fff;border-color:#48638a}.compose-actions{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:12px}.hint{font-size:10px;color:var(--muted)}kbd{border:1px solid #39465a;background:#0a0f16;border-radius:5px;padding:2px 5px;font-size:9px;color:#aebbd0}
.meta-card{padding:12px;display:grid;grid-template-columns:1fr 1fr auto;gap:9px;align-items:end}.field label{display:block;font-size:10px;color:var(--muted);margin:0 0 5px 2px}.field input,.field select{width:100%;border:1px solid var(--line);background:#0b111a;color:var(--text);border-radius:9px;padding:9px 10px;outline:none}.meta-actions{display:flex;gap:7px}
.workbench{display:grid;grid-template-rows:46px minmax(230px,38%) minmax(220px,1fr);min-height:600px;overflow:hidden}.workbar{display:flex;align-items:center;justify-content:space-between;padding:0 12px;border-bottom:1px solid var(--line);background:#101722}.workbar .tabs{display:flex;gap:5px}.tab{border:0;background:transparent;color:var(--muted);padding:7px 9px;border-radius:8px;font-size:11px;font-weight:700}.tab.active{background:#1c2839;color:white}.work-actions{display:flex;gap:7px;align-items:center}.dirty{font-size:10px;color:var(--amber);display:none}.dirty.show{display:inline}
.editor-zone{display:grid;grid-template-columns:minmax(0,1fr) 250px;border-bottom:1px solid var(--line);min-height:0}.editor-wrap{display:flex;flex-direction:column;min-width:0}.editor-label{padding:7px 11px;border-bottom:1px solid var(--line);font-size:10px;color:var(--muted);display:flex;justify-content:space-between}.editor{width:100%;height:100%;min-height:220px;resize:none;border:0;background:#080d14;color:#dce8f7;padding:13px 14px;outline:none;font:12px/1.55 Consolas,"SFMono-Regular",monospace;tab-size:4}.rail-mini{padding:11px;background:#0b111a;overflow:auto}.check{display:flex;gap:8px;padding:8px;border-radius:9px;margin-bottom:6px;background:#101925;border:1px solid #1f2e43}.check-dot{width:8px;height:8px;border-radius:50%;background:var(--green);margin-top:4px;flex:0 0 auto}.check.warn .check-dot{background:var(--amber)}.check .t{font-size:10px;font-weight:750}.check .d{font-size:9px;color:var(--muted);margin-top:3px;line-height:1.35}
.result-zone{display:grid;grid-template-columns:minmax(0,1fr) 260px;min-height:0}.chart{position:relative;min-height:250px}.chart #chart{width:100%;height:100%}.empty-chart{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:11px;pointer-events:none}.metrics{border-left:1px solid var(--line);padding:11px;display:flex;flex-direction:column;gap:8px;background:#0c121b;overflow:auto}.metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}.metric{border:1px solid var(--line);border-radius:10px;background:var(--panel);padding:9px}.metric .k{font-size:9px;color:var(--muted)}.metric .v{font-size:14px;font-weight:800;margin-top:4px}.console{border:1px solid var(--line);border-radius:10px;background:#070b11;min-height:90px;padding:9px;font:10px/1.45 Consolas,monospace;color:#96a6ba;white-space:pre-wrap}
.right{grid-area:right;border-left:1px solid var(--line);background:var(--panel3);padding:14px;overflow:auto}.right h3{font-size:12px;margin:0 0 8px}.guard{border:1px solid #244836;background:#0e211b;border-radius:12px;padding:11px;margin-bottom:10px}.guard strong{font-size:11px;color:#9be8c9}.guard p{font-size:10px;color:#83aa9c;line-height:1.45;margin:5px 0 0}.step{display:flex;gap:9px;margin:10px 0}.step-n{width:22px;height:22px;border-radius:7px;background:#1b2940;border:1px solid #314667;display:grid;place-items:center;font-size:10px;font-weight:800;flex:0 0 auto}.step.done .step-n{background:#123227;border-color:#235a46;color:#9be8c9}.step .st{font-size:10px;font-weight:750}.step .sd{font-size:9px;color:var(--muted);margin-top:3px;line-height:1.4}.divider{height:1px;background:var(--line);margin:12px 0}.source-drawer{display:none;margin-top:10px}.source-drawer.show{display:block}.source-editor{width:100%;min-height:150px;resize:vertical;background:#080d14;color:#dbe7f5;border:1px solid var(--line);border-radius:10px;padding:10px;font:11px/1.45 Consolas,monospace;outline:none}
.toast{position:fixed;right:18px;bottom:18px;background:#172333;border:1px solid #344964;color:white;border-radius:10px;padding:10px 12px;font-size:11px;box-shadow:var(--shadow);opacity:0;transform:translateY(8px);pointer-events:none;transition:.2s;z-index:20}.toast.show{opacity:1;transform:none}
@media(max-width:1180px){.shell{grid-template-columns:240px minmax(0,1fr);grid-template-areas:"top top" "left main"}.right{display:none}}@media(max-width:820px){body{overflow:auto}.shell{height:auto;min-height:100vh;display:block}.top{position:sticky;top:0;height:64px}.left{display:none}.main{padding:10px}.meta-card{grid-template-columns:1fr}.editor-zone,.result-zone{grid-template-columns:1fr}.rail-mini,.metrics{border-left:0;border-top:1px solid var(--line)}.workbench{min-height:850px}}
</style>
</head>
<body>
<div class="shell">
  <header class="top">
    <div class="brand"><div class="brand-mark">Q</div><div><h1>Quant DSL Studio</h1><small>Idea → DSL → deterministic execution</small></div></div>
    <div class="top-actions"><span class="status-pill"><strong>●</strong> Core deterministic</span><span class="shortcut">기존 UI <a href="/" style="color:#9fc0ff">열기</a></span><button class="btn success" onclick="runBacktest()">백테스트 실행</button></div>
  </header>

  <aside class="left">
    <div class="left-head"><div class="section-title">내 전략</div><div class="subtle">검색하고 바로 이어서 편집합니다.</div><input id="search" class="search" placeholder="전략 검색" oninput="renderStrategies()"/><div class="left-actions"><button class="btn primary" onclick="newStrategy()">+ 새 전략</button><button class="btn" onclick="loadStrategies()">↻</button></div></div>
    <ul id="strategy-list" class="strategy-list"></ul>
  </aside>

  <main class="main">
    <section class="card composer">
      <div class="composer-head"><div><h2>무엇을 만들고 싶으세요?</h2><div class="subtle">전략 아이디어를 평문으로 쓰면 DSL 초안을 만들고, 이후에는 DSL이 최종 통제점이 됩니다.</div></div><div class="mode-row"><button class="mode active" data-mode="PROMPT" onclick="setMode('PROMPT',this)">자연어</button><button class="mode" data-mode="PINESCRIPT" onclick="setMode('PINESCRIPT',this)">Pine</button><button class="mode" data-mode="KIWOOM" onclick="setMode('KIWOOM',this)">키움</button></div></div>
      <textarea id="prompt" class="prompt" placeholder="예: 5일선이 20일선을 상향 돌파하고 RSI가 60 미만일 때 진입. 5일선이 20일선을 하향 돌파하면 청산. 손실 구간에서 무리하게 진입하지 않도록 조건을 명확히 해줘."></textarea>
      <div class="quick-row"><span class="subtle">빠른 시작</span><button class="chip" onclick="usePrompt('5일선이 20일선을 상향 돌파하고 RSI 60 미만일 때 진입, 하향 돌파 시 청산')">이평 돌파</button><button class="chip" onclick="usePrompt('RSI 30 이하 과매도 구간 진입, RSI 70 이상 청산')">RSI 반전</button><button class="chip" onclick="usePrompt('20일 이동평균 위에서만 진입하고 최근 종가가 전일 종가보다 높을 때 매수')">추세 필터</button><button class="chip" onclick="toggleSource()">원본 코드 붙여넣기</button></div>
      <div id="source-drawer" class="source-drawer"><textarea id="source" class="source-editor" placeholder="Pine Script 또는 키움 수식을 붙여넣으세요."></textarea></div>
      <div class="compose-actions"><div class="hint"><kbd>Ctrl</kbd> + <kbd>Enter</kbd> 생성 · <kbd>Ctrl</kbd> + <kbd>S</kbd> 저장 · <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> 실행</div><button class="btn primary" onclick="generateDSL()">DSL 초안 만들기 →</button></div>
    </section>

    <section class="card meta-card"><div class="field"><label>전략 이름</label><input id="name" placeholder="예: Trend_RSI_v1" /></div><div class="field"><label>설명</label><input id="desc" placeholder="핵심 진입/청산 의도" /></div><div class="meta-actions"><button id="delete-btn" class="btn danger" onclick="deleteStrategy()" style="display:none">삭제</button><button class="btn" onclick="saveStrategy()">저장</button></div></section>

    <section class="card workbench">
      <div class="workbar"><div class="tabs"><button class="tab active">DSL 편집</button><button class="tab" onclick="focusPrompt()">아이디어 수정</button></div><div class="work-actions"><span id="dirty" class="dirty">● 저장 안 됨</span><button class="btn ghost" onclick="copyDSL()">복사</button><button class="btn" onclick="formatDSL()">정리</button><button class="btn success" onclick="runBacktest()">실행</button></div></div>
      <div class="editor-zone"><div class="editor-wrap"><div class="editor-label"><span>최종 실행 DSL</span><span id="line-count">0 lines</span></div><textarea id="dsl" class="editor" spellcheck="false"></textarea></div><div class="rail-mini"><div class="section-title">실행 전 체크</div><div class="check"><span class="check-dot"></span><div><div class="t">DSL이 최종 권한</div><div class="d">자연어는 초안을 만들 뿐 실행 권한을 직접 갖지 않습니다.</div></div></div><div class="check"><span class="check-dot"></span><div><div class="t">Core guard 유지</div><div class="d">Parser / Semantic / hard guard를 우회하지 않습니다.</div></div></div><div class="check warn"><span class="check-dot"></span><div><div class="t">결과를 검토하세요</div><div class="d">백테스트 결과는 자동 배포 권한을 의미하지 않습니다.</div></div></div></div></div>
      <div class="result-zone"><div class="chart"><div id="chart"></div><div id="empty-chart" class="empty-chart">백테스트를 실행하면 차트가 표시됩니다.</div></div><aside class="metrics"><div class="section-title">백테스트 결과</div><div class="metric-grid"><div class="metric"><div class="k">총 수익률</div><div id="m-return" class="v">-</div></div><div class="metric"><div class="k">MDD</div><div id="m-mdd" class="v">-</div></div><div class="metric"><div class="k">승률</div><div id="m-win" class="v">-</div></div><div class="metric"><div class="k">거래 횟수</div><div id="m-trades" class="v">-</div></div></div><div class="section-title" style="margin-top:4px">로그</div><div id="console" class="console">준비 완료.</div></aside></div>
    </section>
  </main>

  <aside class="right">
    <div class="guard"><strong>결정론적 안전 레일</strong><p>LLM/프롬프트는 DSL 작성 보조 역할입니다. 실행 여부는 기존 DSL Parser, Semantic, Runtime, hard guard 계약이 결정합니다.</p></div>
    <h3>추천 작업 순서</h3><div id="s1" class="step done"><div class="step-n">1</div><div><div class="st">아이디어 설명</div><div class="sd">평문 또는 기존 Pine/키움 코드를 입력합니다.</div></div></div><div id="s2" class="step"><div class="step-n">2</div><div><div class="st">DSL 확인</div><div class="sd">생성된 DSL을 직접 읽고 필요한 조건을 수정합니다.</div></div></div><div id="s3" class="step"><div class="step-n">3</div><div><div class="st">저장</div><div class="sd">전략 이름과 의도를 함께 남겨 다시 찾기 쉽게 합니다.</div></div></div><div id="s4" class="step"><div class="step-n">4</div><div><div class="st">백테스트</div><div class="sd">차트·수익률·MDD·승률을 한 화면에서 확인합니다.</div></div></div>
    <div class="divider"></div><h3>편의 기능</h3><div class="subtle">• 전략 검색<br>• 로컬 자동 임시저장<br>• 키보드 단축키<br>• 자연어/Pine/키움 한 자리 입력<br>• 레거시 UI 즉시 전환<br>• DSL 복사/정리</div>
  </aside>
</div>
<div id="toast" class="toast"></div>
<script>
let strategies=[], currentId=null, sourceMode='PROMPT', dirty=false;
let chart=null,candle=null,ma5=null,ma20=null,bbU=null,bbL=null;
const $=id=>document.getElementById(id);
function toast(msg){const el=$('toast');el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}
function log(msg){$('console').textContent=`${new Date().toLocaleTimeString()}  ${msg}\n`+$('console').textContent}
function setDirty(v=true){dirty=v;$('dirty').classList.toggle('show',v);if(v) localSave()}
function localSave(){localStorage.setItem('quant-dsl-ux-draft',JSON.stringify({name:$('name').value,desc:$('desc').value,prompt:$('prompt').value,dsl:$('dsl').value,mode:sourceMode,source:$('source').value}))}
function restoreDraft(){try{const x=JSON.parse(localStorage.getItem('quant-dsl-ux-draft')||'null');if(!x)return;$('name').value=x.name||'';$('desc').value=x.desc||'';$('prompt').value=x.prompt||'';$('dsl').value=x.dsl||'';$('source').value=x.source||'';updateLines()}catch(e){}}
function setMode(mode,btn){sourceMode=mode;document.querySelectorAll('.mode').forEach(x=>x.classList.remove('active'));btn.classList.add('active');if(mode==='PROMPT'){$('source-drawer').classList.remove('show');$('prompt').placeholder='전략 아이디어를 자연어로 설명하세요.'}else{$('source-drawer').classList.add('show');$('prompt').placeholder=mode==='PINESCRIPT'?'Pine 코드의 의도나 변환 메모를 적어도 됩니다.':'키움 수식의 의도나 변환 메모를 적어도 됩니다.'}localSave()}
function toggleSource(){$('source-drawer').classList.toggle('show')}
function usePrompt(t){$('prompt').value=t;sourceMode='PROMPT';document.querySelectorAll('.mode').forEach(x=>x.classList.toggle('active',x.dataset.mode==='PROMPT'));setDirty(true);$('prompt').focus()}
function focusPrompt(){$('prompt').focus();$('prompt').scrollIntoView({behavior:'smooth',block:'center'})}
async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opt});let data=null;try{data=await r.json()}catch(e){}if(!r.ok)throw new Error(data?.detail||`HTTP ${r.status}`);return data}
async function loadStrategies(){try{strategies=await api('/api/strategies');renderStrategies()}catch(e){log('전략 목록 오류: '+e.message)}}
function renderStrategies(){const q=$('search').value.trim().toLowerCase();const list=$('strategy-list');list.innerHTML='';strategies.filter(s=>!q||`${s.name} ${s.description||''}`.toLowerCase().includes(q)).forEach(s=>{const li=document.createElement('li');li.className='strategy'+(s.id===currentId?' active':'');li.innerHTML=`<div class="name">${escapeHtml(s.name)}</div><div class="meta">${escapeHtml(s.description||'설명 없음')}</div>`;li.onclick=()=>selectStrategy(s);list.appendChild(li)})}
function escapeHtml(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function selectStrategy(s){currentId=s.id;$('name').value=s.name||'';$('desc').value=s.description||'';$('dsl').value=s.dsl_code||'';$('delete-btn').style.display='inline-block';setDirty(false);updateLines();renderStrategies();markStep(2);log(`전략 '${s.name}' 로드`) }
function newStrategy(){currentId=null;$('name').value='';$('desc').value='';$('dsl').value='';$('prompt').value='';$('source').value='';$('delete-btn').style.display='none';setDirty(false);updateLines();renderStrategies();$('prompt').focus();toast('새 전략 작성 시작')}
async function generateDSL(){const source=sourceMode==='PROMPT'?$('prompt').value:$('source').value;if(!source.trim()){toast('먼저 아이디어나 원본 코드를 입력하세요.');return}try{log(`${sourceMode} → DSL 변환 요청`);const res=await api('/api/transpile',{method:'POST',body:JSON.stringify({source_type:sourceMode,source_code:source,name:$('name').value||'Converted_Strategy'})});$('dsl').value=res.dsl_code||'';setDirty(true);updateLines();markStep(2);toast('DSL 초안을 만들었습니다. 검토 후 실행하세요.')}catch(e){log('DSL 생성 실패: '+e.message);toast('DSL 생성 실패') }}
async function saveStrategy(){const name=$('name').value.trim(),dsl=$('dsl').value.trim();if(!name||!dsl){toast('전략 이름과 DSL이 필요합니다.');return}const payload={name,description:$('desc').value.trim(),dsl_code:dsl,source_type:sourceMode};try{if(currentId){await api(`/api/strategies/${currentId}`,{method:'PUT',body:JSON.stringify(payload)})}else{const r=await api('/api/strategies',{method:'POST',body:JSON.stringify(payload)});currentId=r.id}$('delete-btn').style.display='inline-block';setDirty(false);localStorage.removeItem('quant-dsl-ux-draft');await loadStrategies();markStep(3);toast('전략을 저장했습니다.');log('전략 저장 완료')}catch(e){log('저장 실패: '+e.message);toast('저장 실패: '+e.message)}}
async function deleteStrategy(){if(!currentId||!confirm('이 전략을 삭제할까요?'))return;try{await api(`/api/strategies/${currentId}`,{method:'DELETE'});newStrategy();await loadStrategies();toast('전략을 삭제했습니다.')}catch(e){toast('삭제 실패')}}
function copyDSL(){navigator.clipboard?.writeText($('dsl').value);toast('DSL을 복사했습니다.')}
function formatDSL(){let s=$('dsl').value.split('\n').map(x=>x.replace(/\s+$/,'')).join('\n').replace(/\n{3,}/g,'\n\n').trim();$('dsl').value=s+'\n';setDirty(true);updateLines();toast('공백을 정리했습니다.')}
function updateLines(){$('line-count').textContent=($('dsl').value?$('dsl').value.split('\n').length:0)+' lines'}
function markStep(n){for(let i=1;i<=n;i++)$('s'+i)?.classList.add('done')}
function ensureChart(){if(chart)return;const el=$('chart');chart=LightweightCharts.createChart(el,{autoSize:true,layout:{background:{color:'#0b1018'},textColor:'#8695aa'},grid:{vertLines:{color:'#182130'},horzLines:{color:'#182130'}},timeScale:{borderColor:'#283548'},rightPriceScale:{borderColor:'#283548'}});candle=chart.addCandlestickSeries({upColor:'#2dc48d',downColor:'#ef6673',wickUpColor:'#2dc48d',wickDownColor:'#ef6673',borderVisible:false});ma5=chart.addLineSeries({color:'#4f8cff',lineWidth:2});ma20=chart.addLineSeries({color:'#f2b64c',lineWidth:2});bbU=chart.addLineSeries({color:'#9d78ff',lineWidth:1,lineStyle:2});bbL=chart.addLineSeries({color:'#9d78ff',lineWidth:1,lineStyle:2})}
async function runBacktest(){const dsl=$('dsl').value.trim();if(!dsl){toast('실행할 DSL이 없습니다.');return}try{log('백테스트 실행 중…');const r=await api('/api/backtest',{method:'POST',body:JSON.stringify({dsl_code:dsl})});ensureChart();candle.setData(r.candles||[]);ma5.setData(r.ma5||[]);ma20.setData(r.ma20||[]);bbU.setData(r.bb_upper||[]);bbL.setData(r.bb_lower||[]);if(r.markers&&candle.setMarkers)candle.setMarkers(r.markers);chart.timeScale().fitContent();$('empty-chart').style.display='none';const m=r.metrics||{};$('m-return').textContent=m.total_return||'-';$('m-mdd').textContent=m.mdd||'-';$('m-win').textContent=m.win_rate||'-';$('m-trades').textContent=m.trade_count||'-';markStep(4);log(`완료 · ${m.engine_mode||'engine'}`);toast('백테스트 완료')}catch(e){log('백테스트 실패: '+e.message);toast('백테스트 실패')}}
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&!e.shiftKey){e.preventDefault();generateDSL()}if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key==='Enter'){e.preventDefault();runBacktest()}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveStrategy()}});
['name','desc','prompt','dsl','source'].forEach(id=>$(id).addEventListener('input',()=>{if(id==='dsl')updateLines();setDirty(true)}));
restoreDraft();loadStrategies();updateLines();
</script>
</body>
</html>'''


@app.get("/ux", response_class=HTMLResponse, include_in_schema=False)
def ux_index():
    return UX_HTML


if __name__ == "__main__":
    uvicorn.run("app_ui_ux:app", host="127.0.0.1", port=8000, reload=False)
