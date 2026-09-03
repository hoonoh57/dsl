# todo.md — 한 일 / 할 일

## 한 일

- 권위 파일은 `rules.md` + `todo.md` 두 개뿐이다. 세션 복구는 `rules.md` → `todo.md` 순서다.
- 전체 상태는 계속 `REMEDIATION_REQUIRED`다. UIA-1/Chart 구조/global PASS는 아직 선언하지 않는다.
- Chart 작업은 `hoonoh57/kiwoom-condition` branch `standardize/four-axis-render-pipeline`, draft PR #5에서만 진행한다.
- PR #5는 **DO NOT MERGE until legacy drawing lifecycle is removed** 상태를 유지한다.
- dsl 작업 branch는 `dsl-live-studio`; `origin/main`을 섞지 않는다.

### 4축 현재 계약

- Core = generic drawing primitive/grammar만 소유한다.
- Add-on = 계산 의미, drawing 종류, pure reducer/data request/descriptor만 소유한다.
- Runtime = feature-blind per-item data/drawing lifecycle과 surface translation만 소유한다.
- JSON/State = 선언/ON-OFF persistence다. raw JSON이 Core를 직접 실행하지 않는다.
- 핵심 invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; parent/global OFF/restart도 동일 per-item path 반복이다.

### 표준 부품 완료

- `ChartDrawingGrammar`: JSON-only generic primitives.
- `ChartDrawingRuntime`: item-local `ensure/update/setVisible/remove`.
- `ChartDrawingDefinition`: pure synchronous `describe(...,data?)` + optional pure `reduce()`.
- `ChartDrawingReconciler`: independent desired-item diff + targeted `reconcileItem()`.
- `ChartDrawingPipeline`: async data ready event를 해당 item drawing에만 연결; whole-list async completion 재스캔 금지.
- `ChartDrawingDataDefinition/DataRuntime`: per-item async generation/cancel/stale rejection + `dataKey()` + AbortSignal.
- `ChartDrawingSurfaceRouter/ContextRegistry`: opaque surfaceId translation.
- `ChartSubjectDrawingSurfaceBinder`: legacy subjectViews와 새 renderer 사이 임시 bridge; 최종 child 전환 후 삭제 대상.
- `ChartAddonStateStore`: 기존 `addons[id]` 독립 node에 optional `parentId` persistence를 추가했다. 별도 children collection/storage는 만들지 않았다.
- `ChartDesiredItemProjection`: node parent chain을 generic `effectiveEnabled`로 계산한다. missing parent/cycle은 해당 chain만 fail-closed한다.

### pure Add-on 준비 완료 범위

- Indicator 11종 pure descriptor + 기존 계산 equivalence.
- Trend Regime pure line/marker/region descriptor.
- Managed Strategy pure fast/slow JMA + signal markers descriptor.
- N_UP_COUNT `dataKey + loadData + pane/histogram descriptor`.
- MarketBetaCohort는 **primary beta high/low line/data 경계만** pure 준비. `selectedSubjects[]` collection은 아직 legacy다.

### semantic gate / 최근 PASS

- 1000 drawing items = 동일 `ensure(item)` 1000회; `item-537` 단독 변경은 해당 item만 touch.
- 1000 async items = 동일 start path; cancel/failure/stale result locality.
- async ready = targeted drawing 1건; calculation-only state 변경은 data 재사용 + drawing 1건.
- parent/child state도 같은 Store → Projection → Pipeline 경로를 사용한다.
- 1000 child + parent에서 `child-537` OFF = `remove(child-537)` 1건, 나머지 1000 unchanged.
- parent OFF = 현재 live parent/descendant에 동일 per-item remove 반복; parent ON = 동일 ensure 반복.
- restart = 같은 persisted nodes를 같은 normal ensure path로 재생한다.
- global `visualsVisible`도 모든 item의 visible gate만 동일 per-item update한다.
- missing parent/cycle은 unrelated item을 건드리지 않고 invalid chain만 disabled 처리한다.

PASS checkpoints:
- per-surface context `d27ca7d9...` workflow #57 PASS.
- subject binder `fbaddb6d...` workflow #63 PASS.
- async DataRuntime/dataKey `39238f43...` workflow #72 PASS.
- N_UP_COUNT + AbortSignal adapter `15747325...` workflow #76 PASS.
- MarketBeta primary line/data `e9f76756...` workflow #79 PASS.
- async-data → targeted-drawing Pipeline `7e990dc5...` workflow #83 PASS.
- independent child state/projection `d83084c35a6e47e7021038bcd399f8e340b2bc35` workflow #86 **PASS**.

### 아직 NONSTANDARD인 핵심

- active RuntimeHost/catalog는 legacy `definition.create(context)` live object path다.
- Compare/ConditionSearch/SectorLeadership/MarketBeta selectedSubjects는 collection/owner whole lifecycle이다.
- `ChartSubjectViewManager`는 `subjects[] -> whole signature/revision/replace(owner)` 구조다.
- JSON에는 compare `subjects[]`, restore-only `__layout` 등 collection authority가 남아 있다.
- `MarketChart.whenAddonsIdle()` 이후 별도 layout restore/stabilize/viewport 경로가 남아 있다.
- 따라서 PR #5는 계속 draft이며 dsl submodule main baseline은 아직 advance하지 않는다.

## 할 일

1. **첫 실제 independent child drawing 사례를 만든다.**
   - 우선 MarketBeta `selectedSubjects`를 대상으로 공용 bars service 경계를 확인한다.
   - one subject = one persisted node + one data request + one pane/candlestick/legend descriptor.
   - bar loading/subscription을 현재 one-shot DataRuntime에 억지로 끼우지 않는다. 공용 bars 계약이 live stream이면 generic per-item stream 계약을 먼저 만든다.
   - subject 하나 추가/삭제/갱신이 다른 subject에 영향 없어야 한다.

2. MarketBeta child PASS 후 Compare / SectorLeadership / ConditionSearch를 같은 independent child node 구조로 이행한다.
   - Compare `subjects[]` whole signature/revision/pending/replace 제거.
   - Condition realtime membership은 state node add/remove만 수행하고 drawing lifecycle을 직접 소유하지 않는다.

3. 모든 feature가 pure definition/data/reducer 준비된 뒤 RuntimeHost를 **한 번의 경계 변경**으로 Pipeline 단일 active path로 전환한다.
   - `.create`/`.describe` fallback 또는 이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

4. 이후 `ChartSubjectViewManager` collection lifecycle, compare collection JSON, restore-only `__layout`, 별도 layout stabilization path를 제거/마이그레이션한다.

5. 최종 gate에서 1/10/1000 cardinality, locality, async/stream locality, global/item equivalence, restart==normal apply, idempotence, single-path를 전체 제품경로로 검증한다.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
