export const WORKSPACE_TIMEFRAME_ROUTE = '/api/chart/workspace/timeframe';
export const WORKSPACE_TIMEFRAME_PERSISTENCE_PORT = '__chartWorkspaceTimeframePersistence';

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function errorText(error) {
  return String(error?.message ?? error);
}

export async function installWorkspaceTimeframeJsonPersistence({
  target = globalThis,
  fetchPort = globalThis.fetch?.bind(globalThis),
  navigatorPort = globalThis.navigator,
} = {}) {
  if (!fetchPort) throw new Error('workspace timeframe persistence requires fetch().');

  let current;
  try {
    const response = await fetchPort(WORKSPACE_TIMEFRAME_ROUTE, {
      method: 'GET',
      headers: { accept: 'application/json' },
      cache: 'no-store',
    });
    if (response.ok) current = cloneJson(await response.json());
    else if (response.status !== 404) throw new Error(`workspace timeframe load failed: HTTP ${response.status}`);
  } catch (error) {
    target.console?.error?.(`[PERSISTENCE] ${errorText(error)}`);
  }

  let queue = Promise.resolve();
  const saveNow = async payload => {
    const response = await fetchPort(WORKSPACE_TIMEFRAME_ROUTE, {
      method: 'PUT',
      headers: { 'content-type': 'application/json;charset=UTF-8' },
      body: JSON.stringify(payload),
      keepalive: true,
    });
    if (!response.ok) throw new Error(`workspace timeframe save failed: HTTP ${response.status}`);
  };

  const port = {
    read() { return cloneJson(current); },
    write(value) {
      current = cloneJson(value);
      const payload = cloneJson(current);
      const operation = queue.then(() => saveNow(payload));
      queue = operation.catch(error => {
        target.console?.error?.(`[PERSISTENCE] ${errorText(error)}`);
      });
      return true;
    },
    async whenIdle() { await queue; },
    flushOnUnload() {
      if (current === undefined) return false;
      const body = JSON.stringify(current);
      try {
        if (typeof navigatorPort?.sendBeacon === 'function') {
          return navigatorPort.sendBeacon(WORKSPACE_TIMEFRAME_ROUTE, body) !== false;
        }
        void fetchPort(WORKSPACE_TIMEFRAME_ROUTE, {
          method: 'POST',
          headers: { 'content-type': 'application/json;charset=UTF-8' },
          body,
          keepalive: true,
        });
        return true;
      } catch {
        return false;
      }
    },
  };

  target[WORKSPACE_TIMEFRAME_PERSISTENCE_PORT] = port;
  return port;
}
