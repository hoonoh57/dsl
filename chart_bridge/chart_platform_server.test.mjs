import test from 'node:test';
import assert from 'node:assert/strict';

import { createChartPlatformServer, normalizeKiwoomEnv } from './chart_platform_server.mjs';

async function withServer(repository, run) {
  const server = createChartPlatformServer({ repository });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  try {
    const address = server.address();
    await run(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
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
    async loadClosePanel() {
      return [{ code: '005930', volume: 12345678901234567890n }];
    },
    async loadDailyPanel() {
      return [];
    },
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
