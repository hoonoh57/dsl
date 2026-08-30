import { chartAddonCatalog } from '/src/addons/catalog.mjs';

const runtimeModuleUrl = '/__dsl/DslStrategyAddon.mjs';
const validationModuleUrl = '/__dsl/DslCatalogValidationManager.mjs';
const validationDefinitionUrl = '/__dsl/DslCatalogValidationDefinition.mjs';

const managerEntry = {
  id: 'strategy.dsl-manager',
  label: '등록 DSL 차트 검증',
  category: 'strategy',
  defaultState: {},
  parameters: [],
  editor: {
    async load() { return (await import(validationModuleUrl)).createDslCatalogValidationEditor; },
  },
  registration: {
    id: 'strategy.dsl-manager',
    async load() { return (await import(validationDefinitionUrl)).dslCatalogValidationDefinition; },
  },
};

const rendererSeed = {
  id: 'strategy.dsl',
  label: 'DSL Strategy Runtime',
  category: 'strategy',
  defaultState: { strategy: { name: 'DSL Strategy Runtime', dsl_code: 'strategy "Runtime" { timeframe = "1d" }' } },
  parameters: [],
  registration: {
    id: 'strategy.dsl',
    async load() { return (await import(runtimeModuleUrl)).dslStrategyAddonDefinition; },
  },
  dslRuntimeSeed: true,
};

if (!chartAddonCatalog.some(item => item.id === managerEntry.id)) chartAddonCatalog.push(managerEntry);
if (!chartAddonCatalog.some(item => item.id === rendererSeed.id)) chartAddonCatalog.push(rendererSeed);

const { MarketChartWorkspace } = await import('/src/shell/index-wysiwyg/MarketChartWorkspace.mjs');
const host = document.getElementById('market-chart-host');
if (!host) throw new Error('Missing #market-chart-host.');
const workspace = new MarketChartWorkspace(host);
await workspace.mount();
for (let index = chartAddonCatalog.length - 1; index >= 0; index -= 1) {
  if (chartAddonCatalog[index]?.dslRuntimeSeed === true) chartAddonCatalog.splice(index, 1);
}
window.addEventListener('beforeunload', () => workspace.dispose(), { once: true });
