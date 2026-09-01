import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { createChartPlatformServer } from './chart_platform_server.mjs';
import {
  WORKSPACE_TIMEFRAME_ROUTE,
  WorkspaceTimeframeJsonStore,
} from './workspace_timeframe_persistence.mjs';

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return `http://127.0.0.1:${server.address().port}`;
}

async function withServer(file, run) {
  const repository = { async loadClosePanel() { return []; }, async loadDailyPanel() { return []; } };
  const server = createChartPlatformServer({ repository, workspaceTimeframeFile: file });
  const base = await listen(server);
  try { await run(base); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

test('workspace timeframe JSON store is versioned, explicit, and fail-closed', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'dsl-timeframe-store-'));
  const file = path.join(directory, 'chart-workspace-timeframe.json');
  try {
    const store = new WorkspaceTimeframeJsonStore(file);
    assert.equal(await store.load(), undefined);
    assert.deepEqual(await store.save({ period: 'minute', interval: '5' }), { period: 'minute', interval: '5' });
    assert.deepEqual(await new WorkspaceTimeframeJsonStore(file).load(), { period: 'minute', interval: '5' });

    const onDisk = JSON.parse(await readFile(file, 'utf8'));
    assert.deepEqual(onDisk, {
      schemaVersion: 1,
      timeframe: { period: 'minute', interval: '5' },
    });
    assert.throws(() => store.save({ period: 'minute', interval: '999' }), /unsupported/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('chart bridge restores the same timeframe after a complete server restart', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'dsl-timeframe-http-'));
  const file = path.join(directory, 'chart-workspace-timeframe.json');
  try {
    await withServer(file, async base => {
      const absent = await fetch(`${base}${WORKSPACE_TIMEFRAME_ROUTE}`);
      assert.equal(absent.status, 404);

      const saved = await fetch(`${base}${WORKSPACE_TIMEFRAME_ROUTE}`, {
        method: 'PUT',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ period: 'minute', interval: '5' }),
      });
      assert.equal(saved.status, 200);
      assert.deepEqual((await saved.json()).timeframe, { period: 'minute', interval: '5' });
    });

    await withServer(file, async base => {
      const restored = await fetch(`${base}${WORKSPACE_TIMEFRAME_ROUTE}`);
      assert.equal(restored.status, 200);
      assert.deepEqual(await restored.json(), { period: 'minute', interval: '5' });
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('unload beacon POST uses the same validation and cannot persist unsupported values', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'dsl-timeframe-post-'));
  const file = path.join(directory, 'chart-workspace-timeframe.json');
  try {
    await withServer(file, async base => {
      const invalid = await fetch(`${base}${WORKSPACE_TIMEFRAME_ROUTE}`, {
        method: 'POST',
        headers: { 'content-type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify({ period: 'minute', interval: '999' }),
      });
      assert.equal(invalid.status, 400);

      const valid = await fetch(`${base}${WORKSPACE_TIMEFRAME_ROUTE}`, {
        method: 'POST',
        headers: { 'content-type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify({ period: 'week' }),
      });
      assert.equal(valid.status, 200);
    });
    assert.deepEqual(await new WorkspaceTimeframeJsonStore(file).load(), { period: 'week' });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
