import test from 'node:test';
import assert from 'node:assert/strict';

import {
  WORKSPACE_TIMEFRAME_PERSISTENCE_PORT,
  WORKSPACE_TIMEFRAME_ROUTE,
  installWorkspaceTimeframeJsonPersistence,
} from './WorkspaceTimeframeJsonPersistence.mjs';

function response(status, body) {
  return {
    status,
    ok: status >= 200 && status < 300,
    async json() { return body; },
  };
}

test('JSON persistence port restores before mount, saves in order, and flushes latest value on unload', async () => {
  const calls = [];
  const beacons = [];
  const errors = [];
  const target = { console: { error(message) { errors.push(message); } } };
  const fetchPort = async (url, options = {}) => {
    calls.push({ url, options: { ...options } });
    if ((options.method ?? 'GET') === 'GET') return response(200, { period: 'minute', interval: '5' });
    return response(200, { ok: true });
  };
  const navigatorPort = {
    sendBeacon(url, body) { beacons.push({ url, body }); return true; },
  };

  const port = await installWorkspaceTimeframeJsonPersistence({ target, fetchPort, navigatorPort });
  assert.equal(target[WORKSPACE_TIMEFRAME_PERSISTENCE_PORT], port);
  assert.deepEqual(port.read(), { period: 'minute', interval: '5' });

  assert.equal(port.write({ period: 'minute', interval: '15' }), true);
  assert.equal(port.write({ period: 'day' }), true);
  await port.whenIdle();

  const writes = calls.filter(call => call.options.method === 'PUT');
  assert.deepEqual(writes.map(call => JSON.parse(call.options.body)), [
    { period: 'minute', interval: '15' },
    { period: 'day' },
  ]);
  assert.ok(writes.every(call => call.options.keepalive === true));
  assert.equal(port.flushOnUnload(), true);
  assert.deepEqual(beacons, [{ url: WORKSPACE_TIMEFRAME_ROUTE, body: JSON.stringify({ period: 'day' }) }]);
  assert.deepEqual(errors, []);
});

test('missing JSON state permits the shell fallback without failing startup', async () => {
  const target = { console: { error() { throw new Error('unexpected persistence error'); } } };
  const port = await installWorkspaceTimeframeJsonPersistence({
    target,
    navigatorPort: {},
    fetchPort: async () => response(404, { error: 'WORKSPACE_TIMEFRAME_NOT_FOUND' }),
  });
  assert.equal(port.read(), undefined);
});
