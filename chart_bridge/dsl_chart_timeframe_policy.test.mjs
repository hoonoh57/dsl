import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

import {
  applyDslTimeframe,
  assertDslChartTimeframeCompatible,
  dslTimeframeFromChart,
  dslTimeframeFromSource,
} from './browser/DslChartTimeframeGuard.mjs';

const browserUrl = new URL('./browser/', import.meta.url);

async function browserSource(name) {
  return readFile(fileURLToPath(new URL(name, browserUrl)), 'utf8');
}

test('chart timeframe is converted to a DSL timeframe without a 1d special case', () => {
  assert.equal(dslTimeframeFromChart({ request: { period: 'minute', interval: '5' } }), '5m');
  assert.equal(dslTimeframeFromChart({ request: { period: 'minute', interval: '60' } }), '60m');
  assert.equal(dslTimeframeFromChart({ request: { period: 'day' } }), '1d');
  assert.equal(dslTimeframeFromChart({ request: { period: 'week' } }), '1w');
  assert.equal(dslTimeframeFromChart({ request: { period: 'month' } }), '1M');
});

test('registered DSL timeframe can be changed generically before Parser validation', () => {
  const source = `strategy "Feature_ta_macd" {\n  timeframe = "1d"\n  value = ta.macd(close, 12, 26, "exponential")\n}`;
  const changed = applyDslTimeframe(source, '5m');
  assert.equal(dslTimeframeFromSource(source), '1d');
  assert.equal(dslTimeframeFromSource(changed), '5m');
  assert.match(changed, /timeframe = "5m"/);
  assert.doesNotMatch(changed, /timeframe = "1d"/);
});

test('timeframe declaration is inserted when a DSL relies on the Parser 1d default', () => {
  const source = `strategy "NoTimeframe" {\n  value = ta.sma(close, 5)\n}`;
  assert.equal(dslTimeframeFromSource(source), '1d');
  const changed = applyDslTimeframe(source, '3m');
  assert.match(changed, /strategy "NoTimeframe" \{\n  timeframe = "3m"/);
});

test('chart compatibility treats 60m and 1h as the same duration', () => {
  const chart = { request: { period: 'minute', interval: '60' } };
  assert.doesNotThrow(() => assertDslChartTimeframeCompatible('60m', chart));
  assert.doesNotThrow(() => assertDslChartTimeframeCompatible('1h', chart));
  assert.throws(() => assertDslChartTimeframeCompatible('5m', chart), /일치하지 않습니다/);
});

test('all active chart DSL execution paths expose explicit timeframe provenance', async () => {
  const manager = await browserSource('DslCatalogValidationManager.mjs');
  assert.match(manager, /data-timeframe/);
  assert.match(manager, /applyDslTimeframe/);
  assert.match(manager, /data_timeframe:\s*strategy\.timeframe/);

  const renderer = await browserSource('DslStrategyRendererAddon.mjs');
  assert.match(renderer, /assertDslChartTimeframeCompatible/);
  assert.match(renderer, /data_timeframe:\s*strategy\.timeframe/);
});
