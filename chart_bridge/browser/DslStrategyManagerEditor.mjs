import { chartBarsToDslMarket } from './DslStrategyAddon.mjs';

const DSL_STRATEGY_ADDON_ID = 'strategy.dsl';

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function normalizeLibrary(value) {
  return Array.isArray(value) ? value.filter(item => item && typeof item === 'object').map(item => cloneJson(item)) : [];
}

async function jsonRequest(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload?.ok === false) {
    const detail = payload?.detail ?? payload;
    throw new Error(detail?.message ?? payload?.message ?? `HTTP ${response.status}`);
  }
  return payload;
}

async function loadCatalog() {
  const payload = await jsonRequest('/__dsl/catalog');
  return (payload.categories ?? []).flatMap(category =>
    (category.features ?? []).map(feature => ({ ...feature, category: feature.category ?? category.category }))
  );
}

async function validateSyntax(dslCode) {
  return jsonRequest('/__dsl/validate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ dsl_code: dslCode }),
  });
}

async function evaluateOnChart(dslCode, bars, settings = {}) {
  return jsonRequest('/__dsl/evaluate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      dsl_code: dslCode,
      settings,
      market: chartBarsToDslMarket(bars),
      bars_count: bars.length,
    }),
  });
}

function nextInstanceId(port, strategyId) {
  const base = `strategy.dsl.${String(strategyId).replace(/[^A-Za-z0-9_.-]/g, '_')}`;
  const addons = port.snapshotAddonState()?.addons ?? {};
  if (!(base in addons)) return base;
  for (let ordinal = 2; ordinal < 100000; ordinal += 1) {
    const candidate = `${base}.${ordinal}`;
    if (!(candidate in addons)) return candidate;
  }
  throw new Error('DSL strategy instance id를 할당할 수 없습니다.');
}

