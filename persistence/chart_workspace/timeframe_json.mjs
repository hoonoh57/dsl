import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

export const WORKSPACE_TIMEFRAME_SCHEMA_VERSION = 1;

const BASE_PERIODS = new Set(['month', 'week', 'day']);
const MINUTE_INTERVALS = new Set(['1', '3', '5', '10', '15', '30', '60', '240']);
const TICK_INTERVALS = new Set(['1', '5', '10', '30', '60', '120', '240', '360', '480', '540', '720']);

export function normalizeWorkspaceTimeframe(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('workspace timeframe must be an object.');
  const period = String(value.period ?? '').trim();
  if (BASE_PERIODS.has(period)) return { period };
  const interval = String(value.interval ?? '').trim();
  if (period === 'minute' && MINUTE_INTERVALS.has(interval)) return { period, interval };
  if (period === 'tick' && TICK_INTERVALS.has(interval)) return { period, interval };
  throw new Error('workspace timeframe is unsupported.');
}

async function readOptional(file) {
  try { return await readFile(file, 'utf8'); }
  catch (error) { if (error?.code === 'ENOENT') return undefined; throw error; }
}

async function atomicWrite(file, text) {
  await mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(temporary, text, 'utf8');
  await rename(temporary, file);
}

export class WorkspaceTimeframeJsonStore {
  #file;

  constructor(file) {
    const normalized = String(file ?? '').trim();
    if (!normalized) throw new Error('WorkspaceTimeframeJsonStore file is required.');
    this.#file = path.resolve(normalized);
  }

  get file() { return this.#file; }

  async load() {
    const text = await readOptional(this.#file);
    if (text === undefined) return undefined;
    let value;
    try { value = JSON.parse(text); }
    catch { throw new Error('workspace timeframe JSON is invalid.'); }
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('workspace timeframe JSON must contain an object.');
    if (Number(value.schemaVersion) !== WORKSPACE_TIMEFRAME_SCHEMA_VERSION) throw new Error('workspace timeframe schemaVersion is unsupported.');
    return normalizeWorkspaceTimeframe(value.timeframe);
  }

  async save(value) {
    const timeframe = normalizeWorkspaceTimeframe(value);
    const record = { schemaVersion: WORKSPACE_TIMEFRAME_SCHEMA_VERSION, timeframe };
    await atomicWrite(this.#file, `${JSON.stringify(record, null, 2)}\n`);
    return timeframe;
  }
}
