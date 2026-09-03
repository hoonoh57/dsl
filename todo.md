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
- per-item async `ChartDrawingDataRuntime`, live `ChartDrawingStreamRuntime`, sync/async/stream 단일 `ChartDrawingPipeline`.
- opaque drawing surface router/context registry + State/JSON/Projection `surfaceId` roundtrip.
- independent parent-child State + `ChartDesiredItemProjection`.
- generic action commands `chart.item.remove`, `chart.selection.set`.
- generic `scope:'session'` desired node persistence/restart gate PASS.
- Add-on-owned `StandardDrawingRegistry`: 모든 active drawing registration pure definition으로 커버, `strategy.manager`만 Shell/UI 전용.
- **one-time legacy drawing state migration 계약 완료**:
  - gate-only `629df59...`를 먼저 추가해 migration 부재 FAIL 확인.
  - authoritative Sector fixture 사실오류만 gate-only `f019687...`에서 교정.
  - 제품 `StandardDrawingStateMigration` 구현.
  - Compare/MarketBeta/Sector/Condition/Battlefield Map/Battlefield Force legacy state를 independent child node로 materialize.
  - Compare/Sector legacy selection은 generic `display.activeSubject`로 migration.
  - legacy parent drawing collection field 제거.
  - child가 이미 존재하면 overwrite하지 않아 independent node authority 우선.
  - document schemaVersion=2로 one-time 완료를 고정하여 다음 startup에서 migrator 재진입 금지.
  - 동일 결과에 두 번째 migration 변화 0.
  - Compare 1000 subjects -> 1000 stable child identities, #537 보존.

### pure Add-on 준비 완료

- Indicator 11종 + 기존 계산 equivalence.
- Trend Regime, Managed Strategy, N_UP_COUNT.
- MarketBeta parent + one-subject-per-child stream/descriptor.
- Compare: one subject = child node/stream/pane descriptor; layout height 이관; generic selection/delete.
- SectorLeadership: leader/follower independent child; stable code id; role/palette state 고정.
- ConditionSearch: authoritative current session only session child; stale restart child 0; realtime I/D pure transition.
- Battlefield Map: primary overlay pure parent + non-primary local subject independent lane child; N에 따른 경로 변경 결함 제거.
- Battlefield Force: parent regions + one force group per child; group id lifecycle identity.
- FeatureValidation no-drawing add-on empty pure descriptor.

### 최근 PASS

- Battlefield Map + Battlefield Force `f87dc2f0a2014e4029078395acbbf8d371f347c5`, #125 PASS.
- surface desired-state route `a9c7c86d05a17c3f222945039e64c79eac6948ce`, #129 PASS.
- standard drawing registry completeness `616843f9b76849fe28b88a1ad3a4395654bb51f0`, #131 PASS.
- one-time independent child state migration `635a85bb671b7081542dc298a3b7ccefa34948c5`, workflow #135 **PASS**.
- PR #5 current verified head = `635a85bb671b7081542dc298a3b7ccefa34948c5`.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`는 여전히 `registration.load() -> definition.create(context)` live-object path.
- legacy Add-on이 raw surface/state/getBars/workspace/capabilities/layout/realtime를 소유한다.
- migration 계약은 준비됐지만 **아직 startup active path에 적용하지 않았다**. 기존 UI가 parent collection을 다시 쓰므로 지금 적용하면 legacy Runtime과 충돌한다.
- Compare/MarketBeta/Sector/Condition/Battlefield/Force editor/shell write path가 아직 independent child CRUD로 완전히 전환되지 않았다.
- Managed Strategy legacy `subjectViews.watch()` live lifecycle이 남아 있음.
- `strategy.manager` UI/DOM lifecycle이 Runtime Add-on에 남아 있음.
- `ChartSubjectViewManager` whole collection lifecycle과 임시 subject binder가 남아 있음.
- restore-only `__layout` + 별도 layout stabilization/viewport restore path가 남아 있음.

## 할 일

1. **UI/editor write path를 independent State write로 전환한다.**
   - 첫 순서 Compare Shell: append/replace/delete/select가 parent `subjects[]`를 쓰지 않고 child node CRUD + parent semantic state만 쓴다.
   - 이후 MarketBeta, SectorLeadership, ConditionSearch, Battlefield Map, Battlefield Force 순으로 동일 원칙 적용.
   - Condition child는 `scope:'session'` 유지.
   - parent collection을 normal write로 재생성하는 코드 금지.

2. Managed Strategy target을 neutral opaque `surfaceId` desired metadata로 이관한다.
   - Add-on -> Runtime helper import 금지.
   - Add-on이 `subjectViews.watch()`/live series/marker lifecycle을 소유하지 않는다.

3. `strategy.manager` UI lifecycle을 Runtime Add-on에서 Shell/UI 축으로 이동한다.

4. UI/State 준비가 끝나면 startup에 one-time migration을 적용하고 migrated JSON을 persistence authority로 저장한다.

5. 그 직후 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create` fallback/이중 active path 금지.
   - legacy drawing live implementations 동시 제거.

6. `ChartSubjectViewManager`, 임시 binder, legacy collection helpers, restore-only `__layout`, 별도 stabilization/viewport restore path 제거.

7. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, surface locality, restart==normal apply, idempotence, single-path + real WYSIWYG restart.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