function validatedStrategy(base, result) {
  return {
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
}

export async function createDslStrategyManagerEditor({ instanceId, state, port, host, reportStatus }) {
  let library = normalizeLibrary(state?.library);
  let catalog = [];
  let selectedCatalogId;
  let selectedSavedId;
  let syntaxValidatedCode;

  host.style.display = 'grid';
  host.style.gridTemplateColumns = '260px minmax(0,1fr)';
  host.style.gap = '10px';
  host.style.maxHeight = 'none';
  host.style.height = '60vh';
  host.innerHTML = `
    <section style="min-width:0;display:grid;grid-template-rows:auto 1fr;border-right:1px solid #2d4357;padding-right:8px">
      <div style="display:flex;gap:5px;margin-bottom:7px">
        <button data-tab-catalog type="button" style="flex:1;padding:7px;background:#214a6b;color:#fff;border:1px solid #36506a;border-radius:4px">등록 DSL</button>
        <button data-tab-saved type="button" style="flex:1;padding:7px;background:#172635;color:#dbe7f2;border:1px solid #36506a;border-radius:4px">삽입 기록</button>
      </div>
      <div data-left-list style="overflow:auto;display:grid;align-content:start;gap:4px"></div>
    </section>
    <section style="min-width:0;display:grid;grid-template-rows:auto minmax(280px,1fr) auto;gap:8px">
      <input data-name placeholder="전략명" style="width:100%;background:#172635;color:#dbe7f2;border:1px solid #36506a;border-radius:4px;padding:7px"/>
      <textarea data-dsl placeholder="좌측의 등록 DSL을 선택하세요." spellcheck="false" style="width:100%;resize:none;background:#070b11;color:#dce8f7;border:1px solid #36506a;border-radius:4px;padding:10px;font:12px/1.5 Consolas,monospace"></textarea>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <button data-syntax type="button" style="padding:7px 10px;background:#314a63;color:#fff;border:1px solid #45617b;border-radius:4px">문법 검증</button>
        <button data-insert type="button" disabled style="padding:7px 10px;background:#214a6b;color:#fff;border:1px solid #36506a;border-radius:4px;opacity:.5">차트 삽입</button>
        <span data-status style="font-size:11px;color:#91a2b8"></span>
      </div>
    </section>`;

  const leftList = host.querySelector('[data-left-list]');
  const tabCatalog = host.querySelector('[data-tab-catalog]');
  const tabSaved = host.querySelector('[data-tab-saved]');
  const name = host.querySelector('[data-name]');
  const dsl = host.querySelector('[data-dsl]');
  const syntaxButton = host.querySelector('[data-syntax]');
  const insertButton = host.querySelector('[data-insert]');
  const status = host.querySelector('[data-status]');
  let leftMode = 'catalog';

  const invalidateSyntax = () => {
    syntaxValidatedCode = undefined;
    insertButton.disabled = true;
    insertButton.style.opacity = '.5';
  };
  name.addEventListener('input', invalidateSyntax);
  dsl.addEventListener('input', invalidateSyntax);

  const selectCatalog = feature => {
    selectedCatalogId = feature.feature_id ?? feature.id;
    selectedSavedId = undefined;
    name.value = feature.title ?? feature.feature_id ?? 'DSL Strategy';
    dsl.value = feature.dsl_code ?? '';
    invalidateSyntax();
    status.textContent = `${feature.category ?? ''} · ${selectedCatalogId}`;
    renderLeft();
  };

  const selectSaved = strategy => {
    selectedSavedId = strategy.id;
    selectedCatalogId = undefined;
    name.value = strategy.name ?? '';
    dsl.value = strategy.dsl_code ?? '';
    invalidateSyntax();
    status.textContent = strategy.validation ? `삽입 기록 · ${strategy.validation.trade_count ?? 0} trades` : '삽입 기록';
    renderLeft();
  };

  const buttonFor = (label, active, click, sublabel = '') => {
    const button = document.createElement('button');
    button.type = 'button';
    button.style.cssText = `text-align:left;background:${active ? '#214a6b' : '#172635'};color:#dbe7f2;border:1px solid #334b60;border-radius:4px;padding:7px`;
    button.innerHTML = `<div style="font-size:11px"></div><div style="font-size:9px;color:#89a0b5;margin-top:2px"></div>`;
    button.children[0].textContent = label;
    button.children[1].textContent = sublabel;
    button.onclick = click;
    return button;
  };

  const renderLeft = () => {
    tabCatalog.style.background = leftMode === 'catalog' ? '#214a6b' : '#172635';
    tabSaved.style.background = leftMode === 'saved' ? '#214a6b' : '#172635';
    if (leftMode === 'saved') {
      leftList.replaceChildren(...library.map(strategy => buttonFor(
        strategy.name,
        strategy.id === selectedSavedId,
        () => selectSaved(strategy),
        `${strategy.validation?.trade_count ?? 0} trades · ${Number(strategy.validation?.total_return_pct ?? 0).toFixed(2)}%`,
      )));
      return;
    }
    const nodes = [];
    let previousCategory;
    for (const feature of catalog) {
      const category = String(feature.category ?? 'DSL');
      if (category !== previousCategory) {
        const heading = document.createElement('div');
        heading.textContent = category;
        heading.style.cssText = 'font-size:10px;font-weight:700;color:#9eb0c1;margin:7px 2px 2px;text-transform:uppercase';
        nodes.push(heading);
        previousCategory = category;
      }
      const featureId = feature.feature_id ?? feature.id;
      nodes.push(buttonFor(feature.title ?? featureId, featureId === selectedCatalogId, () => selectCatalog(feature), featureId));
    }
    leftList.replaceChildren(...nodes);
  };

  tabCatalog.onclick = () => { leftMode = 'catalog'; renderLeft(); };
  tabSaved.onclick = () => { leftMode = 'saved'; renderLeft(); };

  syntaxButton.onclick = async () => {
    try {
      const code = String(dsl.value ?? '').trim();
      if (!code) throw new Error('DSL 코드를 선택하거나 입력하세요.');
      status.textContent = 'Parser / Semantic 검증 중...';
      const result = await validateSyntax(code);
      syntaxValidatedCode = code;
      insertButton.disabled = false;
      insertButton.style.opacity = '1';
      status.textContent = `문법 PASS · ${result.strategy} · ${result.timeframe}`;
      reportStatus?.(`DSL 문법 검증 PASS · ${result.strategy}`);
    } catch (error) {
      invalidateSyntax();
      status.textContent = `문법 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
    }
  };

  insertButton.onclick = async () => {
    try {
      const code = String(dsl.value ?? '').trim();
      if (!syntaxValidatedCode || syntaxValidatedCode !== code) throw new Error('현재 DSL을 먼저 문법 검증하세요.');
      const strategyName = String(name.value ?? '').trim();
      if (!strategyName) throw new Error('전략명은 필수입니다.');
      const bars = port.snapshotBars();
      if (!Array.isArray(bars) || bars.length < 2) throw new Error('현재 차트 봉 데이터가 부족합니다.');
      status.textContent = `Core 백테스트 중 · ${bars.length} bars...`;
      const base = {
        schemaVersion: 1,
        id: selectedSavedId || `dsl-strategy-${Date.now()}`,
        name: strategyName,
        dsl_code: code,
        settings: {},
        catalog_feature_id: selectedCatalogId || undefined,
      };
      const result = await evaluateOnChart(code, bars, base.settings);
      const validated = validatedStrategy(base, result);
      const existing = library.findIndex(item => item.id === validated.id);
      if (existing >= 0) library[existing] = validated; else library.push(validated);
      selectedSavedId = validated.id;

      port.writeAddonState(instanceId, {
        enabled: true,
        definitionId: 'strategy.dsl-manager',
        visible: true,
        state: { library: cloneJson(library) },
      });
      const strategyInstanceId = nextInstanceId(port, validated.id);
      port.writeAddonState(strategyInstanceId, {
        enabled: true,
        definitionId: DSL_STRATEGY_ADDON_ID,
        visible: true,
        state: { strategy: cloneJson(validated) },
      });
      await port.whenAddonsIdle();
      status.textContent = `차트 삽입 PASS · trades ${validated.validation.trade_count} · return ${validated.validation.total_return_pct.toFixed(2)}%`;
      reportStatus?.(`DSL 차트 삽입 PASS · ${validated.name}`);
      leftMode = 'saved';
      renderLeft();
    } catch (error) {
      status.textContent = `차트 삽입 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
    }
  };

  status.textContent = '등록 DSL 목록 로딩 중...';
  try {
    catalog = await loadCatalog();
    status.textContent = `등록 DSL ${catalog.length}개 · 항목을 선택하세요.`;
  } catch (error) {
    status.textContent = `DSL 목록 FAIL · ${String(error?.message ?? error)}`;
  }
  renderLeft();

  return {
    readState() { return { library: cloneJson(library) }; },
    dispose() { host.replaceChildren(); },
  };
}
