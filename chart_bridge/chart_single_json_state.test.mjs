import http from 'node:http';
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { createChartPlatformServer } from './chart_platform_server.mjs';

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return `http://127.0.0.1:${server.address().port}`;
}

async function withServer(root, run) {
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  const server = createChartPlatformServer({ root, repository });
  const base = await listen(server);
  try { await run(base); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

const state = {
  schemaVersion: 1,
  visualsVisible: true,
  display: { indicatorSyncEnabled: false },
  workspace: {
    primaryInstrument: { kind: 'INDEX', code: '001', name: 'KOSPI' },
    timeframe: { period: 'minute', interval: '5' },
    baseDate: '2026-09-01',
    visibleCount: 163,
    priceDisplayMode: 'price',
    viewport: { logicalRange: { from: 20.5, to: 182.5 } },
  },
  addons: {
    'drawing.test': {
      enabled: true,
      definitionId: 'drawing.test',
      visible: true,
      state: {
        points: [{ x: 101.25, y: 220.75 }],
        __layout: { panes: { primary: { height: 287 } } },
      },
    },
  },
};

test('product server persists and restores the entire chart state through one JSON document', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'dsl-chart-state-'));
  try {
    await withServer(root, async base => {
      const saved = await fetch(`${base}/api/chart/addons/state`, {
        method: 'PUT',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(state),
      });
      assert.equal(saved.status, 200);
    });

    await withServer(root, async base => {
      const restored = await fetch(`${base}/api/chart/addons/state`);
      assert.equal(restored.status, 200);
      assert.deepEqual(await restored.json(), state);
    });

    const files = (await readdir(path.join(root, '.runtime', 'chart-addons'))).filter(name => name.endsWith('.json'));
    assert.deepEqual(files, ['chart-state.json']);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('browser unload POST writes the same full state route rather than a special timeframe file', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'dsl-chart-state-post-'));
  try {
    await withServer(root, async base => {
      const posted = await fetch(`${base}/api/chart/addons/state`, {
        method: 'POST',
        headers: { 'content-type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify(state),
      });
      assert.equal(posted.status, 200);
      const restored = await (await fetch(`${base}/api/chart/addons/state`)).json();
      assert.deepEqual(restored.workspace.timeframe, { period: 'minute', interval: '5' });
      assert.deepEqual(restored.addons['drawing.test'].state.points, [{ x: 101.25, y: 220.75 }]);
    });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
