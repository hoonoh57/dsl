(()=>{
const $=id=>document.getElementById(id);
const api=async url=>{const r=await fetch(url);const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(body.detail||`HTTP ${r.status}`);return body};
const clone=value=>JSON.parse(JSON.stringify(value));
const chartSsotBase=(new URLSearchParams(location.search).get('chartSsot')||'http://127.0.0.1:5174').replace(/\/$/,'');
const chartSsotOrigin=new URL(chartSsotBase).origin;
let requestSequence=0;

function status(text,kind='ok'){
  const node=$('status');
  if(!node)return;
  node.textContent=text;
  node.style.color=kind==='bad'?'#ff9c98':kind==='warn'?'#e6a43d':'#7de0b8';
}
function currentExperimentId(){
  const match=String($('current')?.textContent||'').match(/#(\d+)/);
  return match?Number(match[1]):null;
}
function chartTimeForSource(document,sourceTime){
  const needle=String(sourceTime);
  return document?.bars?.find(bar=>String(bar.sourceTime)===needle)?.time;
}
function money(value){
  const number=Number(value);
  return Number.isFinite(number)?number.toLocaleString(undefined,{maximumFractionDigits:2}):'-';
}
function pct(value){
  const number=Number(value);
  return Number.isFinite(number)?`${number.toFixed(2)}%`:'-';
}
function markRows(selected){
  document.querySelectorAll('#trades tr[data-trade-id]').forEach(row=>{
    const active=row===selected;
    row.classList.toggle('trade-selected',active);
    row.setAttribute('aria-selected',active?'true':'false');
    row.tabIndex=0;
    row.setAttribute('role','button');
    row.title='클릭하면 이 거래를 차트에서 강조합니다.';
  });
}
function renderSelectedTrade(trade){
  const host=$('selected-trade');
  if(!host)return;
  host.innerHTML=`<b>Trade #${trade.trade_id}</b><div>진입 ${money(trade.entry_price)} → 청산 ${money(trade.exit_price)}</div><div>Return ${pct(trade.return_pct)} · MFE ${pct(trade.mfe_pct)} · MAE ${pct(trade.mae_pct)}</div>`;
  host.className='trade-audit-card active';
}
function sendChart(document){
  const frame=$('shared-chart-frame');
  if(!frame?.contentWindow)throw new Error('Shared Chart가 아직 준비되지 않았습니다.');
  frame.contentWindow.postMessage({type:'chart-document/render',requestId:`stage1-trade-${++requestSequence}`,document},chartSsotOrigin);
}
async function inspect(row){
  const experimentId=currentExperimentId();
  if(!experimentId)throw new Error('먼저 Experiment를 선택하세요.');
  const tradeId=Number(row.dataset.tradeId);
  if(!Number.isFinite(tradeId))throw new Error('거래 번호를 읽지 못했습니다.');
  status(`Trade #${tradeId} audit 준비 중…`,'warn');
  const detail=await api(`/api/stage1/experiments/${experimentId}`);
  const trade=(detail.experiment?.result?.closed_trades||[]).find(item=>Number(item.trade_id)===tradeId);
  if(!trade)throw new Error(`Trade #${tradeId} evidence를 찾지 못했습니다.`);
  const document=clone(detail.chart_document);
  const entryTime=chartTimeForSource(document,trade.entry_time);
  const exitTime=chartTimeForSource(document,trade.exit_time);
  if(entryTime===undefined||exitTime===undefined)throw new Error(`Trade #${tradeId}의 차트 시간을 찾지 못했습니다.`);

  document.references=[...(document.references||[]),
    {price:Number(trade.entry_price),title:`Trade #${tradeId} ENTRY`},
    {price:Number(trade.exit_price),title:`Trade #${tradeId} EXIT`}];
  if(entryTime!==exitTime){
    document.geometries=[...(document.geometries||[]),{kind:'vertical-region',fromTime:entryTime,toTime:exitTime}];
  }
  document.markers=[...(document.markers||[]),
    {time:entryTime,position:'belowBar',shape:'arrowUp',color:'#e6a43d',text:`#${tradeId} ENTRY`,size:2},
    {time:exitTime,position:'aboveBar',shape:'arrowDown',color:'#e6a43d',text:`#${tradeId} EXIT`,size:2}];

  markRows(row);
  renderSelectedTrade(trade);
  if($('analysis'))$('analysis').textContent=JSON.stringify({
    trade_id:trade.trade_id,
    signal_time:trade.signal_time,
    entry_fill_time:trade.entry_time,
    entry_price:trade.entry_price,
    exit_signal_time:trade.exit_signal_time,
    exit_fill_time:trade.exit_time,
    exit_price:trade.exit_price,
    entry_reason:trade.entry_reason,
    exit_reason:trade.exit_reason,
    return_pct:trade.return_pct,
    mfe_pct:trade.mfe_pct,
    mae_pct:trade.mae_pct,
    net_pnl:trade.net_pnl,
    holding_bars:trade.holding_bars,
  },null,2);
  sendChart(document);
  status(`Trade #${tradeId} 선택 · 차트 ENTRY/EXIT/보유구간 강조`,'ok');
}
function activateFromEvent(event){
  const row=event.target?.closest?.('#trades tr[data-trade-id]');
  if(!row)return false;
  event.preventDefault();
  event.stopImmediatePropagation();
  inspect(row).catch(error=>status(error.message||String(error),'bad'));
  return true;
}
document.addEventListener('click',activateFromEvent,true);
document.addEventListener('keydown',event=>{
  if(!['Enter',' '].includes(event.key))return;
  activateFromEvent(event);
},true);
const trades=$('trades');
if(trades){
  const refresh=()=>markRows(null);
  new MutationObserver(refresh).observe(trades,{childList:true});
  refresh();
}
})();
