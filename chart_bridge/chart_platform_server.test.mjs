import test from 'node:test';
import assert from 'node:assert/strict';

import { createChartPlatformServer } from './chart_platform_server.mjs';

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
