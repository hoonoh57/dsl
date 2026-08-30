function normalizeDslTimeframe(value) {
  const text = String(value ?? '').trim();
  const match = /^(\d+)([mhdwM])$/.exec(text);
  if (!match) throw new Error(`지원하지 않는 DSL timeframe: ${text || '(empty)'}`);
  const count = Number(match[1]);
  if (!Number.isInteger(count) || count < 1) throw new Error(`잘못된 DSL timeframe: ${text}`);
  const unit = match[2];
  if (unit === 'm') return { period: 'minute', interval: String(count), label: `${count}분` };
  if (unit === 'h') return { period: 'minute', interval: String(count * 60), label: `${count}시간` };
  if (unit === 'd') return { period: 'day', interval: undefined, label: `${count}일` };
  if (unit === 'w') return { period: 'week', interval: undefined, label: `${count}주` };
  return { period: 'month', interval: undefined, label: `${count}개월` };
}

function chartTimeframeOf(workspaceContext = {}) {
  const request = workspaceContext?.request ?? workspaceContext?.currentRequest ?? workspaceContext;
  const period = String(request?.period ?? '').trim();
  const interval = request?.interval === undefined ? undefined : String(request.interval).trim();
  if (!period) return undefined;
  return { period, interval };
}

export function assertDslChartTimeframeCompatible(dslTimeframe, workspaceContext = {}) {
  const expected = normalizeDslTimeframe(dslTimeframe);
  const current = chartTimeframeOf(workspaceContext);
  if (!current) throw new Error(`현재 차트 timeframe을 확인할 수 없습니다. DSL ${dslTimeframe} 검증을 중단합니다.`);

  const samePeriod = current.period === expected.period;
  const sameInterval = expected.period === 'minute'
    ? String(current.interval ?? '1') === String(expected.interval ?? '1')
    : true;

  if (!samePeriod || !sameInterval) {
    const currentLabel = current.period === 'minute' ? `${current.interval ?? '1'}분` : current.period;
    throw new Error(`현재 차트 ${currentLabel}과 DSL timeframe ${dslTimeframe}이 일치하지 않습니다. ${expected.label} 차트로 전환한 뒤 검증하세요.`);
  }
  return { expected, current };
}
