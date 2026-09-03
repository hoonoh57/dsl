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
- JSON/State = independent desired node의 선언/ON-OFF/order/layout persistence만.
- invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; parent/global OFF와 restart도 같은 per-item path 반복.
- feature별 planner/gate에서 product failure가 나와도 semantic 기준을 완화하지 않는다.

### 표준 부품 완료

- JSON-only `ChartDrawingGrammar`, item-local `ChartDrawingRuntime`, pure `ChartDrawingDefinition`.
- independent `ChartDrawingReconciler` + targeted `reconcileItem()`.
- per-item async `ChartDrawingDataRuntime`, live `ChartDrawingStreamRuntime`, sync/async/stream 단일 `ChartDrawingPipeline`.
- opaque surface router/context + State/JSON/Projection `surfaceId` roundtrip.
- independent parent-child State + `ChartDesiredItemProjection`.
- generic action commands `chart.item.remove`, `chart.selection.set`.
- generic `scope:'session'` persistence/restart gate PASS.
- Add-on-owned `StandardDrawingRegistry`: active drawing registration pure definition 커버; `strategy.manager`만 Shell/UI 전용.
- one-time `StandardDrawingStateMigration`: legacy collections -> actual child nodes, parent drawing collection 제거, existing child authority 우선, schemaVersion=2 lock, second migration change 0.
- explicit generic `order`: State/JSON/Projection roundtrip; Compare/Sector/Condition/Battlefield lane order가 explicit metadata로 고정된다.

### feature별 independent state/write planner 완료

- Compare: gate #141 FAIL -> `bf8e65477d3178b47383a810b75c5e369b283500`, #142 PASS.
  - append/replace/timeframe/remove/select locality.
  - parent normal state에 `subjects[]`, `selectedPaneId`, `__layout` 없음.
- MarketBeta: gate #143 FAIL -> `a52d07254290888bac00b3b547b97f633af3970e`, #144 PASS.
  - selected set diff; 1000 중 #537 deselect = child #537 remove 1건.
  - parent normal state에 `selectedSubjects[]` 없음.
- SectorLeadership: gate #145 FAIL -> `894beb6b244c13f99dfc3bd18d1d513973017de3`, #147 PASS.
  - stable code id + role + paletteSlot + order 보존.
  - 중간 child 제거가 sibling recolor/reorder로 전파되지 않음.
- ConditionSearch:
  - gate #148 FAIL.
  - `ConditionSearchIndependentState.mjs` + session child explicit order 추가.
  - READY authoritative session에서만 selected set -> session child diff.
  - child는 `scope:'session'`; STALE/non-ready는 child write 0 + current session child 제거 fail-closed.
  - 1000 READY results 중 #537 uncheck = #537 remove 1건.
  - #150 실패는 frozen plan output에 test가 `.sort()`를 직접 호출한 gate 구현 오류였고 semantic 의미는 변경하지 않았다.
  - `9ab1b469e12d5d51967ee0a6955b4d632abebf5c`, workflow #151 PASS.
- Battlefield Map:
  - gate-only `8b9b9e7dce285b3364febdbb25d6859433164163`, workflow #152 FAIL.
  - parent `subjectSelection`은 정상 semantic state로 유지하고 lane만 current IDs ↔ desired IDs diff.
  - primary subject는 선택 개수와 무관하게 같은 primary overlay path 유지.
  - non-primary local subject만 independent lane child 반복.
  - lane order는 배열 위치가 아니라 canonical identity로 고정: `KOSPI=0`, `KOSDAQ=1`.
  - KOSPI lane 제거가 KOSDAQ lifecycle/order를 변경하지 않음.
  - 제품 `4bb89fb2ed25f37ddef6d3a3291dd9380d907775`, workflow #154 PASS.

### pure Add-on 준비 완료

- Indicator 11종 + 기존 계산 equivalence.
- Trend Regime, Managed Strategy, N_UP_COUNT.
- MarketBeta parent + one-subject-per-child stream/descriptor + independent write planner.
- Compare one subject = child node/stream/pane descriptor + independent write planner.
- SectorLeadership leader/follower independent child + stable role/palette/order + independent write planner.
- ConditionSearch READY session child + stable palette/order + independent write planner; stale restart child 0; realtime I/D pure transition.
- Battlefield Map primary overlay pure parent + non-primary local subject independent lane child + independent write planner.
- Battlefield Force parent regions + one force group per child definition은 존재하지만 **현재 locality 결함 발견으로 미완료**.
- FeatureValidation no-drawing add-on empty pure descriptor.

### 최근 PASS

- standard drawing registry completeness `616843f9b76849fe28b88a1ad3a4395654bb51f0`, #131 PASS.
- one-time independent child state migration `635a85bb671b7081542dc298a3b7ccefa34948c5`, #135 PASS.
- explicit desired item order `08fd22ea6e1bb47fd2700a4cb16ad31ad5e8e354`, #140 PASS.
- Compare planner `bf8e65477d3178b47383a810b75c5e369b283500`, #142 PASS.
- MarketBeta planner `a52d07254290888bac00b3b547b97f633af3970e`, #144 PASS.
- Sector planner/order `894beb6b244c13f99dfc3bd18d1d513973017de3`, #147 PASS.
- Condition planner/order `9ab1b469e12d5d51967ee0a6955b4d632abebf5c`, #151 PASS.
- Battlefield Map planner/canonical lane order `4bb89fb2ed25f37ddef6d3a3291dd9380d907775`, #154 PASS.
- PR #5 current verified head = `4bb89fb2ed25f37ddef6d3a3291dd9380d907775`.

