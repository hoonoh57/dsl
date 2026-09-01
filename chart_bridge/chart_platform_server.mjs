import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnvFile } from 'node:process';

import { ChartAddonJsonStore } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/server/chart/ChartAddonJsonStore.mjs';
import { MySqlDailyMarketDataRepository } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/server/market-data/MySqlDailyMarketDataRepository.mjs';
import { createChartAddonPersistenceMiddleware } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/shell/index-wysiwyg/ChartAddonPersistenceHttpHost.mjs';
import { createIndexWysiwygProxy, createIndexWysiwygProxyMiddleware } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/shell/index-wysiwyg/IndexWysiwygHttpHost.mjs';
import { WorkspaceTimeframeJsonStore, createWorkspaceTimeframePersistenceMiddleware } from '../persistence/chart_workspace/timeframe_json.mjs';

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_PROJECT_ROOT = path.resolve(moduleDir, '..');
export const DEFAULT_CHART_ROOT = path.resolve(DEFAULT_PROJECT_ROOT, 'vendor/kiwoom-condition/condition1516/chart-platform');
export const DEFAULT_DSL_BROWSER_ROOT = path.resolve(moduleDir, 'browser');

function tryLoad(file) {
  try { loadEnvFile(file); return true; }
  catch (error) { if (error?.code === 'ENOENT') return false; throw error; }
}

export function normalizeKiwoomEnv(env) {
  const modeText = String(env.KIWOOM_ENV ?? '').trim().toLowerCase();
  if (!env.KIWOOM_MOCK && modeText) {
    if (modeText === 'mock') env.KIWOOM_MOCK = 'true';
    else if (modeText === 'live' || modeText === 'real') env.KIWOOM_MOCK = 'false';
    else throw new Error('KIWOOM_ENV must be mock, live, or real.');
  }

  const isMock = String(env.KIWOOM_MOCK ?? 'true').trim().toLowerCase() !== 'false';
  const appKeyName = isMock ? 'KIWOOM_MOCK_APP_KEY' : 'KIWOOM_REAL_APP_KEY';
  const secretKeyName = isMock ? 'KIWOOM_MOCK_SECRET_KEY' : 'KIWOOM_REAL_SECRET_KEY';

  if (!env[appKeyName] && env.KIWOOM_APP_KEY) env[appKeyName] = env.KIWOOM_APP_KEY;
  if (!env[secretKeyName] && env.KIWOOM_SECRET_KEY) env[secretKeyName] = env.KIWOOM_SECRET_KEY;
  return env;
}

function jsonText(value) {
  return JSON.stringify(value, (_key, item) => typeof item === 'bigint' ? item.toString() : item);
}

function sendJson(response, statusCode, value) {
  const body = jsonText(value);
  if (response.headersSent) {
    if (!response.writableEnded) response.end();
    return false;
  }
  response.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
  });
  response.end(body);
  return true;
}

function listOf(value) {
  return String(value ?? '').split(',').map(item => item.trim()).filter(Boolean);
}

async function readBody(request, maxBytes = 8 * 1024 * 1024) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    size += buffer.length;
    if (size > maxBytes) throw new Error('request body exceeds 8 MiB limit.');
    chunks.push(buffer);
  }
  return Buffer.concat(chunks);
}

export function createSafeMarketDataMiddleware(repository) {
  if (!repository || typeof repository.loadClosePanel !== 'function') throw new Error('Market data repository is required.');
  return async function marketDataMiddleware(request, response, next) {
    const url = new URL(request.url || '/', 'http://127.0.0.1');
    if (request.method !== 'GET') { next(); return; }
    const codes = listOf(url.searchParams.get('codes'));
    const options = {
      from: url.searchParams.get('from'),
      to: url.searchParams.get('to'),
      markets: listOf(url.searchParams.get('markets')),
      ...(codes.length ? { codes } : {}),
    };
    try {
      if (url.pathname === '/__cascade/market-data/daily-closes') {
        sendJson(response, 200, { rows: await repository.loadClosePanel(options) });
        return;
      }
      if (url.pathname === '/__cascade/market-data/daily-panel') {
        if (typeof repository.loadDailyPanel !== 'function') throw new Error('Daily market metric panel is unavailable.');
        sendJson(response, 200, { rows: await repository.loadDailyPanel(options) });
        return;
      }
    } catch (error) {
      sendJson(response, 422, { message: error?.message ?? String(error) });
      return;
    }
    next();
  };
}

async function run(middleware, request, response) {
  let pass = false;
  await middleware(request, response, () => { pass = true; });
  return pass;
}

function safePath(root, urlPath) {
  const clean = decodeURIComponent(urlPath.split('?')[0]);
  const relative = clean === '/' ? 'index.html' : clean.replace(/^\/+/, '');
  const first = relative.split(/[\\/]/)[0];
  if (['.git', '.runtime', 'data'].includes(first)) return null;
  const resolved = path.resolve(root, relative);
  if (resolved !== root && !resolved.startsWith(root + path.sep)) return null;
  return resolved;
}

const mime = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.svg', 'image/svg+xml'],
]);

async function serveFile(response, file) {
  const body = await readFile(file);
  response.writeHead(200, {
    'content-type': mime.get(path.extname(file).toLowerCase()) || 'application/octet-stream',
    'cache-control': 'no-store',
  });
  response.end(body);
}

