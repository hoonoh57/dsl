import { chartBarsToDslMarket } from './DslChartMarketAdapter.mjs';

const DSL_STRATEGY_ADDON_ID = 'strategy.dsl';

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function normalizeStrategy(value = {}) {
  const strategy = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const name = String(strategy.name ?? '').trim();
  const dslCode = String(strategy.dsl_code ?? '').trim();
  if (!name) throw new Error('DSL strategy name is required.');
  if (!dslCode) throw new Error('DSL strategy code is required.');
  return {
    schemaVersion: 1,
    id: String(strategy.id ?? '').trim() || 'dsl-strategy',
    name,
    dsl_code: dslCode,
    settings: strategy.settings && typeof strategy.settings === 'object' && !Array.isArray(strategy.settings)
      ? cloneJson(strategy.settings)
      : {},
  };
}

async function evaluateDsl(strategy, bars) {
  const response = await fetch('/__dsl/evaluate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      dsl_code: strategy.dsl_code,
      settings: strategy.settings ?? {},
      market: chartBarsToDslMarket(bars),
      bars_count: bars.length,
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.detail?.message ?? payload?.message ?? `DSL Core HTTP ${response.status}`);
  return payload;
}

class DslStrategyRendererAddon {
  #context;
  #strategy;
  #markerPlugin;
  #markers = [];
  #indicatorSeries = [];
  #visible = true;
  #sequence = 0;
  #timer;

  constructor(context) {
    this.#context = context;
    this.#strategy = normalizeStrategy(context.state.readNode()?.state?.strategy ?? {});
    if (typeof context.surface?.setMarkers !== 'function') {
      throw new Error('DSL strategy requires chart surface setMarkers().');
    }
    this.#markerPlugin = context.surface.setMarkers([]);
    if (!this.#markerPlugin || typeof this.#markerPlugin.setMarkers !== 'function') {
      throw new Error('Chart surface setMarkers() returned invalid marker plugin.');
    }
  }

  onStateChanged(node) {
    this.#strategy = normalizeStrategy(node?.state?.strategy ?? {});
    this.#schedule(this.#context.getBars(), 0);
  }

  onBarsReset(bars) { this.#schedule(bars, 0); }
  onBarChanged() { this.#schedule(this.#context.getBars(), 180); }

  setVisualsVisible(visible) {
    this.#visible = visible === true;
    this.#markerPlugin?.setMarkers(this.#visible ? this.#markers : []);
    for (const series of this.#indicatorSeries) series.setVisible(this.#visible);
  }

  dispose() {
    clearTimeout(this.#timer);
    this.#sequence += 1;
    try { this.#markerPlugin?.setMarkers([]); } catch {}
    try { this.#markerPlugin?.detach?.(); } catch {}
    this.#markerPlugin = undefined;
    this.#markers = [];
    this.#clearIndicators();
  }

  #schedule(bars, delay) {
    clearTimeout(this.#timer);
    const snapshot = Array.isArray(bars) ? bars.map(bar => ({ ...bar })) : [];
    this.#timer = setTimeout(() => void this.#reset(snapshot), delay);
  }

  async #reset(bars) {
    const sequence = ++this.#sequence;
    if (bars.length < 2) {
      this.#markers = [];
      this.#markerPlugin?.setMarkers([]);
      this.#clearIndicators();
      return;
    }
    try {
      const result = await evaluateDsl(this.#strategy, bars);
      if (sequence !== this.#sequence) return;
      this.#markers = Array.isArray(result.markers) ? result.markers.map(item => ({ ...item })) : [];
      this.#markerPlugin?.setMarkers(this.#visible ? this.#markers : []);
      this.#clearIndicators();
      for (const indicator of Array.isArray(result.indicators) ? result.indicators : []) {
        if (indicator?.overlay !== true || !Array.isArray(indicator.data)) continue;
        const series = this.#context.surface.createLineSeries({
          pane: 0,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          inspectionLabel: `${this.#strategy.name} · ${indicator.name}`,
        });
        series.setData(indicator.data);
        series.setVisible(this.#visible);
        this.#indicatorSeries.push(series);
      }
    } catch (error) {
      if (sequence !== this.#sequence) return;
      this.#markers = [];
      this.#markerPlugin?.setMarkers([]);
      this.#clearIndicators();
      this.#context.reportError?.(`DSL strategy evaluation failed: ${String(error?.message ?? error)}`);
    }
  }

  #clearIndicators() {
    for (const series of this.#indicatorSeries) {
      try { series.dispose(); } catch {}
    }
    this.#indicatorSeries = [];
  }
}

export const dslStrategyAddonDefinition = {
  id: DSL_STRATEGY_ADDON_ID,
  create(context) { return new DslStrategyRendererAddon(context); },
};
