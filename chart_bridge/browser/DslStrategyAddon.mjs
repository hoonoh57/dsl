import { chartAddonCatalog } from '/src/addons/catalog.mjs';

export const DSL_STRATEGY_MANAGER_ADDON_ID = 'strategy.dsl-manager';
export const DSL_STRATEGY_ADDON_ID = 'strategy.dsl';
const CATALOG_FLAG = 'dslManagedStrategyCatalogEntry';

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function normalizeStrategy(value = {}) {
  const strategy = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const name = String(strategy.name ?? '').trim();
  const dslCode = String(strategy.dsl_code ?? '').trim();
  if (!name) throw new Error('전략명은 필수입니다.');
  if (!dslCode) throw new Error('DSL 코드는 필수입니다.');
  return {
    schemaVersion: 1,
    id: String(strategy.id ?? '').trim() || `dsl-strategy-${Date.now()}`,
    name,
    dsl_code: dslCode,
    settings: strategy.settings && typeof strategy.settings === 'object' && !Array.isArray(strategy.settings) ? cloneJson(strategy.settings) : {},
    validatedAt: strategy.validatedAt ? String(strategy.validatedAt) : undefined,
    validation: strategy.validation ? cloneJson(strategy.validation) : undefined,
  };
}

function normalizedLibrary(value) {
  return Array.isArray(value) ? value.map(item => normalizeStrategy(item)) : [];
}

export function syncDslStrategyCatalog(value) {
  const library = normalizedLibrary(value);
  for (let index = chartAddonCatalog.length - 1; index >= 0; index -= 1) {
    if (chartAddonCatalog[index]?.[CATALOG_FLAG] === true) chartAddonCatalog.splice(index, 1);
  }
  for (const strategy of library.filter(item => item.validation && item.validatedAt)) {
    chartAddonCatalog.push({
      id: DSL_STRATEGY_ADDON_ID,
      label: strategy.name,
      category: 'strategy',
      defaultState: { strategy: cloneJson(strategy) },
      parameters: [],
      [CATALOG_FLAG]: true,
    });
  }
  return library;
}

function timeText(value, index) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' && Number.isFinite(value)) {
    const date = new Date(value * 1000);
    const yyyy = date.getUTCFullYear();
    const mm = String(date.getUTCMonth() + 1).padStart(2, '0');
    const dd = String(date.getUTCDate()).padStart(2, '0');
    const hh = String(date.getUTCHours()).padStart(2, '0');
    const mi = String(date.getUTCMinutes()).padStart(2, '0');
    const ss = String(date.getUTCSeconds()).padStart(2, '0');
    return `${yyyy}${mm}${dd}${hh}${mi}${ss}`;
  }
  if (value && typeof value === 'object' && Number.isInteger(value.year) && Number.isInteger(value.month) && Number.isInteger(value.day)) {
    return `${String(value.year).padStart(4, '0')}-${String(value.month).padStart(2, '0')}-${String(value.day).padStart(2, '0')}`;
  }
  return String(index).padStart(12, '0');
}

