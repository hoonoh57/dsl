import { chartAddonCatalog } from '/src/addons/catalog.mjs';
import { installWorkspaceTimeframeJsonPersistence } from '/__dsl/WorkspaceTimeframeJsonPersistence.mjs';

const runtimeModuleUrl = '/__dsl/DslStrategyRendererAddon.mjs';
const strategyEditorUrl = '/__dsl/DslStrategyPropertiesEditor.mjs';
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
  label: '삽입 DSL 전략',
  category: 'strategy',
  defaultState: { strategy: { name: 'DSL Strategy Runtime', dsl_code: 'strategy "Runtime" { timeframe = "1d" }' } },
  parameters: [],
  editor: {
    async load() { return (await import(strategyEditorUrl)).createDslStrategyPropertiesEditor; },
  },
  registration: {
    id: 'strategy.dsl',
    async load() { return (await import(runtimeModuleUrl)).dslStrategyAddonDefinition; },
  },
};

if (!chartAddonCatalog.some(item => item.id === managerEntry.id)) chartAddonCatalog.push(managerEntry);
if (!chartAddonCatalog.some(item => item.id === rendererSeed.id)) chartAddonCatalog.push(rendererSeed);

const timeframePersistence = await installWorkspaceTimeframeJsonPersistence();
const { MarketChartWorkspace } = await import('/src/shell/index-wysiwyg/MarketChartWorkspace.mjs');
const host = document.getElementById('market-chart-host');
if (!host) throw new Error('Missing #market-chart-host.');
const workspace = new MarketChartWorkspace(host);
await workspace.mount();
window.addEventListener('beforeunload', () => {
  timeframePersistence.flushOnUnload();
  workspace.dispose();
}, { once: true });
