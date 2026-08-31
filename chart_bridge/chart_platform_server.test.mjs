import http from 'node:http';
import test from 'node:test';
import assert from 'node:assert/strict';

import { createChartPlatformServer, normalizeKiwoomEnv } from './chart_platform_server.mjs';
import { chartBarsToDslMarket } from './browser/DslChartMarketAdapter.mjs';
import { assertDslChartTimeframeCompatible } from './browser/DslChartTimeframeGuard.mjs';

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  return `http://127.0.0.1:${address.port}`;
}

async function withServer(repository, run, options = {}) {
  const server = createChartPlatformServer({ repository, ...options });
  const base = await listen(server);
  try { await run(base); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

test('chart-to-DSL adapter uses tradingDate for daily bars and epoch time for intraday bars', () => {
  const daily = chartBarsToDslMarket([
    { tradingDate: '2026-08-20', open: 100, high: 110, low: 95, close: 105, volume: 10 },
    { tradingDate: '2026-08-21', open: 105, high: 112, low: 101, close: 108, volume: 11 },
  ]);
  assert.deepEqual(daily.time, ['2026-08-20', '2026-08-21']);
  assert.doesNotMatch(daily.time.join(','), /0000-00-00/);

  const intraday = chartBarsToDslMarket([
    { tradingDate: '2026-08-21', time: Date.UTC(2026, 7, 21, 0, 0, 0) / 1000, open: 100, high: 101, low: 99, close: 100, volume: 1 },
  ]);
  assert.equal(intraday.time[0], '20260821000000');
});

test('DSL chart timeframe guard fails closed on mismatched chart timeframe', () => {
  assert.doesNotThrow(() => assertDslChartTimeframeCompatible('1m', { request: { period: 'minute', interval: '1' } }));
  assert.throws(
    () => assertDslChartTimeframeCompatible('1m', { request: { period: 'day' } }),
    /현재 차트 1일과 DSL timeframe 1m이 일치하지 않습니다/,
  );
  assert.throws(
    () => assertDslChartTimeframeCompatible('1m', { request: { period: 'minute', interval: '5' } }),
    /현재 차트 5분과 DSL timeframe 1m이 일치하지 않습니다/,
  );
});

test('legacy Kiwoom mock env maps to chart bridge contract without overwriting explicit values', () => {
  const env = { KIWOOM_ENV: 'mock', KIWOOM_APP_KEY: 'legacy-app', KIWOOM_SECRET_KEY: 'legacy-secret' };
  normalizeKiwoomEnv(env);
  assert.equal(env.KIWOOM_MOCK, 'true');
  assert.equal(env.KIWOOM_MOCK_APP_KEY, 'legacy-app');
  assert.equal(env.KIWOOM_MOCK_SECRET_KEY, 'legacy-secret');
  const explicit = { ...env, KIWOOM_MOCK_APP_KEY: 'explicit-app', KIWOOM_MOCK_SECRET_KEY: 'explicit-secret' };
  normalizeKiwoomEnv(explicit);
  assert.equal(explicit.KIWOOM_MOCK_APP_KEY, 'explicit-app');
  assert.equal(explicit.KIWOOM_MOCK_SECRET_KEY, 'explicit-secret');
});

test('legacy Kiwoom live env maps to real chart bridge contract', () => {
  const env = { KIWOOM_ENV: 'live', KIWOOM_APP_KEY: 'live-app', KIWOOM_SECRET_KEY: 'live-secret' };
  normalizeKiwoomEnv(env);
  assert.equal(env.KIWOOM_MOCK, 'false');
  assert.equal(env.KIWOOM_REAL_APP_KEY, 'live-app');
  assert.equal(env.KIWOOM_REAL_SECRET_KEY, 'live-secret');
});

test('market-data BigInt is serialized without ERR_HTTP_HEADERS_SENT and server remains alive', async () => {
  const repository = { async loadClosePanel() { return [{ code: '005930', volume: 12345678901234567890n }]; }, async loadDailyPanel() { return []; } };
  await withServer(repository, async base => {
    const market = await (await fetch(`${base}/__cascade/market-data/daily-closes`)).json();
    assert.equal(market.rows[0].volume, '12345678901234567890');
    const health = await (await fetch(`${base}/__chart_health`)).json();
    assert.equal(health.status, 'ok');
  });
});

test('DSL-owned chart shell serves catalog validation plus editable inserted strategy lifecycle', async () => {
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  await withServer(repository, async base => {
    const html = await (await fetch(`${base}/`)).text();
    assert.match(html, /DSL STRATEGY ENABLED/);

    const bootstrap = await (await fetch(`${base}/__dsl/bootstrap.mjs`)).text();
    assert.match(bootstrap, /등록 DSL 차트 검증/);
    assert.match(bootstrap, /DslCatalogValidationManager\.mjs/);
    assert.match(bootstrap, /DslStrategyRendererAddon\.mjs/);
    assert.match(bootstrap, /DslStrategyPropertiesEditor\.mjs/);
    assert.match(bootstrap, /editor:\s*\{/);
    assert.doesNotMatch(bootstrap, /dslRuntimeSeed/);

    const validationEditor = await (await fetch(`${base}/__dsl/DslCatalogValidationManager.mjs`)).text();
    assert.match(validationEditor, /등록 DSL/);
    assert.match(validationEditor, /문법 검증/);
    assert.match(validationEditor, /차트 삽입/);
    assert.match(validationEditor, /DslChartMarketAdapter\.mjs/);
    assert.match(validationEditor, /DslChartTimeframeGuard\.mjs/);
    assert.doesNotMatch(validationEditor, /function timeText/);
    assert.doesNotMatch(validationEditor, /\+ 새 DSL 전략/);
    assert.doesNotMatch(validationEditor, /삽입 기록/);

    const propertiesEditor = await (await fetch(`${base}/__dsl/DslStrategyPropertiesEditor.mjs`)).text();
    assert.match(propertiesEditor, /등록 DSL로 교체/);
    assert.match(propertiesEditor, /현재 차트에 적용/);
    assert.match(propertiesEditor, /삭제/);
    assert.match(propertiesEditor, /writeAddonState\(instanceId/);
    assert.match(propertiesEditor, /enabled: false/);

    const renderer = await (await fetch(`${base}/__dsl/DslStrategyRendererAddon.mjs`)).text();
    assert.match(renderer, /surface\.setMarkers/);
    assert.match(renderer, /markerPlugin.*setMarkers/s);
    assert.match(renderer, /DslChartMarketAdapter\.mjs/);
    assert.doesNotMatch(renderer, /createMarkers/);
  });
});

test('DSL catalog validate and evaluate routes proxy to Live Studio authority', async () => {
  const received = [];
  const upstream = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(Buffer.from(chunk));
    const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : undefined;
    received.push({ method: request.method, url: request.url, body });
    response.writeHead(200, { 'content-type': 'application/json' });
    if (request.url === '/api/features') {
      response.end(JSON.stringify({ count: 1, categories: [{ category: 'ta', features: [{ feature_id: 'ta.sma', title: 'SMA', dsl_code: 'strategy "S" { timeframe = "1d" }' }] }] }));
    } else if (request.url === '/api/validate') {
      response.end(JSON.stringify({ ok: true, strategy: 'S', timeframe: '1d', parser: 'PASS', semantic: 'PASS' }));
    } else {
      response.end(JSON.stringify({ evaluation: { engine: 'core.backtest.BacktestEngine' }, markers: [{ time: '2026-01-02', text: 'BUY' }], metrics_numeric: { trade_count: 1 } }));
    }
  });
  const upstreamBase = await listen(upstream);
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  try {
    await withServer(repository, async base => {
      const catalog = await (await fetch(`${base}/__dsl/catalog`)).json();
      assert.equal(catalog.categories[0].features[0].feature_id, 'ta.sma');

      const dslCode = 'strategy "S" { timeframe = "1d" }';
      const validation = await (await fetch(`${base}/__dsl/validate`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ dsl_code: dslCode }) })).json();
      assert.equal(validation.parser, 'PASS');
      assert.equal(validation.semantic, 'PASS');

      const payload = { dsl_code: dslCode, market: { time: ['2026-01-01', '2026-01-02'], open: [1, 1], high: [1, 1], low: [1, 1], close: [1, 1], volume: [0, 0] } };
      const result = await (await fetch(`${base}/__dsl/evaluate`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) })).json();
      assert.equal(result.evaluation.engine, 'core.backtest.BacktestEngine');
      assert.equal(result.markers[0].text, 'BUY');
      assert.deepEqual(received.map(item => item.url), ['/api/features', '/api/validate', '/api/evaluate']);
      assert.deepEqual(received[2].body.market.close, [1, 1]);
    }, { dslStudioUrl: upstreamBase });
  } finally {
    await new Promise(resolve => upstream.close(resolve));
  }
});
