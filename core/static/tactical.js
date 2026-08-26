(()=>{
const $=id=>document.getElementById(id);
const params=new URLSearchParams(location.search);
const chartBase=(params.get('chartSsot')||'http://127.0.0.1:5174').replace(/\/$/,'');
const chartOrigin=new URL(chartBase).origin;
let frame=null,ready=false,pending=null,seq=0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
const shortHash=s=>String(s||'').slice(0,10)||'-';
function state(text,kind=''){const n=$('state');n.textContent=text;n.className=`badge ${kind}`;}
async function api(url,options={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...options});const b=await r.json().catch(()=>({}));if(!r.ok)throw new Error(b.detail||`HTTP ${r.status}`);return b;}
function q(){return new URLSearchParams({
  search_date:$('search-date').value,
  search_time:$('search-time').value,
  condition_name:$('condition').value,
  hold_period:$('hold').value,
  performance_database:$('perf-db').value
}).toString();}
function ensureChart(){
  if(frame)return;
  frame=document.createElement('iframe');
  frame.title='Shared Chart SSOT';
  frame.src=`${chartBase}/src/shell/chart-document-viewer.html?parentOrigin=${encodeURIComponent(location.origin)}`;
  $('chart').append(frame);
  window.addEventListener('message',ev=>{
    if(ev.source!==frame.contentWindow||ev.origin!==chartOrigin)return;
    const m=ev.data||{};
    if(m.type==='chart-document/ready'){ready=true;if(pending)send(pending);}
    if(m.type==='chart-document/rendered')state(`Chart ${m.summary?.bars||0} bars`,'ok');
    if(m.type==='chart-document/error')state(`Chart error: ${m.error||'unknown'}`,'fail');
  });
}
function send(doc){pending=doc;ensureChart();if(!ready)return;frame.contentWindow.postMessage({type:'chart-document/render',requestId:`tactical-${++seq}`,document:doc},chartOrigin);}
async function loadCohort(){
  if(!$('search-date').value)throw new Error('Search date를 입력하세요.');
  state('Cohort loading…');
  const d=await api(`/api/stage1/tactical/1516/cohort?${q()}`);
  $('cohort').textContent=JSON.stringify({
    unit_id:d.unit_id,as_of:d.as_of,snapshot_hash:d.snapshot_hash,
    members:d.members?.map(x=>({symbol:x.symbol,...x.features}))
  },null,2);
  state(`Cohort ${d.members?.length||0} symbols`,'ok');
}
function partitionStatus(validation,role){
  const row=(validation?.partitions||[]).find(x=>x.role===role);
  return row?.status||'-';
}
async function loadEvolution(){
  const family=$('evo-family').value.trim();
  if(!family)throw new Error('Evolution family를 입력하세요.');
  state('Evolution lineage loading…');
  const d=await api(`/api/stage1/tactical/evolution/${encodeURIComponent(family)}`);
  $('evo-head').textContent=`Head: ${shortHash(d.head_generation_hash)}`;
  $('evo-lineage').textContent=`Lineage: ${shortHash(d.lineage_hash)}`;
  $('evo-nodes').innerHTML=(d.nodes||[]).map(node=>{
    const evidence=node.acquisition_evidence||{};
    const validation=evidence.validation||null;
    const summary=node.profile_summary||{};
    return `<tr>`+
      `<td>G${Number(node.generation_index||0)} <span class="hash">${esc(shortHash(node.generation_hash))}</span></td>`+
      `<td>${node.is_head?'HEAD':'-'}</td>`+
      `<td>${esc(node.new_skill||'BASE')}</td>`+
      `<td>${esc((evidence.failure_tags||[]).join(', ')||'-')}</td>`+
      `<td>${esc(validation?.partitions?.find(x=>x.role==='TRAIN')?.status||'-')}</td>`+
      `<td>${esc(partitionStatus(validation,'VALIDATION'))}</td>`+
      `<td>${esc(partitionStatus(validation,'OOS'))}</td>`+
      `<td>${esc(partitionStatus(validation,'HARSH'))}</td>`+
      `<td>${summary.average_return_pct==null?'-':Number(summary.average_return_pct).toFixed(3)}</td>`+
      `<td>${summary.worst_mdd_pct==null?'-':Number(summary.worst_mdd_pct).toFixed(3)}</td>`+
      `</tr>`;
  }).join('');
  $('evo-attempts').innerHTML=(d.attempts||[]).map(item=>{
    const validation=item.validation||null;
    return `<tr>`+
      `<td>${esc(item.skill_id||'-')}</td>`+
      `<td class="hash">${esc(shortHash(item.child_candidate_hash))}</td>`+
      `<td>${esc(item.train_decision||'-')}</td>`+
      `<td>${esc(validation?.decision||'-')}</td>`+
      `<td>${esc((validation?.holdout_failures||[]).join(', ')||'-')}</td>`+
      `<td class="hash">${esc(shortHash(item.promoted_generation_hash))}</td>`+
      `</tr>`;
  }).join('');
  state(`Evolution ${d.summary?.generations||0} generations / ${d.summary?.attempts||0} attempts`,'ok');
}
async function run(){
  if(!$('search-date').value)throw new Error('Search date를 입력하세요.');
  state('1516 tactical run…');
  const body={
    search_date:$('search-date').value,
    search_time:$('search-time').value,
    condition_name:$('condition').value,
    hold_period:$('hold').value,
    dsl_code:$('dsl').value,
    timeframe:$('timeframe').value,
    required_bars:Number($('bars').value),
    entry_end_time:Number($('cutoff').value),
    max_workers:Number($('workers').value),
    benchmark_symbol:$('benchmark').value.trim(),
    rank_by:'feature:search_volume',
    performance_database:$('perf-db').value,
    market_database:$('market-db').value,
    market_table:$('market-table').value,
    market_table_timeframe:$('timeframe').value,
    settings:{signal_mode:'bar_close',total_capital:10000000}
  };
  const d=await api('/api/stage1/tactical/1516/run',{method:'POST',body:JSON.stringify(body)});
  const e=d.evaluation||{},r=d.result||{};
  $('m-cohort').textContent=e.cohort_symbols??'-';
  $('m-pos').textContent=e.official_mission_positive??'-';
  $('m-retain').textContent=e.mission_positive_profitable_retention==null?'-':`${(e.mission_positive_profitable_retention*100).toFixed(1)}%`;
  $('m-precision').textContent=e.profitable_precision_against_mission==null?'-':`${(e.profitable_precision_against_mission*100).toFixed(1)}%`;
  $('m-scenario').textContent=String(r.scenario_hash||'').slice(0,8)||'-';
  const rank=new Map((r.ranking||[]).map(x=>[x.symbol,x.score]));
  $('rows').innerHTML=(r.results||[]).map(x=>{
    const f=x.metadata?.point_in_time_features||{},o=x.official_outcome||{};
    const score=rank.get(x.symbol);
    return `<tr><td>${esc(x.symbol)}</td><td>${esc(f.name||'')}</td><td>${esc(f.search_volume??'')}</td><td>${score==null?'-':Number(score).toFixed(2)}</td><td>${Number(x.strategy_return_pct||0).toFixed(2)}</td><td>${o.max_ret_in_period==null?'-':Number(o.max_ret_in_period).toFixed(2)}</td><td>${o.label_10??'-'}</td><td>${Number(x.mdd_pct||0).toFixed(2)}</td></tr>`;
  }).join('');
  send(d.chart_document);
  state('1516 tactical run complete','ok');
}
function wrap(fn){return async()=>{try{await fn();}catch(e){state(e.message,'fail');}}}
$('load').onclick=wrap(loadCohort);
$('run').onclick=wrap(run);
$('evo-load').onclick=wrap(loadEvolution);
ensureChart();
})();
