function normalizeDslTimeframe(value) {
  const text = String(value ?? '').trim();
  const match = /^(\d+)([mhdwM])$/.exec(text);
  if (!match) throw new Error(`지원하지 않는 DSL timeframe: ${text || '(empty)'}`);
  const count = Number(match[1]);
  if (!Number.isInteger(count) || count < 1) throw new Error(`잘못된 DSL timeframe: ${text}`);
  const unit = match[2];
  if (unit === 'm') return { text, period: 'minute', interval: String(count), label: `${count}분` };
  if (unit === 'h') return { text, period: 'minute', interval: String(count * 60), label: `${count}시간` };
  if (unit === 'd') return { text, period: 'day', interval: String(count), label: `${count}일` };
  if (unit === 'w') return { text, period: 'week', interval: String(count), label: `${count}주` };
  return { text, period: 'month', interval: String(count), label: `${count}개월` };
}

function chartTimeframeOf(workspaceContext = {}) {
  const request = workspaceContext?.request ?? workspaceContext?.currentRequest ?? workspaceContext;
  const period = String(request?.period ?? '').trim();
  const interval = request?.interval === undefined ? undefined : String(request.interval).trim();
  if (!period) return undefined;
  return { period, interval };
}

function positiveInterval(value, fallback = 1) {
  const count = value === undefined || value === '' ? fallback : Number(value);
  if (!Number.isInteger(count) || count < 1) throw new Error(`잘못된 차트 interval: ${value}`);
  return count;
}

export function dslTimeframeFromChart(workspaceContext = {}) {
  const current = chartTimeframeOf(workspaceContext);
  if (!current) throw new Error('현재 차트 timeframe을 확인할 수 없습니다.');
  const count = positiveInterval(current.interval, 1);
  if (current.period === 'minute') return `${count}m`;
  if (current.period === 'day') return `${count}d`;
  if (current.period === 'week') return `${count}w`;
  if (current.period === 'month') return `${count}M`;
  throw new Error(`지원하지 않는 차트 timeframe: ${current.period}`);
}

export function dslTimeframeFromSource(dslCode) {
  const source = String(dslCode ?? '');
  const match = /^\s*timeframe\s*=\s*["'](\d+(?:m|h|d|w|M))["']\s*;?\s*$/m.exec(source);
  return match ? normalizeDslTimeframe(match[1]).text : '1d';
}

export function applyDslTimeframe(dslCode, timeframe) {
  const source = String(dslCode ?? '');
  const normalized = normalizeDslTimeframe(timeframe).text;
  const declaration = /^(\s*timeframe\s*=\s*)(["'])(\d+(?:m|h|d|w|M))\2(\s*;?\s*)$/m;
  if (declaration.test(source)) {
    return source.replace(declaration, (_full, prefix, quote, _previous, suffix) => `${prefix}${quote}${normalized}${quote}${suffix}`);
  }
  const strategyHeader = /(\bstrategy\s+(?:"[^"]*"|'[^']*')\s*\{)/;
  if (!strategyHeader.test(source)) throw new Error('strategy 선언을 찾을 수 없어 timeframe을 적용할 수 없습니다.');
  return source.replace(strategyHeader, `$1\n  timeframe = "${normalized}"`);
}

export function assertDslChartTimeframeCompatible(dslTimeframe, workspaceContext = {}) {
  const expected = normalizeDslTimeframe(dslTimeframe);
  const current = chartTimeframeOf(workspaceContext);
  if (!current) throw new Error(`현재 차트 timeframe을 확인할 수 없습니다. DSL ${dslTimeframe} 검증을 중단합니다.`);

  const samePeriod = current.period === expected.period;
  const currentInterval = positiveInterval(current.interval, 1);
  const expectedInterval = positiveInterval(expected.interval, 1);
  const sameInterval = currentInterval === expectedInterval;

  if (!samePeriod || !sameInterval) {
    const currentLabel = current.period === 'minute'
      ? `${currentInterval}분`
      : `${currentInterval}${current.period === 'day' ? '일' : current.period === 'week' ? '주' : current.period === 'month' ? '개월' : ` ${current.period}`}`;
    throw new Error(`현재 차트 ${currentLabel}과 DSL timeframe ${dslTimeframe}이 일치하지 않습니다. ${expected.label} 차트로 전환한 뒤 검증하세요.`);
  }
  return { expected, current };
}
