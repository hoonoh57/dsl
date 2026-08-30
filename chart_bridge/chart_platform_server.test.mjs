import http from 'node:http';
import test from 'node:test';
import assert from 'node:assert/strict';

import { createChartPlatformServer, normalizeKiwoomEnv } from './chart_platform_server.mjs';

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

test('legacy Kiwoom mock env maps to chart bridge contract without overwriting explicit values', () => {
  const env = {
    KIWOOM_ENV: 'mock',
    KIWOOM_APP_KEY: 'legacy-app',
    KIWOOM_SECRET_KEY: 'legacy-secret',
  };
  normalizeKiwoomEnv(env);
  assert.equal(env.KIWOOM_MOCK, 'true');
  assert.equal(env.KIWOOM_MOCK_APP_KEY, 'legacy-app');
  assert.equal(env.KIWOOM_MOCK_SECRET_KEY, 'legacy-secret');

  const explicit = {
    KIWOOM_ENV: 'mock',
    KIWOOM_APP_KEY: 'legacy-app',
    KIWOOM_SECRET_KEY: 'legacy-secret',
    KIWOOM_MOCK_APP_KEY: 'explicit-app',
    KIWOOM_MOCK_SECRET_KEY: 'explicit-secret',
  };
  normalizeKiwoomEnv(explicit);
  assert.equal(explicit.KIWOOM_MOCK_APP_KEY, 'explicit-app');
  assert.equal(explicit.KIWOOM_MOCK_SECRET_KEY, 'explicit-secret');
});

test('legacy Kiwoom live env maps to real chart bridge contract', () => {
  const env = {
    KIWOOM_ENV: 'live',
    KIWOOM_APP_KEY: 'live-app',
    KIWOOM_SECRET_KEY: 'live-secret',
  };
  normalizeKiwoomEnv(env);
  assert.equal(env.KIWOOM_MOCK, 'false');
  assert.equal(env.KIWOOM_REAL_APP_KEY, 'live-app');
  assert.equal(env.KIWOOM_REAL_SECRET_KEY, 'live-secret');
});

test('market-data BigInt is serialized without ERR_HTTP_HEADERS_SENT and server remains alive', async () => {
  const repository = {
    async loadClosePanel() { return [{ code: '005930', volume: 12345678901234567890n }]; },
    async loadDailyPanel() { return []; },
  };

  await withServer(repository, async base => {
    const marketResponse = await fetch(`${base}/__cascade/market-data/daily-closes`);
    assert.equal(marketResponse.status, 200);
    const market = await marketResponse.json();
    assert.equal(market.rows[0].volume, '12345678901234567890');

    const healthResponse = await fetch(`${base}/__chart_health`);
    assert.equal(healthResponse.status, 200);
    const health = await healthResponse.json();
    assert.equal(health.status, 'ok');
    assert.equal(health.app, 'dsl-chart-bridge');
  });
});

test('DSL-owned chart composition shell and browser extension are served without modifying vendor files', async () => {
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  await withServer(repository, async base => {
    const html = await (await fetch(`${base}/`)).text();
    assert.match(html, /DSL STRATEGY ENABLED/);
    assert.match(html, /\/__dsl\/bootstrap\.mjs/);

    const bootstrap = await fetch(`${base}/__dsl/bootstrap.mjs`);
    assert.equal(bootstrap.status, 200);
    assert.match(await bootstrap.text(), /strategy\.dsl-manager/);

    const addon = await fetch(`${base}/__dsl/DslStrategyAddon.mjs`);
    assert.equal(addon.status, 200);
    assert.match(await addon.text(), /DSL Strategy Manager/);
  });
});

test('DSL evaluate route proxies chart payload to Live Studio Core boundary', async () => {
  let received;
  const upstream = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(Buffer.from(chunk));
    received = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end(JSON.stringify({ evaluation: { engine: 'core.backtest.BacktestEngine' }, markers: [{ time: '2026-01-02', text: 'BUY' }], metrics_numeric: { trade_count: 1 } }));
  });
  const upstreamBase = await listen(upstream);
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  try {
    await withServer(repository, async base => {
      const payload = { dsl_code: 'strategy "X" { timeframe = "1d" }', market: { time: ['2026-01-01', '2026-01-02'], open: [1, 1], high: [1, 1], low: [1, 1], close: [1, 1], volume: [0, 0] } };
      const response = await fetch(`${base}/__dsl/evaluate`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
      assert.equal(response.status, 200);
      const result = await response.json();
      assert.equal(result.evaluation.engine, 'core.backtest.BacktestEngine');
      assert.equal(result.markers[0].text, 'BUY');
      assert.equal(received.dsl_code, payload.dsl_code);
      assert.deepEqual(received.market.close, [1, 1]);
    }, { dslStudioUrl: upstreamBase });
  } finally {
    await new Promise(resolve => upstream.close(resolve));
  }
});
