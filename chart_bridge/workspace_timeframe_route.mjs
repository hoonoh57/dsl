export const WORKSPACE_TIMEFRAME_ROUTE = '/api/chart/workspace/timeframe';

const MAX_REQUEST_BYTES = 64 * 1024;

function requestPath(url) {
  try { return new URL(String(url ?? '/'), 'http://127.0.0.1').pathname; }
  catch { return '/'; }
}

function sendJson(response, statusCode, value) {
  response.statusCode = statusCode;
  response.setHeader('content-type', 'application/json;charset=UTF-8');
  response.setHeader('cache-control', 'no-store');
  response.end(JSON.stringify(value));
}

async function readJsonObject(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    size += buffer.length;
    if (size > MAX_REQUEST_BYTES) throw new Error('workspace timeframe request exceeds 64 KiB.');
    chunks.push(buffer);
  }
  let value;
  try { value = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw new Error('workspace timeframe request must be valid JSON.'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('workspace timeframe request must be a JSON object.');
  return value;
}

export function createWorkspaceTimeframePersistenceMiddleware(store) {
  if (!store || typeof store.load !== 'function' || typeof store.save !== 'function') {
    throw new Error('workspace timeframe route requires a persistence store.');
  }

  return async (request, response, next) => {
    if (requestPath(request.url) !== WORKSPACE_TIMEFRAME_ROUTE) { next(); return; }
    const method = String(request.method ?? '').toUpperCase();

    if (method === 'GET') {
      try {
        const value = await store.load();
        if (!value) { sendJson(response, 404, { error: 'WORKSPACE_TIMEFRAME_NOT_FOUND' }); return; }
        sendJson(response, 200, value);
      } catch (error) {
        sendJson(response, 500, { error: 'WORKSPACE_TIMEFRAME_LOAD_FAILED', message: String(error?.message ?? error) });
      }
      return;
    }

    if (method === 'PUT' || method === 'POST') {
      try {
        const value = await readJsonObject(request);
        sendJson(response, 200, { ok: true, timeframe: await store.save(value) });
      } catch (error) {
        sendJson(response, 400, { error: 'WORKSPACE_TIMEFRAME_SAVE_FAILED', message: String(error?.message ?? error) });
      }
      return;
    }

    response.setHeader('allow', 'GET, PUT, POST');
    sendJson(response, 405, { error: 'METHOD_NOT_ALLOWED' });
  };
}
