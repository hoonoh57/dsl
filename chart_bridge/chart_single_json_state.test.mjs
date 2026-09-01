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
  stateRevision: 17,
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
      assert.equal(restored.stateRevision, 17);
      assert.deepEqual(restored.workspace.timeframe, { period: 'minute', interval: '5' });
      assert.deepEqual(restored.addons['drawing.test'].state.points, [{ x: 101.25, y: 220.75 }]);
    });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('late stale PUT cannot overwrite newer browser-close state', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'dsl-chart-state-order-'));
  try {
    await withServer(root, async base => {
      const latest = structuredClone(state);
      latest.stateRevision = 42;
      latest.workspace.visibleCount = 242;
      latest.workspace.layout = { primaryPanes: { priceHeight: 510, volumeHeight: 135 } };
      latest.addons['indicator.supertrend.2'] = {
        enabled: true,
        definitionId: 'indicator.supertrend',
        visible: true,
        state: { atrPeriod: 14, multiplier: 2 },
      };
      const stale = structuredClone(state);
      stale.stateRevision = 41;
      stale.workspace.visibleCount = 141;

      const closeSaved = await fetch(`${base}/api/chart/addons/state`, {
        method: 'POST',
        headers: { 'content-type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify(latest),
      });
      assert.equal(closeSaved.status, 200);

      const lateOldSave = await fetch(`${base}/api/chart/addons/state`, {
        method: 'PUT',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(stale),
      });
      assert.equal(lateOldSave.status, 200);

      const restored = await (await fetch(`${base}/api/chart/addons/state`)).json();
      assert.equal(restored.stateRevision, 42);
      assert.equal(restored.workspace.visibleCount, 242);
      assert.deepEqual(restored.workspace.layout.primaryPanes, { priceHeight: 510, volumeHeight: 135 });
      assert.equal(restored.addons['indicator.supertrend.2'].enabled, true);
    });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});