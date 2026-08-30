import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnvFile } from 'node:process';

import { ChartAddonJsonStore } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/server/chart/ChartAddonJsonStore.mjs';
import { MySqlDailyMarketDataRepository } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/server/market-data/MySqlDailyMarketDataRepository.mjs';
import { createChartAddonPersistenceMiddleware } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/shell/index-wysiwyg/ChartAddonPersistenceHttpHost.mjs';
import { createIndexWysiwygProxy, createIndexWysiwygProxyMiddleware } from '../vendor/kiwoom-condition/condition1516/chart-platform/src/shell/index-wysiwyg/IndexWysiwygHttpHost.mjs';

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_CHART_ROOT = path.resolve(moduleDir, '../vendor/kiwoom-condition/condition1516/chart-platform');

function tryLoad(file) {
  try { loadEnvFile(file); return true; }
  catch (error) { if (error?.code === 'ENOENT') return false; throw error; }
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

export function createChartPlatformServer({ root = DEFAULT_CHART_ROOT, env = process.env, repository } = {}) {
  tryLoad(path.join(root, '.env'));
  const marketDir = String(env.MARKET_DATA_ENV_DIR ?? '').trim();
  if (marketDir) tryLoad(path.join(path.resolve(marketDir), '.env'));
  const kiwoomDir = String(env.KIWOOM_ENV_DIR ?? '').trim();
  if (kiwoomDir) tryLoad(path.join(path.resolve(kiwoomDir), '.env'));

  const repo = repository ?? new MySqlDailyMarketDataRepository({ env });
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
      sendJson(response, 200, { app: 'dsl-chart-bridge', status: 'ok', chartRoot: root });
      return;
    }
    try {
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
      const body = await readFile(file);
      response.writeHead(200, {
        'content-type': mime.get(path.extname(file).toLowerCase()) || 'application/octet-stream',
        'cache-control': 'no-store',
      });
      response.end(body);
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
