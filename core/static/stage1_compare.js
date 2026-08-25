(()=>{
const $=id=>document.getElementById(id);
const api=async url=>{const r=await fetch(url);const b=await r.json().catch(()=>({}));if(!r.ok)throw new Error(b.detail||`HTTP ${r.status}`);return b};
const num=(value,digits=2)=>Number(value??0).toFixed(digits);
const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let lastCurrentId=null,lastRootId=null;

function ensureComparePanel(){
  if($('experiment-compare'))return;
  const history=$('history'); if(!history)return;
  const panel=document.createElement('div'); panel.id='experiment-compare';
  panel.style.cssText='position:sticky;top:0;z-index:3;background:#131821;border:1px solid #2a3444;border-radius:5px;padding:7px;margin-bottom:8px';
  panel.innerHTML=`<div style="font-weight:800;margin-bottom:6px">Experiment A/B Compare</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:5px"><select id="compare-a" class="control"></select><select id="compare-b" class="control"></select></div>
  <div style="display:flex;gap:5px;margin-bottom:5px"><button id="compare-run" class="primary">비교</button><button id="compare-load-a">A 차트</button><button id="compare-load-b">B 차트</button></div>
  <div id="compare-result" style="max-height:190px;overflow:auto;font-size:11px;color:#c2ccd9"></div>`;
  history.before(panel);
  $('compare-run').onclick=()=>runCompare().catch(showError);
  $('compare-load-a').onclick=()=>loadExperimentFromHistory(Number($('compare-a').value));
  $('compare-load-b').onclick=()=>loadExperimentFromHistory(Number($('compare-b').value));
}
function showError(error){const host=$('compare-result');if(host)host.innerHTML=`<span style="color:#ff9c98">${esc(error.message||error)}</span>`}
function currentId(){const text=$('current')?.textContent||'';const m=text.match(/#(\d+)/);return m?Number(m[1]):null}
async function refresh(){
  ensureComparePanel(); const id=currentId(); if(!id||id===lastCurrentId)return;
  const detail=await api(`/api/stage1/experiments/${id}`); const root=Number(detail.experiment.root_id); lastCurrentId=id; lastRootId=root;
  const listing=await api(`/api/stage1/experiments?root_id=${root}&limit=500`); const rows=[...(listing.experiments||[])].sort((a,b)=>a.id-b.id);
  const options=rows.map(e=>`<option value="${e.id}">#${e.id} ${esc(e.operation)} · ${num(e.result?.metrics_numeric?.total_return_pct)}%</option>`).join('');
  $('compare-a').innerHTML=options; $('compare-b').innerHTML=options;
  const baseline=rows.find(e=>e.operation==='BASELINE')||rows[0]; if(baseline)$('compare-a').value=String(baseline.id); $('compare-b').value=String(id);
  await runCompare();
}
function metricRow(name,a,b,reverse=false){const av=Number(a||0),bv=Number(b||0),delta=bv-av;const good=reverse?delta<0:delta>0;const tone=Math.abs(delta)<1e-12?'#8f9bad':good?'#7de0b8':'#ff9c98';return`<tr><td style="text-align:left">${esc(name)}</td><td>${num(av)}</td><td>${num(bv)}</td><td style="color:${tone}">${delta>=0?'+':''}${num(delta)}</td></tr>`}
async function runCompare(){
  const left=Number($('compare-a')?.value),right=Number($('compare-b')?.value); if(!left||!right)return;
  const [a,b]=await Promise.all([api(`/api/stage1/experiments/${left}`),api(`/api/stage1/experiments/${right}`)]);
  const am=a.experiment.result?.metrics_numeric||{},bm=b.experiment.result?.metrics_numeric||{};
  const sameData=a.experiment.provenance?.data_hash===b.experiment.provenance?.data_hash;
  const lineage=new Set((b.lineage||[]).map(x=>x.id)); const ancestor=lineage.has(left);
  const ah=(a.experiment.analysis?.findings||[]).map(x=>x.code).join(', ')||'-'; const bh=(b.experiment.analysis?.findings||[]).map(x=>x.code).join(', ')||'-';
  $('compare-result').innerHTML=`<table class="table"><thead><tr><th>Metric</th><th>A</th><th>B</th><th>Δ B-A</th></tr></thead><tbody>
    ${metricRow('Return %',am.total_return_pct,bm.total_return_pct)}${metricRow('MDD %',Math.abs(am.mdd_pct||0),Math.abs(bm.mdd_pct||0),true)}
    ${metricRow('Win rate %',am.win_rate_pct,bm.win_rate_pct)}${metricRow('Profit factor',am.profit_factor,bm.profit_factor)}
    ${metricRow('Closed trades',am.closed_trade_count,bm.closed_trade_count)}${metricRow('Total cost',am.total_cost,bm.total_cost,true)}</tbody></table>
    <div style="margin-top:5px"><b>Data</b> ${sameData?'SAME':'DIFFERENT'} · <b>A→B lineage</b> ${ancestor?'YES':'NO'}</div>
    <div><b>A findings</b> ${esc(ah)}</div><div><b>B findings</b> ${esc(bh)}</div>
    <div><b>A</b> #${a.experiment.id} ${esc(a.experiment.operation)} · <b>B</b> #${b.experiment.id} ${esc(b.experiment.operation)}</div>`;
}
function loadExperimentFromHistory(id){if(!id)return;const row=document.querySelector(`.history-row[data-id="${id}"]`);if(row){row.click();return}location.hash=`experiment-${id}`}
const observer=new MutationObserver(()=>refresh().catch(showError));
addEventListener('DOMContentLoaded',()=>{ensureComparePanel();const badge=$('current');if(badge)observer.observe(badge,{childList:true,subtree:true,characterData:true});setInterval(()=>refresh().catch(()=>{}),1500)});
})();
