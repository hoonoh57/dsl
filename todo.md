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
- explicit generic `order`: State/JSON/Projection roundtrip; Compare/Sector/Condition migration이 child order를 명시.
- Compare independent planner: gate #141 FAIL -> `bf8e65477d3178b47383a810b75c5e369b283500`, #142 PASS.
- MarketBeta independent planner: gate #143 FAIL -> `a52d07254290888bac00b3b547b97f633af3970e`, #144 PASS.
- SectorLeadership independent planner: gate #145 FAIL -> `894beb6b244c13f99dfc3bd18d1d513973017de3`, #147 PASS. stable role/palette/order, #537 locality.
- **ConditionSearch independent state planner 완료**:
  - gate-only `487f315d0a80b3d7b4d3ebc4287c0209d49ddf09`, workflow #148 FAIL.
  - 제품 `ConditionSearchIndependentState.mjs` + session child explicit order 추가.
  - READY authoritative session에서만 selected set -> session child diff 허용.
  - child는 `scope:'session'`; persistence authority로 승격하지 않음.
  - existing child palette/order 보존; 중간 제거가 sibling recolor/reorder로 전파되지 않음.
  - 1000 READY results 중 #537 uncheck = #537 remove 1건.
  - STALE/non-ready session = child write 0, current session child 제거로 fail closed.
  - parent normal state에 `selectedSubjects[]` 없음.
  - 제품 head `77e8df57648d8c06ea7583f03ad873e2f8cd0ebf`의 workflow #150은 semantic 실패가 아니라 test가 frozen `itemRemoves`에 `.sort()`를 직접 호출한 gate 구현 오류 1건으로 FAIL; 나머지 265/266 PASS.
  - gate 의미 변경 없이 복사본 정렬로 구현만 교정한 `9ab1b469e12d5d51967ee0a6955b4d632abebf5c`, workflow #151 **PASS**.

### pure Add-on 준비 완료

- Indicator 11종 + 기존 계산 equivalence.
- Trend Regime, Managed Strategy, N_UP_COUNT.
- MarketBeta parent + one-subject-per-child stream/descriptor + independent write planner.
- Compare one subject = child node/stream/pane descriptor + independent write planner.
- SectorLeadership leader/follower independent child + stable role/palette/order + independent write planner.
- ConditionSearch READY session child + stable palette/order + independent write planner; stale restart child 0; realtime I/D pure transition.
- Battlefield Map primary overlay pure parent + non-primary local subject independent lane child.
- Battlefield Force parent regions + one force group per child.
- FeatureValidation no-drawing add-on empty pure descriptor.

### 최근 PASS

- standard drawing registry completeness `616843f9b76849fe28b88a1ad3a4395654bb51f0`, #131 PASS.
- one-time independent child state migration `635a85bb671b7081542dc298a3b7ccefa34948c5`, #135 PASS.
- explicit desired item order `08fd22ea6e1bb47fd2700a4cb16ad31ad5e8e354`, #140 PASS.
- Compare planner `bf8e65477d3178b47383a810b75c5e369b283500`, #142 PASS.
- MarketBeta planner `a52d07254290888bac00b3b547b97f633af3970e`, #144 PASS.
- Sector planner/order `894beb6b244c13f99dfc3bd18d1d513973017de3`, #147 PASS.
- Condition planner/order + gate implementation correction `9ab1b469e12d5d51967ee0a6955b4d632abebf5c`, workflow #151 **PASS**.
- PR #5 current verified head = `9ab1b469e12d5d51967ee0a6955b4d632abebf5c`.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`는 여전히 `registration.load() -> definition.create(context)` live-object path.
- legacy Add-on이 raw surface/state/getBars/workspace/capabilities/layout/realtime를 소유한다.
- migration은 아직 startup active path에 적용하지 않았다.
- active Compare/MarketBeta/Sector/Condition UI는 아직 legacy parent collection을 쓴다.
- active UI만 먼저 child-only로 바꾸면 legacy Runtime이 parent collection을 읽으므로 drawing이 중간 commit에서 사라진다. dual-write/fallback은 금지한다.
- independent UI/write planners를 모두 준비한 뒤 active UI composition + migration + RuntimeHost를 single-path cutover tranche에서 함께 전환한다.
- Battlefield Map/Force independent write planner 준비 필요.
- Managed Strategy legacy `subjectViews.watch()` live lifecycle이 남아 있음.
- `strategy.manager` UI/DOM lifecycle이 Runtime Add-on에 남아 있음.
- `ChartSubjectViewManager` whole collection lifecycle과 임시 subject binder가 남아 있음.
- restore-only `__layout` + 별도 layout stabilization/viewport restore path가 남아 있음.

## 할 일

1. **feature별 independent write planner를 gate-first로 완성한다.**
   - 다음 Battlefield Map -> Battlefield Force.
   - normal action은 addressed child만 write/remove; parent는 semantic state만 유지.
   - Battlefield Map `subjectSelection`은 parent semantic state이므로 제거하지 않고 lane child만 ID diff한다.
   - collection 재생성 금지.

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

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
