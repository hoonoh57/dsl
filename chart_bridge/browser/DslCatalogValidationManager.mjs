import { chartBarsToDslMarket } from './DslChartMarketAdapter.mjs';
import { assertDslChartTimeframeCompatible } from './DslChartTimeframeGuard.mjs';

export const DSL_VALIDATION_MANAGER_ID = 'strategy.dsl-validation-manager';
export const DSL_STRATEGY_ADDON_ID = 'strategy.dsl';

const managerPorts = new Map();

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function flattenCatalog(payload) {
  return (payload?.categories ?? []).flatMap(group =>
    (group?.features ?? []).map(item => ({ ...item, category: group.category })),
  );
}

function strategyOf(feature, timeframe) {
  return {
    schemaVersion: 1,
    id: `catalog-${String(feature.feature_id ?? feature.id ?? '').replace(/[^a-zA-Z0-9_.-]/g, '-')}`,
    name: String(feature.feature_id ?? feature.id ?? feature.title ?? 'DSL Strategy'),
    dsl_code: String(feature.dsl_code ?? ''),
    settings: cloneJson(feature.settings ?? {}),
    ...(timeframe ? { timeframe: String(timeframe) } : {}),
  };
}

function uniqueInstanceId(chartState, base) {
  const snapshot = chartState.snapshot();
  if (!snapshot?.addons?.[base]) return base;
  for (let index = 2; index < Number.MAX_SAFE_INTEGER; index += 1) {
    const candidate = `${base}.${index}`;
    if (!snapshot.addons[candidate]) return candidate;
  }
  throw new Error('DSL strategy instance id allocation failed.');
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.detail?.message ?? payload?.message ?? `HTTP ${response.status}`);
  return payload;
}

async function validateDsl(dslCode) {
  return requestJson('/__dsl/validate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ dsl_code: dslCode }),
  });
}

async function evaluateDsl(strategy, bars) {
  return requestJson('/__dsl/evaluate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      dsl_code: strategy.dsl_code,
      settings: strategy.settings ?? {},
      market: chartBarsToDslMarket(bars),
      bars_count: bars.length,
    }),
  });
}

class DslCatalogValidationManagerAddon {
  #context;
  #action;

  constructor(context) {
    this.#context = context;
    const chartState = context.capabilities?.chartState;
    if (!chartState || typeof chartState.snapshot !== 'function' || typeof chartState.writeAddon !== 'function') {
      throw new Error('DSL catalog validation manager requires chartState capability.');
    }
    managerPorts.set(context.id, {
      getBars: () => context.getBars().map(bar => ({ ...bar })),
      getWorkspaceContext: () => context.getWorkspaceContext?.() ?? {},
      chartState,
    });
    if (typeof document !== 'undefined') {
      const action = document.createElement('button');
      action.type = 'button';
      action.hidden = true;
      action.dataset.chartAddonContextAction = '등록 DSL 차트 검증…';
      action.addEventListener('click', () => {
        const row = [...document.querySelectorAll('[data-definition-id]')]
          .find(node => node.dataset.definitionId === DSL_VALIDATION_MANAGER_ID);
        row?.click?.();
      });
      document.body.append(action);
      this.#action = action;
    }
  }

  onStateChanged() {}
  setVisualsVisible() {}