export function chartBarsToDslMarket(bars = []) {
  const clean = Array.isArray(bars) ? bars.filter(bar => ['open', 'high', 'low', 'close'].every(key => Number.isFinite(Number(bar?.[key])))) : [];
  return {
    time: clean.map((bar, index) => timeText(bar.time, index)),
    open: clean.map(bar => Number(bar.open)),
    high: clean.map(bar => Number(bar.high)),
    low: clean.map(bar => Number(bar.low)),
    close: clean.map(bar => Number(bar.close)),
    volume: clean.map(bar => Number.isFinite(Number(bar.volume)) ? Number(bar.volume) : 0),
    _meta: { source: 'condition1516_chart_loaded_bars', provenance: 'DSL_CHART_BRIDGE' },
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

class DslStrategyAddon {
  #context;
  #strategy;
  #markers;
  #indicatorSeries = [];
  #visible = true;
  #sequence = 0;
  #timer;

  constructor(context) {
    this.#context = context;
    this.#strategy = normalizeStrategy(context.state.readNode()?.state?.strategy ?? {});
    if (typeof context.surface?.createMarkers !== 'function') throw new Error('DSL strategy requires generic candle marker surface.');
    this.#markers = context.surface.createMarkers([]);
  }

  onStateChanged(node) {
    this.#strategy = normalizeStrategy(node?.state?.strategy ?? {});
    this.#schedule(this.#context.getBars(), 0);
  }

  onBarsReset(bars) { this.#schedule(bars, 0); }
  onBarChanged() { this.#schedule(this.#context.getBars(), 180); }

  setVisualsVisible(visible) {
    this.#visible = visible === true;
    this.#markers?.setVisible(this.#visible);
    for (const series of this.#indicatorSeries) series.setVisible(this.#visible);
  }

  dispose() {
    clearTimeout(this.#timer);
    this.#sequence += 1;
    this.#markers?.dispose();
    this.#markers = undefined;
    this.#clearIndicators();
  }

  #schedule(bars, delay) {
    clearTimeout(this.#timer);
    const snapshot = Array.isArray(bars) ? bars.map(bar => ({ ...bar })) : [];
    this.#timer = setTimeout(() => this.#reset(snapshot), delay);
  }

  async #reset(bars) {
    const sequence = ++this.#sequence;
    if (bars.length < 2) {
      this.#markers?.setMarkers([]);
      this.#clearIndicators();
      return;
    }
    try {
      const result = await evaluateDsl(this.#strategy, bars);
      if (sequence !== this.#sequence) return;
      this.#markers?.setMarkers(Array.isArray(result.markers) ? result.markers : []);
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
      this.#markers?.setMarkers([]);
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

class DslStrategyManagerAddon {
  #context;
  #action;
  #dialog;

  constructor(context) {
    this.#context = context;
    syncDslStrategyCatalog(context.state.readNode()?.state?.library ?? []);
    const chartState = context.capabilities?.chartState;
    if (!chartState || typeof chartState.snapshot !== 'function' || typeof chartState.writeAddon !== 'function') {
      throw new Error('DSL Strategy Manager requires chartState capability.');
    }
    if (typeof document !== 'undefined') {
      const action = document.createElement('button');
      action.type = 'button';
      action.hidden = true;
      action.dataset.chartAddonContextAction = 'DSL Strategy Manager…';
      action.addEventListener('click', () => this.#open());
      document.body.append(action);
      this.#action = action;
    }
  }

  onStateChanged(node) { syncDslStrategyCatalog(node?.state?.library ?? []); }
  setVisualsVisible() {}

  dispose() {
    this.#action?.remove();
    this.#dialog?.remove();
    this.#action = undefined;
    this.#dialog = undefined;
  }

  #library() {
    return normalizedLibrary(this.#context.state.readNode()?.state?.library ?? []);
  }

  #writeLibrary(library) {
    const chartState = this.#context.capabilities.chartState;
    chartState.writeAddon(this.#context.id, {
      enabled: true,
      visible: true,
      state: { library: cloneJson(library) },
    });
  }

  #open() {
    this.#dialog?.remove();
    const dialog = document.createElement('dialog');
    dialog.style.cssText = 'width:min(920px,calc(100vw - 40px));max-height:88vh;background:#111d28;color:#dbe7f2;border:1px solid #36506a;border-radius:8px;padding:14px';
    dialog.innerHTML = `
      <h3 style="margin:0 0 10px">DSL Strategy Manager</h3>
      <div style="display:grid;grid-template-columns:220px 1fr;gap:12px;min-height:560px">
        <div><button data-new type="button">+ 새 DSL 전략</button><div data-list style="margin-top:8px;display:grid;gap:5px"></div></div>
        <div style="display:grid;grid-template-rows:auto 1fr auto;gap:8px">
          <input data-name placeholder="전략명" style="background:#172635;color:#dbe7f2;border:1px solid #36506a;padding:7px"/>
          <textarea data-dsl placeholder="strategy ..." style="min-height:430px;background:#070b11;color:#dce8f7;border:1px solid #36506a;padding:10px;font:12px/1.5 Consolas,monospace"></textarea>
          <div><button data-validate type="button">현재 차트로 검증/저장</button> <button data-delete type="button">삭제</button> <button data-close type="button">닫기</button><span data-status style="margin-left:10px;font-size:11px;color:#91a2b8"></span></div>
        </div>
      </div>`;
    document.body.append(dialog);
    this.#dialog = dialog;
    const list = dialog.querySelector('[data-list]');
    const name = dialog.querySelector('[data-name]');
    const dsl = dialog.querySelector('[data-dsl]');
    const status = dialog.querySelector('[data-status]');
    let selectedId;

    const render = () => {
      const library = this.#library();
      list.replaceChildren(...library.map(strategy => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = `${strategy.validation ? '✓ ' : ''}${strategy.name}`;
        button.style.cssText = 'text-align:left;background:#172635;color:#dbe7f2;border:1px solid #334b60;border-radius:4px;padding:7px';
        button.onclick = () => { selectedId = strategy.id; name.value = strategy.name; dsl.value = strategy.dsl_code; status.textContent = strategy.validation ? `검증됨 · ${strategy.validation.trade_count ?? 0} trades` : '미검증'; };
        return button;
      }));
    };

    dialog.querySelector('[data-new]').onclick = () => { selectedId = undefined; name.value = ''; dsl.value = ''; status.textContent = '새 전략'; };
    dialog.querySelector('[data-close]').onclick = () => dialog.close();
    dialog.querySelector('[data-delete]').onclick = () => {
      if (!selectedId) return;
      this.#writeLibrary(this.#library().filter(item => item.id !== selectedId));
      selectedId = undefined; name.value = ''; dsl.value = ''; status.textContent = '삭제됨'; render();
    };
    dialog.querySelector('[data-validate]').onclick = async () => {
      try {
        status.textContent = 'DSL Core 검증 중...';
        const base = normalizeStrategy({ id: selectedId, name: name.value, dsl_code: dsl.value });
        const bars = this.#context.getBars();
        const result = await evaluateDsl(base, bars);
        const validated = {
          ...base,
          validatedAt: new Date().toISOString(),
          validation: {
            engine: result?.evaluation?.engine ?? 'core.backtest.BacktestEngine',
            data_claim: result?.evaluation?.data_claim ?? 'CALLER_SUPPLIED_MARKET',
            trade_count: Number(result?.metrics_numeric?.trade_count ?? 0),
            closed_trade_count: Number(result?.metrics_numeric?.closed_trade_count ?? 0),
            total_return_pct: Number(result?.metrics_numeric?.total_return_pct ?? 0),
          },
        };
        const library = this.#library();
        const index = library.findIndex(item => item.id === validated.id);
        if (index >= 0) library[index] = validated; else library.push(validated);
        this.#writeLibrary(library);
        selectedId = validated.id;
        status.textContent = `PASS · trades ${validated.validation.trade_count} · return ${validated.validation.total_return_pct.toFixed(2)}%`;
        render();
      } catch (error) {
        status.textContent = `FAIL · ${String(error?.message ?? error)}`;
      }
    };
    render();
    dialog.showModal();
  }
}

export const dslStrategyAddonDefinition = {
  id: DSL_STRATEGY_ADDON_ID,
  create(context) { return new DslStrategyAddon(context); },
};

export const dslStrategyManagerAddonDefinition = {
  id: DSL_STRATEGY_MANAGER_ADDON_ID,
  create(context) { return new DslStrategyManagerAddon(context); },
};
