# todo.md — 한 일 / 할 일

## 한 일

- 권위 파일은 `rules.md` + `todo.md` 두 개뿐이다. 세션 복구는 `rules.md` → `todo.md` 순서다.
- 전체 상태는 `REMEDIATION_REQUIRED`. UIA-1/Chart 구조/global PASS는 아직 금지다.
- Chart 작업: `hoonoh57/kiwoom-condition` branch `standardize/four-axis-render-pipeline`, draft PR #5.
- PR #5는 **DO NOT MERGE until legacy drawing lifecycle is removed** 상태다.
- dsl branch는 `dsl-live-studio`; `origin/main`을 섞지 않는다.

### 4축 고정 계약

- Core = generic drawing grammar/primitives만.
- Add-on = feature 계산/의미 + pure descriptor/reducer/data/stream request만.
- Runtime = feature-blind per-item translation/lifecycle만.
- JSON/State = independent desired node의 선언/ON-OFF persistence만.
- invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; parent/global OFF와 restart도 같은 per-item path 반복.

### 표준 부품 완료

- JSON-only `ChartDrawingGrammar`.
- item-local `ChartDrawingRuntime.ensure/update/setVisible/remove`.
- pure `ChartDrawingDefinition.describe/reduce`.
- independent `ChartDrawingReconciler` + targeted `reconcileItem()`.
- per-item one-shot async `ChartDrawingDataRuntime` + `dataKey` + AbortSignal.
- per-item live `ChartDrawingStreamRuntime` + JSON snapshot/event reduction.
- sync/async/stream 단일 `ChartDrawingPipeline`.
- opaque surface router/context registry.
- independent parent-child State + `ChartDesiredItemProjection`.
- generic action commands `chart.item.remove`, `chart.selection.set`.
- **generic session-scoped desired node**:
  - in-memory State/Projection은 persistent node와 동일 경로.
  - `scope:'session'`만 수명 metadata로 보유.
  - `persistentChartAddonStateDocument()`가 disk JSON 경계에서 session node를 제거.
  - load/hydrate/save/unload/saveAddon 모두 session node를 persistence authority에서 제외.
  - persistent sibling은 그대로 유지.

### pure Add-on 준비 완료

- Indicator 11종, Trend Regime, Managed Strategy, N_UP_COUNT.
- MarketBeta parent + independent child.
- Compare independent child:
  - legacy `subjects[]` migration input only.
  - one subject = child node + bars stream + pane/candlestick/legend.
  - `__layout` height를 child paneHeight로 정확히 이관.
  - selectedPaneId -> generic selection.
  - 1000 subject locality PASS.
- SectorLeadership independent child:
  - leader/follower = independent child node/stream/descriptor.
  - code-stable id, role/palette state 고정, generic select/delete.
- ConditionSearch independent child base:
  - current authoritative session일 때만 child projection.
  - one stock = child node/stream/descriptor.
  - stale persisted selection은 session authority 없으면 child 0개.
  - 최종 child node는 `scope:'session'` 사용 예정.

### 최근 PASS

- MarketBeta stream/pipeline `8700ea1185773660fc1145e585427c5e0ae3b174`, workflow #100 PASS.
- Compare child `2cf88bbdd78824f9428df617c29db45dc11a8e33`, #107 PASS.
- SectorLeadership child `2b775500b9c42bc85b4221ccb6c9bd13b83b1f3c`, #110 PASS.
- ConditionSearch child base `8fa762820021a4b242d7db0f8ab78682d1fef5ef`, #112 PASS.
- session-scope persistence `1c4c3ed2cf332e5c33245ef9ebc9b44bec8c6577`, workflow #115 **PASS**.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`/catalog는 legacy `definition.create(context)` live-object path.
- MarketBeta/Compare/SectorLeadership/ConditionSearch active legacy lifecycle은 아직 살아 있음.
- `ChartSubjectViewManager` whole collection lifecycle이 살아 있음.
- legacy collection JSON + restore-only `__layout` authority가 남아 있음.
- 별도 layout restore/stabilize/viewport 경로가 남아 있음.

## 할 일

1. **session-scope restart gate를 완성한다.**
   - live Store에 persistent+session node 생성.
   - 저장된 JSON에는 persistent만 존재.
   - hydrate -> 새 Store -> DesiredItemProjection에서 session node 0개 확인.
   - persistent sibling은 동일 normal apply 대상이어야 한다.

2. ConditionSearch realtime membership을 parent feature state + session child node add/remove로 분리한다.
   - selected child 생성은 `scope:'session'`.
   - membership D는 해당 child만 remove + parent resultCodes 갱신.
   - membership I는 parent resultCodes만 갱신하며 selected child를 임의 생성하지 않는다.

3. 모든 feature 준비 후 `ChartRuntimeHost`를 한 번의 경계 변경으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create`/`.describe` fallback/이중 active path 금지.
   - 동시에 legacy drawing live implementations 제거.

4. 이후 `ChartSubjectViewManager`, legacy collection JSON, restore-only `__layout`, 별도 stabilization path 제거/마이그레이션.

5. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, restart==normal apply, idempotence, single-path.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