  dispose() {
    managerPorts.delete(this.#context.id);
    this.#action?.remove();
    this.#action = undefined;
  }
}

export async function createDslCatalogValidationEditor({ instanceId, host, reportStatus }) {
  const manager = managerPorts.get(instanceId);
  if (!manager) throw new Error('DSL catalog validation runtime is not ready.');

  const dialog = host.closest('dialog');
  const outerSave = dialog?.querySelector('#addon-properties-save');
  const outerCancel = dialog?.querySelector('#addon-properties-cancel');
  const originalSaveHidden = outerSave?.hidden;
  const originalCancelText = outerCancel?.textContent;
  if (outerSave) outerSave.hidden = true;
  if (outerCancel) outerCancel.textContent = '닫기';

  host.style.display = 'grid';
  host.style.gridTemplateColumns = '300px minmax(0,1fr)';
  host.style.gap = '10px';
  host.style.maxHeight = 'none';
  host.style.height = '64vh';
  host.innerHTML = `
    <section style="min-width:0;display:grid;grid-template-rows:auto 1fr;gap:8px;border-right:1px solid #2d4357;padding-right:8px">
      <div>
        <strong>등록 DSL</strong>
        <div data-count style="font-size:11px;color:#91a2b8;margin-top:3px">로딩 중...</div>
      </div>
      <div data-list style="overflow:auto;display:grid;align-content:start;gap:5px"></div>
    </section>
    <section style="min-width:0;display:grid;grid-template-rows:auto minmax(300px,1fr) auto;gap:8px">
      <div><input data-name readonly placeholder="DSL을 선택하세요" style="width:100%;background:#172635;color:#dbe7f2;border:1px solid #36506a;border-radius:4px;padding:7px"/></div>
      <textarea data-dsl readonly spellcheck="false" placeholder="좌측 등록 DSL을 선택하세요." style="width:100%;resize:none;background:#070b11;color:#dce8f7;border:1px solid #36506a;border-radius:4px;padding:10px;font:12px/1.5 Consolas,monospace"></textarea>
      <div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap">
        <button data-validate type="button" disabled style="padding:7px 10px;background:#214a6b;color:#fff;border:1px solid #36506a;border-radius:4px">문법 검증</button>
        <button data-insert type="button" disabled style="padding:7px 10px;background:#286541;color:#fff;border:1px solid #3f7d58;border-radius:4px">차트 삽입</button>
        <span data-status style="font-size:11px;color:#91a2b8">DSL을 선택하세요.</span>
      </div>
    </section>`;

  const list = host.querySelector('[data-list]');
  const count = host.querySelector('[data-count]');
  const name = host.querySelector('[data-name]');
  const dsl = host.querySelector('[data-dsl]');
  const validateButton = host.querySelector('[data-validate]');
  const insertButton = host.querySelector('[data-insert]');
  const status = host.querySelector('[data-status]');
  let selected;
  let validatedCode;
  let validatedTimeframe;

  const setSelected = feature => {
    selected = feature;
    const strategy = strategyOf(feature);
    name.value = strategy.name;
    dsl.value = strategy.dsl_code;
    validatedCode = undefined;
    validatedTimeframe = undefined;
    validateButton.disabled = false;
    insertButton.disabled = true;
    status.textContent = '선택됨 · 문법 검증을 실행하세요.';
    for (const button of list.querySelectorAll('[data-feature-id]')) {
      button.style.background = button.dataset.featureId === String(feature.feature_id) ? '#214a6b' : '#172635';
    }
  };

  try {
    const catalog = await requestJson('/__dsl/catalog');
    const features = flattenCatalog(catalog);
    count.textContent = `${features.length}개 · Live Studio SSOT`;
    let lastCategory;
    for (const feature of features) {
      if (feature.category !== lastCategory) {
        const heading = document.createElement('div');
        heading.textContent = String(feature.category ?? '').toUpperCase();
        heading.style.cssText = 'margin:8px 0 1px;font-size:10px;font-weight:700;color:#aebfce';
        list.append(heading);
        lastCategory = feature.category;
      }
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.featureId = String(feature.feature_id ?? '');
      button.style.cssText = 'text-align:left;background:#172635;color:#dbe7f2;border:1px solid #334b60;border-radius:4px;padding:7px';
      button.innerHTML = `<div></div><small style="color:#91a2b8"></small>`;
      button.children[0].textContent = feature.title || feature.feature_id;
      button.children[1].textContent = feature.feature_id;
      button.onclick = () => setSelected(feature);
      list.append(button);
    }
  } catch (error) {
    count.textContent = `ERROR · ${String(error?.message ?? error)}`;
    reportStatus?.(count.textContent);
  }

  validateButton.onclick = async () => {
    if (!selected) return;
    insertButton.disabled = true;
    status.textContent = 'Parser + Semantic 검증 중...';
    try {
      const result = await validateDsl(dsl.value);
      if (!result?.ok) throw new Error(result?.message ?? 'DSL validation failed.');
      validatedCode = dsl.value;
      validatedTimeframe = String(result.timeframe ?? '').trim();
      assertDslChartTimeframeCompatible(validatedTimeframe, manager.getWorkspaceContext());
      insertButton.disabled = false;
      status.textContent = `문법 PASS · ${result.strategy} · ${validatedTimeframe} · 현재 차트 호환`;
      reportStatus?.(`DSL 문법 PASS · ${selected.feature_id} · ${validatedTimeframe}`);
    } catch (error) {
      validatedCode = undefined;
      validatedTimeframe = undefined;
      status.textContent = `검증 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
    }
  };

  insertButton.onclick = async () => {
    if (!selected || validatedCode !== dsl.value || !validatedTimeframe) return;
    insertButton.disabled = true;
    status.textContent = '현재 차트 실데이터로 Core 실행 중...';
    try {
      assertDslChartTimeframeCompatible(validatedTimeframe, manager.getWorkspaceContext());
      const strategy = strategyOf(selected, validatedTimeframe);
      const bars = manager.getBars();
      const result = await evaluateDsl(strategy, bars);
      const validated = {
        ...strategy,
        validatedAt: new Date().toISOString(),
        validation: {
          engine: result?.evaluation?.engine ?? 'core.backtest.BacktestEngine',
          data_claim: result?.evaluation?.data_claim ?? 'CALLER_SUPPLIED_MARKET',
          trade_count: Number(result?.metrics_numeric?.trade_count ?? 0),
          closed_trade_count: Number(result?.metrics_numeric?.closed_trade_count ?? 0),
          total_return_pct: Number(result?.metrics_numeric?.total_return_pct ?? 0),
        },
      };
      const strategyInstanceId = uniqueInstanceId(manager.chartState, `strategy.dsl.${String(selected.feature_id).replace(/[^a-zA-Z0-9_.-]/g, '-')}`);
      manager.chartState.writeAddon(strategyInstanceId, {
        enabled: true,
        definitionId: DSL_STRATEGY_ADDON_ID,
        visible: true,
        state: { strategy: cloneJson(validated) },
      });
      status.textContent = `차트 삽입 PASS · trades ${validated.validation.trade_count} · return ${validated.validation.total_return_pct.toFixed(2)}%`;
      reportStatus?.(`DSL 차트 삽입 PASS · ${selected.feature_id}`);
    } catch (error) {
      status.textContent = `차트 삽입 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
      insertButton.disabled = false;
    }
  };

  return {
    readState() { return {}; },
    dispose() {
      if (outerSave) outerSave.hidden = originalSaveHidden === true;
      if (outerCancel && originalCancelText !== undefined) outerCancel.textContent = originalCancelText;
      host.replaceChildren();
    },
  };
}

export const dslCatalogValidationManagerAddonDefinition = {
  id: DSL_VALIDATION_MANAGER_ID,
  create(context) { return new DslCatalogValidationManagerAddon(context); },
};
