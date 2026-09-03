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
- **opaque `surfaceId` desired-state route 완료**:
  - gate-only `df13fa7...`에서 State/persistence/projection 유실을 먼저 FAIL로 확인.
  - gate 의미 변경 없이 State normalization + persistence hydrate merge + DesiredItemProjection만 수정.
  - `State -> JSON -> DesiredItemProjection -> Pipeline -> SurfaceRouter`에서 `surfaceId` 보존.
  - 1000 items 중 #537 `surfaceId` 변경 시 #537만 재적용, 999 lifecycle 0.
- **pure standard drawing registry 완료**:
  - Add-on 축 `StandardDrawingRegistry`가 drawing/data/stream pure definitions를 제공.
  - Runtime은 feature module을 직접 해석하지 않고 향후 definitions 주입만 받는 구조.
  - 모든 active registration은 pure drawing registry 또는 shell-only owner로 분류.
  - `strategy.manager`만 drawing registry 밖 Shell/UI 전용으로 명시.
  - generated child definition도 first-class registry member.

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

- MarketBeta stream/pipeline `8700ea1185773660fc1145e585427c5e0ae3b174`, #100 PASS.
- Compare child `2cf88bbdd78824f9428df617c29db45dc11a8e33`, #107 PASS.
- SectorLeadership child `2b775500b9c42bc85b4221ccb6c9bd13b83b1f3c`, #110 PASS.
- ConditionSearch child base `8fa762820021a4b242d7db0f8ab78682d1fef5ef`, #112 PASS.
- session-scope persistence `1c4c3ed2cf332e5c33245ef9ebc9b44bec8c6577`, #115 PASS.
- session restart gate `4f39744251e3834de0a678755fdcacecf6094e5f`, #116 PASS.
- ConditionSearch realtime membership/session child `4f19d8eea6b458865ab556031527ba6bbcc140c2`, #118 PASS.
- Battlefield Map + Battlefield Force `f87dc2f0a2014e4029078395acbbf8d371f347c5`, #125 PASS.
- surface desired-state route `a9c7c86d05a17c3f222945039e64c79eac6948ce`, workflow #129 **PASS**.
- standard drawing registry completeness `616843f9b76849fe28b88a1ad3a4395654bb51f0`, workflow #131 **PASS**.
- PR #5 current verified head = `616843f9b76849fe28b88a1ad3a4395654bb51f0`.

### 아직 NONSTANDARD / 새로 확인된 cutover blocker

- active `ChartRuntimeHost`는 여전히 `registration.load() -> definition.create(context)` live-object path다.
- legacy Add-on에 raw surface/state/getBars/workspace/capabilities/layout/realtime를 주고 `onStateChanged/onBarsReset/onBarChanged/whenIdle/dispose` lifecycle을 구동한다.
- MarketBeta/Compare/SectorLeadership/ConditionSearch/Battlefield/Managed Strategy legacy live implementations은 아직 active path에 남아 있음.
- **pure child definitions는 준비됐지만 실제 persisted State에는 아직 independent child node가 생성되지 않는다.**
- 현재 JSON의 `subjects[]`, `selectedSubjects[]`, leader/followers, `forceGroups[]` 등 legacy parent collection이 아직 실제 authority다.
- Host만 먼저 새 pipeline으로 바꾸면 child desired item이 없어 기능이 사라지므로 cutover 전에 one-time State migration + UI write-path 전환이 필수다.
- `ChartSubjectViewManager` whole collection lifecycle이 살아 있음.
- `ChartSubjectDrawingSurfaceBinder`는 legacy subjectViews와 새 renderer 사이 임시 bridge이며 final child cutover 후 삭제 대상.
- legacy collection JSON + restore-only `__layout` authority가 남아 있음.
- `MarketChart.whenAddonsIdle()` 뒤 별도 layout restore/stabilize/viewport 경로가 남아 있음.
- `strategy.manager`는 drawing이 아닌 UI/관리 lifecycle을 Runtime Add-on이 소유하므로 Shell/UI 축으로 이동 필요.

## 할 일

1. **legacy parent collection -> independent child node one-time migration 계약을 먼저 만든다.**
   - legacy collection은 migration input으로만 허용하고 normal reconcile authority로 남기지 않는다.
   - migration 후 parent state에서는 drawing collection authority를 제거한다.
   - child는 실제 `addons[id]` State node로 생성한다.
   - migration을 두 번 적용해도 두 번째 변화 0인 idempotence gate가 필요하다.
   - 1000 collection 중 #537 identity가 one child identity로 보존되어야 한다.

2. UI/editor write path를 feature별로 independent State write로 전환한다.
   - Compare/MarketBeta/Sector/Condition/Battlefield/Force가 parent collection을 다시 쓰지 못하게 한다.
   - item add/remove/update는 해당 child node만 write/remove한다.
   - Condition child는 `scope:'session'` 유지.

3. Managed Strategy target을 neutral opaque `surfaceId` desired metadata로 이관한다.
   - Add-on -> Runtime helper import 금지.
   - Add-on이 `subjectViews.watch()`/live series/marker lifecycle을 소유하지 않는다.

4. `strategy.manager` UI lifecycle을 Runtime Add-on에서 Shell/UI 축으로 이동한다.

5. 위 State/UI 준비가 끝난 뒤 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create` fallback/이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

6. 이후 `ChartSubjectViewManager`, 임시 subject binder, legacy collection JSON, restore-only `__layout`, 별도 stabilization/viewport restore path를 제거한다.

7. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, surface locality, restart==normal apply, idempotence, single-path + real WYSIWYG restart.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