async function proxyStudio(request, response, studioBase, upstreamPath, method) {
  const actual = String(request.method ?? 'GET').toUpperCase();
  if (actual !== method) {
    sendJson(response, 405, { message: `${method} required.` });
    return;
  }
  try {
    const options = { method, headers: {} };
    if (method !== 'GET') {
      options.headers['content-type'] = 'application/json';
      options.body = await readBody(request);
    }
    const upstream = await fetch(`${studioBase}${upstreamPath}`, options);
    const text = await upstream.text();
    if (!response.headersSent) response.writeHead(upstream.status, {
      'content-type': upstream.headers.get('content-type') || 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    });
    if (!response.writableEnded) response.end(text);
  } catch (error) {
    sendJson(response, 502, { message: `DSL Studio unavailable: ${String(error?.message ?? error)}` });
  }
}

export function createChartPlatformServer({ root = DEFAULT_CHART_ROOT, env = process.env, repository, dslStudioUrl, workspaceTimeframeFile } = {}) {
  if (env === process.env) tryLoad(path.join(DEFAULT_PROJECT_ROOT, '.env'));
  tryLoad(path.join(root, '.env'));
  const marketDir = String(env.MARKET_DATA_ENV_DIR ?? '').trim();
  if (marketDir) tryLoad(path.join(path.resolve(marketDir), '.env'));
  const kiwoomDir = String(env.KIWOOM_ENV_DIR ?? '').trim();
  if (kiwoomDir) tryLoad(path.join(path.resolve(kiwoomDir), '.env'));
  normalizeKiwoomEnv(env);

  const studioBase = String(dslStudioUrl ?? env.DSL_STUDIO_URL ?? 'http://127.0.0.1:8010').replace(/\/+$/, '');
  const repo = repository ?? new MySqlDailyMarketDataRepository({ env });
  const workspaceTimeframeMiddleware = createWorkspaceTimeframePersistenceMiddleware(new WorkspaceTimeframeJsonStore(
    workspaceTimeframeFile ?? path.join(DEFAULT_PROJECT_ROOT, '.runtime', 'dsl-stack', 'chart-workspace-timeframe.json'),
  ));
  const addonMiddleware = createChartAddonPersistenceMiddleware(new ChartAddonJsonStore(path.join(root, '.runtime', 'chart-addons')));
  const marketMiddleware = createSafeMarketDataMiddleware(repo);
  let proxy;
  function getProxy() { if (!proxy) proxy = createIndexWysiwygProxy(env); return proxy; }
  const proxyMiddleware = createIndexWysiwygProxyMiddleware({
    call: request => getProxy().call(request),
    subscribeRealtime: subscribe => getProxy().subscribeRealtime(subscribe),
    snapshotGovernance: () => proxy?.snapshotGovernance?.() ?? {},
  });

  return http.createServer(async (request, response) => {
    const url = new URL(request.url || '/', 'http://127.0.0.1');
    if (url.pathname === '/__chart_health') {
      sendJson(response, 200, { app: 'dsl-chart-bridge', status: 'ok', chartRoot: root, dslStudioUrl: studioBase });
      return;
    }

    if (url.pathname === '/__dsl/catalog') {
      await proxyStudio(request, response, studioBase, '/api/features', 'GET');
      return;
    }
    if (url.pathname === '/__dsl/validate') {
      await proxyStudio(request, response, studioBase, '/api/validate', 'POST');
      return;
    }
    if (url.pathname === '/__dsl/evaluate') {
      await proxyStudio(request, response, studioBase, '/api/evaluate', 'POST');
      return;
    }

    if (url.pathname === '/') {
      try {
        await serveFile(response, path.join(DEFAULT_DSL_BROWSER_ROOT, 'index.html'));
      } catch (error) {
        sendJson(response, 500, { message: `DSL chart shell unavailable: ${String(error?.message ?? error)}` });
      }
      return;
    }

    if (url.pathname.startsWith('/__dsl/')) {
      try {
        const relative = url.pathname.slice('/__dsl/'.length);
        const target = safePath(DEFAULT_DSL_BROWSER_ROOT, relative);
        if (!target) throw new Error('invalid DSL extension path');
        const info = await stat(target);
        const file = info.isDirectory() ? path.join(target, 'index.html') : target;
        await serveFile(response, file);
      } catch {
        if (!response.headersSent) response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
        if (!response.writableEnded) response.end('Not found');
      }
      return;
    }

    try {
      if (!(await run(workspaceTimeframeMiddleware, request, response))) return;
      if (!(await run(addonMiddleware, request, response))) return;
      if (!(await run(marketMiddleware, request, response))) return;
      if (!(await run(proxyMiddleware, request, response))) return;
    } catch (error) {
      if (response.headersSent) {
        if (!response.writableEnded) response.end();
        return;
      }
      sendJson(response, 422, { message: error?.message ?? String(error) });
      return;
    }
    try {
      const target = safePath(root, url.pathname);
      if (!target) throw new Error('invalid path');
      const info = await stat(target);
      const file = info.isDirectory() ? path.join(target, 'index.html') : target;
      await serveFile(response, file);
    } catch {
      if (!response.headersSent) response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
      if (!response.writableEnded) response.end('Not found');
    }
  });
}

function arg(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const host = arg('--host') || process.env.HOST || '127.0.0.1';
  const port = Number(arg('--port') || process.env.PORT || '3032');
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error('[ERROR] Invalid port');
    process.exit(2);
  }
  createChartPlatformServer().listen(port, host, () => {
    console.log(`[PASS] DSL Chart Bridge http://${host}:${port}/`);
  });
}
