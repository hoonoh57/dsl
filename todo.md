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
- 핵심 invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; global OFF/restart도 동일 per-item path 반복이다.

### 표준 부품 완료

- Core `ChartDrawingGrammar`: `pane/line/histogram/candlestick/legend/markers/region`, JSON-only, callback/live handle 금지.
- Runtime `ChartDrawingRuntime`: `ensure/update/setVisible/remove`, item-local rollback/dispose.
- `ChartDrawingDefinition`: synchronous pure `describe({id,state,bars,workspace,data?})` + optional pure `reduce()`.
- `ChartDrawingReconciler`: independent desired item set-diff, 1000-item cardinality/locality, surfaceId/context 지원.
- `ChartDrawingSurfaceRouter` + `ChartDrawingSurfaceContextRegistry`: opaque surfaceId routing/context.
- `ChartSubjectDrawingSurfaceBinder`: legacy subjectViews와 새 renderer 사이 임시 ref-count bridge. 최종 subject item 전환 후 삭제 대상.
- `ChartDrawingDataDefinition` + `ChartDrawingDataRuntime`: per-item async generation/cancel/stale-result rejection, AbortSignal, optional pure `dataKey()`.
- `BrowserDailyMarketDataPort`: optional AbortSignal을 실제 fetch까지 전달.
- stale relative Core import 전수감사 gate 추가 및 발견된 TrendRegime/ManagedStrategy stale dependency 제거.

### pure Add-on 준비 완료 범위

- Indicator 11종: SMA/EMA/JMA/Bollinger/SuperTrend/VWAP/RSI/MACD/Disparity/DMI/OBV pure descriptor + 기존 계산 equivalence.
- Trend Regime: line/marker/region pure descriptor + frozen opportunity authority.
- Managed Strategy: fast/slow JMA + signal markers pure descriptor; target surface generic routing 준비.
- N_UP_COUNT: `dataKey + loadData + pane/histogram descriptor`; threshold 변경은 raw rows 재사용.
- MarketBetaCohort: **primary beta high/low line/data 경계만** pure 계약 준비. `selectedSubjects[] -> subjectViews.replace()`는 아직 legacy collection lifecycle이다.

### semantic gate / 최근 PASS

- 1000 drawing items first apply = 동일 `ensure(item)` 1000회.
- `item-537` OFF/ON/state/visible/surface 변경 = 해당 item만 touch.
- global OFF = 동일 per-item remove 반복.
- restart = first apply와 동일 path.
- 1000 async items = 동일 per-item start; cancel/failure/stale result locality 보장.
- async data ready completion은 whole-list rescan 없이 해당 item만 targeted drawing reconcile하도록 `ChartDrawingPipeline`을 추가했다.
- calculation-only state change에서 dataKey가 같으면 data version/refetch는 유지되고 해당 drawing item만 다시 ensure한다.
- request identity가 바뀌면 해당 item drawing만 remove → 새 data ready 후 ensure한다.
- sync/async definition은 동일 Pipeline에서 feature branch 없이 공존한다.

PASS checkpoints:
- per-surface context `d27ca7d9...` workflow #57 PASS.
- subject binder `fbaddb6d...` workflow #63 PASS.
- async DataRuntime/dataKey `39238f43...` workflow #72 PASS.
- N_UP_COUNT + AbortSignal adapter `15747325...` workflow #76 PASS.
- MarketBeta primary line/data `e9f76756...` workflow #79 PASS.
- async-data → targeted-drawing Pipeline `7e990dc5003b280cc7872200a5e5153b99604b9b` workflow #83 **PASS**.

### 아직 NONSTANDARD인 핵심

- active catalog/RuntimeHost는 여전히 legacy `definition.create(context)` live object path다.
- Add-on live classes가 raw surface/pane/series/subjectViews/bar-window/projection lifecycle을 아직 소유한다.
- Compare/ConditionSearch/SectorLeadership/MarketBeta selectedSubjects는 collection/owner whole lifecycle을 가진다.
- `ChartSubjectViewManager`는 `subjects[] -> whole signature/revision/replace(owner)` 구조다.
- JSON/Persistence에는 compare `subjects[]`, restore-only `__layout` 등 collection authority가 남아 있다.
- `MarketChart.whenAddonsIdle()` 이후 별도 layout restore/stabilize/viewport 경로가 남아 있다.
- 따라서 PR #5는 계속 draft이며 dsl submodule main baseline은 아직 advance하지 않는다.

## 할 일

1. **독립 child item persistence/state 계약을 먼저 만든다.**
   - 부모 `subjects[]` 배열을 Runtime lifecycle authority로 사용하지 않는다.
   - 각 child는 stable `itemId + definitionId + enabled + visible + state + parentId?`를 독립 state node로 가진다.
   - parent/global enabled는 child `effectiveEnabled` gate만 만든다. 별도 whole-replace lifecycle은 금지한다.
   - 1/10/1000 child와 `#537` 단독 ON/OFF/remove/restart가 동일 state-read → Pipeline path인지 semantic gate로 검증한다.

2. 첫 실제 child 사례는 코드 경계가 가장 작은 것을 선택한다.
   - 우선 MarketBeta `selectedSubjects`를 검토한다.
   - subject 하나 = 독립 bar-data request + pane/candlestick/legend descriptor.
   - subject 하나 삭제/추가가 다른 subject pane/data를 건드리지 않아야 한다.
   - legacy `subjectViews.replace(owner)` 위에 descriptor를 병행 활성화하지 않는다.

3. 그 다음 Compare / SectorLeadership / ConditionSearch를 독립 child item으로 이행한다.
   - Compare `subjects[]` whole signature/revision/pending/replace 제거.
   - Sector/Condition의 subject pane도 동일 child pipeline 사용.
   - Condition realtime membership은 state item add/remove만 수행하고 drawing lifecycle을 직접 소유하지 않는다.

4. 모든 feature가 pure definition/data/reducer 준비된 뒤 RuntimeHost를 **한 번의 경계 변경**으로 Pipeline 단일 active path로 전환한다.
   - `.create`/`.describe` fallback 또는 이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations를 제거한다.

5. 이후 `ChartSubjectViewManager` collection lifecycle, compare collection JSON, restore-only `__layout`, 별도 layout stabilization path를 제거/마이그레이션한다.

6. 최종 gate에서 1/10/1000 cardinality, locality, async locality, global/item equivalence, restart==normal apply, idempotence, single-path를 전체 제품경로로 검증한다.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
