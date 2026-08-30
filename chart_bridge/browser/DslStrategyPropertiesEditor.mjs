import { chartBarsToDslMarket } from './DslChartMarketAdapter.mjs';

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload?.ok === false) {
    const detail = payload?.detail ?? payload;
    throw new Error(detail?.message ?? payload?.message ?? `HTTP ${response.status}`);
  }
  return payload;
}

async function loadCatalog() {
  const payload = await requestJson('/__dsl/catalog');
  return (payload.categories ?? []).flatMap(group =>
    (group.features ?? []).map(feature => ({ ...feature, category: feature.category ?? group.category }))
  );
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

function strategyFromFeature(feature) {
  return {
    schemaVersion: 1,
    id: `catalog-${String(feature.feature_id ?? feature.id ?? '').replace(/[^A-Za-z0-9_.-]/g, '-')}`,
    name: String(feature.feature_id ?? feature.id ?? feature.title ?? 'DSL Strategy'),
    dsl_code: String(feature.dsl_code ?? ''),
    settings: cloneJson(feature.settings ?? {}),
    catalog_feature_id: feature.feature_id ?? feature.id,
  };
}

export async function createDslStrategyPropertiesEditor({ instanceId, state, port, host, reportStatus }) {
  let strategy = cloneJson(state?.strategy ?? {});
  let validatedCode;
  let selectedFeatureId = strategy.catalog_feature_id;

  const dialog = host.closest('dialog');
  const outerSave = dialog?.querySelector('#addon-properties-save');
  const outerCancel = dialog?.querySelector('#addon-properties-cancel');
  const originalSaveHidden = outerSave?.hidden;
  const originalCancelText = outerCancel?.textContent;
  if (outerSave) outerSave.hidden = true;
  if (outerCancel) outerCancel.textContent = '닫기';

  host.style.display = 'grid';
  host.style.gridTemplateColumns = '260px minmax(0,1fr)';
  host.style.gap = '10px';
  host.style.maxHeight = 'none';
  host.style.height = '62vh';
  host.innerHTML = `
    <section style="min-width:0;display:grid;grid-template-rows:auto 1fr;gap:7px;border-right:1px solid #2d4357;padding-right:8px">
      <div><strong>등록 DSL로 교체</strong><div data-count style="font-size:10px;color:#91a2b8;margin-top:2px">로딩 중...</div></div>
      <div data-list style="overflow:auto;display:grid;align-content:start;gap:4px"></div>
    </section>
    <section style="min-width:0;display:grid;grid-template-rows:auto minmax(300px,1fr) auto;gap:8px">
      <input data-name readonly style="width:100%;background:#172635;color:#dbe7f2;border:1px solid #36506a;border-radius:4px;padding:7px"/>
      <textarea data-dsl readonly spellcheck="false" style="width:100%;resize:none;background:#070b11;color:#dce8f7;border:1px solid #36506a;border-radius:4px;padding:10px;font:12px/1.5 Consolas,monospace"></textarea>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <button data-validate type="button" style="padding:7px 10px;background:#314a63;color:#fff;border:1px solid #45617b;border-radius:4px">문법 검증</button>
        <button data-apply type="button" disabled style="padding:7px 10px;background:#286541;color:#fff;border:1px solid #3f7d58;border-radius:4px">현재 차트에 적용</button>
        <button data-delete type="button" style="padding:7px 10px;background:#5a2c34;color:#fff;border:1px solid #7a3d47;border-radius:4px">삭제</button>
        <span data-status style="font-size:11px;color:#91a2b8"></span>
      </div>
    </section>`;

  const list = host.querySelector('[data-list]');
  const count = host.querySelector('[data-count]');
  const name = host.querySelector('[data-name]');
  const dsl = host.querySelector('[data-dsl]');
  const validateButton = host.querySelector('[data-validate]');
  const applyButton = host.querySelector('[data-apply]');
  const deleteButton = host.querySelector('[data-delete]');
  const status = host.querySelector('[data-status]');

  const showStrategy = next => {
    strategy = cloneJson(next);
    name.value = strategy.name ?? '';
    dsl.value = strategy.dsl_code ?? '';
    selectedFeatureId = strategy.catalog_feature_id;
    validatedCode = undefined;
    applyButton.disabled = true;
    status.textContent = '문법 검증 후 적용할 수 있습니다.';
    for (const button of list.querySelectorAll('[data-feature-id]')) {
      button.style.background = button.dataset.featureId === String(selectedFeatureId ?? '') ? '#214a6b' : '#172635';
    }
  };

  showStrategy(strategy);

  try {
    const catalog = await loadCatalog();
    count.textContent = `${catalog.length}개 · Live Studio SSOT`;
    let previousCategory;
    for (const feature of catalog) {
      const category = String(feature.category ?? 'DSL');
      if (category !== previousCategory) {
        const heading = document.createElement('div');
        heading.textContent = category.toUpperCase();
        heading.style.cssText = 'font-size:10px;font-weight:700;color:#9eb0c1;margin:7px 2px 2px';
        list.append(heading);
        previousCategory = category;
      }
      const featureId = feature.feature_id ?? feature.id;
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.featureId = String(featureId ?? '');
      button.style.cssText = `text-align:left;background:${String(featureId) === String(selectedFeatureId ?? '') ? '#214a6b' : '#172635'};color:#dbe7f2;border:1px solid #334b60;border-radius:4px;padding:7px`;
      button.innerHTML = '<div></div><small style="color:#91a2b8"></small>';
      button.children[0].textContent = feature.title ?? featureId;
      button.children[1].textContent = featureId;
      button.onclick = () => showStrategy(strategyFromFeature(feature));
      list.append(button);
    }
  } catch (error) {
    count.textContent = `ERROR · ${String(error?.message ?? error)}`;
  }

  validateButton.onclick = async () => {
    try {
      status.textContent = 'Parser + Semantic 검증 중...';
      const result = await validateDsl(dsl.value);
      validatedCode = dsl.value;
      applyButton.disabled = false;
      status.textContent = `문법 PASS · ${result.strategy} · ${result.timeframe}`;
      reportStatus?.(`DSL 문법 PASS · ${strategy.name}`);
    } catch (error) {
      validatedCode = undefined;
      applyButton.disabled = true;
      status.textContent = `문법 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
    }
  };

  applyButton.onclick = async () => {
    try {
      if (!validatedCode || validatedCode !== dsl.value) throw new Error('현재 DSL을 먼저 문법 검증하세요.');
      const bars = port.snapshotBars();
      status.textContent = `현재 차트 ${bars.length} bars로 Core 재실행 중...`;
      const result = await evaluateDsl(strategy, bars);
      strategy = {
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
      port.writeAddonState(instanceId, {
        enabled: true,
        definitionId: 'strategy.dsl',
        visible: true,
        state: { strategy: cloneJson(strategy) },
      });
      await port.whenAddonsIdle();
      status.textContent = `적용 PASS · ${strategy.name} · trades ${strategy.validation.trade_count}`;
      reportStatus?.(`DSL 전략 수정 PASS · ${strategy.name}`);
    } catch (error) {
      status.textContent = `적용 FAIL · ${String(error?.message ?? error)}`;
      reportStatus?.(status.textContent);
    }
  };

  deleteButton.onclick = async () => {
    port.writeAddonState(instanceId, {
      enabled: false,
      definitionId: 'strategy.dsl',
      visible: false,
      state: { strategy: cloneJson(strategy) },
    });
    await port.whenAddonsIdle();
    reportStatus?.(`DSL 전략 삭제 · ${strategy.name}`);
    dialog?.close();
  };

  return {
    readState() { return { strategy: cloneJson(strategy) }; },
    dispose() {
      if (outerSave) outerSave.hidden = originalSaveHidden === true;
      if (outerCancel && originalCancelText !== undefined) outerCancel.textContent = originalCancelText;
      host.replaceChildren();
    },
  };
}