### 새로 발견된 Battlefield Force 제품 결함 — 다음 세션 첫 작업

- 현재 `projectBattlefieldForceGroupChildNodes()`는 각 group child state에 다음을 복제한다:
  - `groupId`
  - `groupIndex`
  - `peerGroups = 전체 forceGroups 복사본`
  - `evaluationState`
- 이 구조에서는 force group 1개 제거 시 남은 모든 child의 `peerGroups`와 일부 `groupIndex`가 바뀔 수 있다.
- 기존 test는 남은 child의 `peerGroups.length`가 2 -> 1로 바뀌는 것을 허용해 **stable id만 검사하고 state/locality 오염을 놓쳤다**.
- 이는 4축 locality 위반이다. 정상 계약은:
  - group #537 제거 -> #537 child remove 1건.
  - 다른 sibling child lifecycle/state rewrite 0.
- child는 자기 `group identity/config + stable order/style + 자기 drawing/data state`만 소유해야 한다.
- cross-group ranking/collective analysis가 실제 기능 의미상 필요하면 일반 child lifecycle에 `peerGroups[]`를 복제하지 말고 **명시적인 collective analysis operation/result**로 분리한다.
- 이 결함을 기존 test 허용사항에 맞춰 유지하거나 semantic gate를 완화하지 않는다.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`는 여전히 `registration.load() -> definition.create(context)` live-object path.
- legacy Add-on이 raw surface/state/getBars/workspace/capabilities/layout/realtime를 소유한다.
- one-time migration은 아직 startup active path에 적용하지 않았다.
- active Compare/MarketBeta/Sector/Condition/Battlefield UI는 아직 legacy parent/feature state write path를 사용한다.
- active UI만 먼저 child-only로 바꾸면 legacy Runtime이 parent collection을 읽으므로 drawing이 중간 commit에서 사라진다. dual-write/fallback은 금지한다.
- independent UI/write planners를 모두 준비한 뒤 active UI composition + migration + RuntimeHost를 single-path cutover tranche에서 함께 전환한다.
- Battlefield Force locality 수정 + independent planner가 아직 필요하다.
- Managed Strategy legacy `subjectViews.watch()` live lifecycle이 남아 있음.
- `strategy.manager` UI/DOM lifecycle이 Runtime Add-on에 남아 있음.
- `ChartSubjectViewManager` whole collection lifecycle과 임시 subject binder가 남아 있음.
- restore-only `__layout` + 별도 layout stabilization/viewport restore path가 남아 있음.

## 할 일

1. **새 세션 첫 작업: Battlefield Force locality gate-first 수정.**
   - 현재 child의 `peerGroups[]` 전체 복제와 index 기반 `groupIndex`가 sibling rewrite를 만드는지 gate로 명시적으로 FAIL시킨다.
   - gate 의미 변경 금지.
   - group 1개 삭제/ON-OFF가 addressed child 1개 lifecycle만 바꾸도록 제품 구조 수정.
   - group stable order/style은 sibling 삭제와 무관하게 보존.
   - cross-group ranking이 필요하면 collective analysis result를 별도 명시적 authority로 분리한다.
   - 그 후 Battlefield Force independent write planner까지 완료한다.

2. Managed Strategy target을 neutral opaque `surfaceId` desired metadata로 이관한다.
   - Add-on -> Runtime helper import 금지.
   - Add-on이 `subjectViews.watch()`/live series/marker lifecycle을 소유하지 않는다.

3. `strategy.manager` UI lifecycle을 Runtime Add-on에서 Shell/UI 축으로 이동한다.

4. independent UI/write 준비 완료 후 **한 번의 active cutover**:
   - startup one-time migration 적용 + migrated JSON persistence authority 저장.
   - active Shell/editor를 independent child CRUD로 전환.
   - `ChartRuntimeHost`를 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환.
   - `.create` fallback/dual-write/이중 active path 금지.
   - legacy drawing live implementations 동시 제거.

5. 이후 `ChartSubjectViewManager`, 임시 binder, legacy collection helpers, restore-only `__layout`, 별도 stabilization/viewport restore path 제거.

6. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, surface/order locality, restart==normal apply, idempotence, single-path + real WYSIWYG restart.

### 새 세션 복구 절차

1. `rules.md` 읽기.
2. 이 `todo.md` 읽기.
3. `hoonoh57/kiwoom-condition` PR #5 / branch `standardize/four-axis-render-pipeline` remote HEAD 재검증.
4. HEAD가 위 기록과 다르면 실제 remote evidence를 우선 확인하되 `rules.md` 의미는 변경하지 않는다.
5. 바로 Battlefield Force locality gate-first 작업부터 계속한다.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
