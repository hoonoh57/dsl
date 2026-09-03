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
- opaque drawing surface router/context registry.
- independent parent-child State + `ChartDesiredItemProjection`.
- generic action commands `chart.item.remove`, `chart.selection.set`.
- generic `scope:'session'` desired node: in-memory 경로는 동일하고 persistence JSON에서만 제외; save/hydrate/restart gate PASS.
- stale relative Core import integrity gate PASS.

### pure Add-on 준비 완료

- Indicator 11종 + 기존 계산 equivalence.
- Trend Regime, Managed Strategy, N_UP_COUNT.
- MarketBeta parent + one-subject-per-child stream/descriptor.
- Compare: legacy `subjects[]` migration input only → one child/subject; layout height child 이관; generic selection/delete; 1000/#537 locality PASS.
- SectorLeadership: leader/follower one child node/stream/descriptor; stable code id; role/palette state 고정.
- ConditionSearch: authoritative current session일 때만 session child projection; stale restart child 0; realtime I/D pure membership transition.
- FeatureValidation 계열 no-drawing add-on은 empty pure descriptor 준비.
- Battlefield Map:
  - parent = primary markers/regions pure descriptor.
  - local non-primary subject = independent lane child + bars stream + histogram/legend.
  - 기존 `선택 1개 vs N개`에 따라 primary/lane 알고리즘이 바뀌던 cardinality 결함 제거.
- Battlefield Force:
  - parent = opportunity regions only.
  - one force group = one independent child drawing item.
  - group id가 lifecycle identity; group 제거 시 해당 child만 제거.
  - 기존 force normalized series/evaluation과 descriptor equivalence gate 추가.

### 최근 PASS

- MarketBeta stream/pipeline `8700ea1185773660fc1145e585427c5e0ae3b174`, workflow #100 PASS.
- Compare child `2cf88bbdd78824f9428df617c29db45dc11a8e33`, #107 PASS.
- SectorLeadership child `2b775500b9c42bc85b4221ccb6c9bd13b83b1f3c`, #110 PASS.
- ConditionSearch child base `8fa762820021a4b242d7db0f8ab78682d1fef5ef`, #112 PASS.
- session-scope persistence `1c4c3ed2cf332e5c33245ef9ebc9b44bec8c6577`, #115 PASS.
- session restart gate `4f39744251e3834de0a678755fdcacecf6094e5f`, #116 PASS.
- ConditionSearch realtime membership/session child `4f19d8eea6b458865ab556031527ba6bbcc140c2`, #118 PASS.
- Battlefield Map + Battlefield Force standard definitions `f87dc2f0a2014e4029078395acbbf8d371f347c5`, workflow #125 **PASS**.
- PR #5 current head = `f87dc2f0a2014e4029078395acbbf8d371f347c5`.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`/catalog는 legacy `registration.load() -> definition.create(context)` live-object path.
- MarketBeta/Compare/SectorLeadership/ConditionSearch/Battlefield/Managed Strategy legacy live implementations은 아직 active path에 남아 있음.
- `ChartSubjectViewManager` whole collection lifecycle이 살아 있음.
- `ChartSubjectDrawingSurfaceBinder`는 legacy subjectViews와 새 renderer 사이 임시 bridge이며 final child cutover 후 삭제 대상.
- legacy collection JSON + restore-only `__layout` authority가 남아 있음.
- `MarketChart.whenAddonsIdle()` 뒤 별도 layout restore/stabilize/viewport 경로가 남아 있음.
- generic Runtime은 `surfaceId`를 지원하지만 State/JSON/DesiredItemProjection이 아직 `surfaceId` metadata를 보존하지 않아 target-surface item의 단일경로가 끊겨 있음.
- `strategy.manager`는 drawing이 아닌 UI/관리 lifecycle을 Runtime Add-on이 소유하므로 Shell/UI 축으로 이동 필요.

## 할 일

1. **`surfaceId`를 State → persistence JSON → DesiredItemProjection까지 generic metadata로 관통시킨다.**
   - default/persistent/session node 모두 동일 계약.
   - `surfaceId`는 feature 의미를 모르는 opaque string이다.
   - 1000 items 중 #537 `surfaceId`만 변경하면 #537만 rebind/reconcile되고 나머지 999 lifecycle은 0이어야 한다.

2. pure drawing/data/stream **standard registry completeness gate**를 만든다.
   - 모든 active drawing definition이 legacy `.create(context)` 없이 표준 registry에서 표현 가능해야 한다.
   - Compare/Sector/Condition처럼 parent가 직접 그리지 않으면 empty pure parent definition으로 등록한다.
   - drawing이 아닌 `strategy.manager`는 registry에 억지로 넣지 않고 Shell/UI 축으로 이동한다.

3. Managed Strategy target rendering을 `target -> opaque surfaceId` desired state로 전환한다.
   - Add-on이 `subjectViews.watch()`/live series/marker lifecycle을 소유하지 않는다.
   - surface binding은 generic Runtime infrastructure만 소유한다.

4. 모든 feature 표준 registry 완결 후 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create`/`.describe` fallback/이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

5. 이후 `ChartSubjectViewManager`, 임시 subject binder, legacy collection JSON, restore-only `__layout`, 별도 stabilization/viewport restore path를 제거/마이그레이션한다.

6. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, surface locality, restart==normal apply, idempotence, single-path.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
