function pad2(value) {
  return String(value).padStart(2, '0');
}

export function chartTimeToDslText(value, index) {
  if (typeof value === 'string') {
    const text = value.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text;
    if (/^\d{8}$/.test(text)) return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
    return text;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    const date = new Date(value * 1000);
    const yyyy = date.getUTCFullYear();
    const mm = pad2(date.getUTCMonth() + 1);
    const dd = pad2(date.getUTCDate());
    const hh = pad2(date.getUTCHours());
    const mi = pad2(date.getUTCMinutes());
    const ss = pad2(date.getUTCSeconds());
    return `${yyyy}${mm}${dd}${hh}${mi}${ss}`;
  }
  if (value && typeof value === 'object' && Number.isInteger(value.year) && Number.isInteger(value.month) && Number.isInteger(value.day)) {
    return `${String(value.year).padStart(4, '0')}-${pad2(value.month)}-${pad2(value.day)}`;
  }
  throw new Error(`Chart bar ${index} has no valid time or tradingDate.`);
}

export function chartBarsToDslMarket(bars = []) {
  const clean = Array.isArray(bars)
    ? bars.filter(bar => ['open', 'high', 'low', 'close'].every(key => Number.isFinite(Number(bar?.[key]))))
    : [];
  return {
    time: clean.map((bar, index) => chartTimeToDslText(bar.time ?? bar.tradingDate, index)),
    open: clean.map(bar => Number(bar.open)),
    high: clean.map(bar => Number(bar.high)),
    low: clean.map(bar => Number(bar.low)),
    close: clean.map(bar => Number(bar.close)),
    volume: clean.map(bar => Number.isFinite(Number(bar.volume)) ? Number(bar.volume) : 0),
    _meta: { source: 'condition1516_chart_loaded_bars', provenance: 'DSL_CHART_BRIDGE' },
  };
}
