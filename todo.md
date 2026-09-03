# todo.md — 한 일 / 할 일

## 한 일

- 권위 파일은 `rules.md` + `todo.md` 두 개뿐이다. 세션 복구는 `rules.md` → `todo.md` 순서다.
- 전체 상태는 `REMEDIATION_REQUIRED`. UIA-1/Chart 구조/global PASS는 아직 금지다.
- Chart 작업: `hoonoh57/kiwoom-condition` branch `standardize/four-axis-render-pipeline`, draft PR #5.
- PR #5는 **DO NOT MERGE until legacy drawing lifecycle is removed** 상태다.
- dsl 작업 branch는 `dsl-live-studio`; `origin/main`을 섞지 않는다.

### 4축 고정 계약

- Core = generic drawing grammar/primitives만.
- Add-on = feature 계산/의미 + pure descriptor/reducer/data/stream request만.
- Runtime = feature-blind per-item translation/lifecycle만.
- JSON/State = independent desired node의 persistence/ON-OFF만.
- invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; parent/global OFF와 restart도 같은 per-item path 반복.

### 표준 부품 완료

- `ChartDrawingGrammar`: JSON-only `pane/line/histogram/candlestick/legend/markers/region`.
- `ChartDrawingRuntime`: item-local `ensure/update/setVisible/remove`.
- `ChartDrawingDefinition`: pure synchronous `describe(...,data?)`, optional pure `reduce()`.
- `ChartDrawingReconciler`: independent desired-item diff + targeted `reconcileItem()`.
- `ChartDrawingDataDefinition/DataRuntime`: one-shot async per-item generation/cancel/stale rejection + `dataKey()` + AbortSignal.
- `ChartDrawingStreamDefinition/StreamRuntime`: live stream per-item `request -> service.open -> lease(snapshot/release) -> pure event reduce`.
  - 1000 stream item 동일 open path.
  - `item-537` OFF/ON은 해당 lease만 release/reopen.
  - open 전 취소는 service 자체를 시작하지 않음.
  - 이미 시작된 open 취소는 idle authority를 즉시 놓고 late lease를 release.
  - open 완료 전 이벤트는 item queue에 보존 후 순서대로 적용.
  - snapshot/event는 JSON-only; 한 item 실패가 sibling을 건드리지 않음.
- `ChartDrawingPipeline`: sync / one-shot async / live stream을 한 generic pipeline에서 처리.
  - async/stream ready/change는 whole-list 재스캔 없이 addressed item `reconcileItem()` 1회만 수행.
  - 1000 stream drawing에서 item-537 event = drawing `ensure(item-537)` 1건만 발생.
  - 한 definition에 async data + stream source 동시 소유는 금지.
- `ChartDrawingSurfaceRouter/ContextRegistry`: opaque `surfaceId` translation.
- `ChartSubjectDrawingSurfaceBinder`: legacy subjectViews와 새 renderer 사이 임시 bridge; final child 전환 후 삭제 대상.
- `ChartAddonStateStore`: `addons[id]` 독립 node에 optional `parentId` persistence.
- `ChartDesiredItemProjection`: generic parent-chain `effectiveEnabled`; missing parent/cycle은 invalid chain만 fail-closed.
- `ChartDrawingActionDispatcher`: feature semantic action은 Add-on reducer로 위임. reserved generic lifecycle command `chart.item.remove`는 해당 independent state node만 제거.

### pure Add-on 준비 완료 범위

- Indicator 11종 pure descriptor + 기존 계산 equivalence.
- Trend Regime pure line/marker/region descriptor.
- Managed Strategy pure fast/slow JMA + signal markers descriptor.
- N_UP_COUNT `dataKey + loadData + pane/histogram descriptor`.
- MarketBeta parent: primary beta high/low line + async raw panel data boundary.
- **MarketBeta child 표준 부품 준비 완료**:
  - legacy `selectedSubjects[]`를 migration input으로만 읽는 `projectMarketBetaSubjectChildNodes()`.
  - one stock = one stable child id + `parentId` + independent state node.
  - one stock = one `bars` stream request.
  - one stock = one `pane + candlestick + legend` pure descriptor.
  - stream reset/bar event는 해당 child JSON bars snapshot만 갱신.
  - legend delete = `{type:'chart.item.remove'}` generic command.
  - active legacy `selectedSubjects[] -> subjectViews.replace(owner)` path는 아직 살아 있으므로 active-path PASS는 아님.

### semantic gate / 최근 PASS

- drawing/async/state parent-child cardinality 1/1000 + item-537 locality PASS.
- restart == normal apply, global/parent OFF == 동일 per-item remove 반복 PASS for new standard components.
- stale relative Core import integrity gate PASS.
- latest standardization head `8700ea1185773660fc1145e585427c5e0ae3b174`, `Verify chart platform` workflow #100 **PASS**.
- stream gate 초기 failure #90에서 취소 전 service가 늦게 시작될 수 있는 product defect를 발견해 Runtime을 수정했고, in-flight late lease test도 정확한 scenario로 분리했다.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`/catalog는 legacy `definition.create(context)` live-object path.
- MarketBeta active implementation은 아직 `selectedSubjects[] -> subjectViews.replace(owner)` collection lifecycle.
- Compare / SectorLeadership / ConditionSearch도 collection/owner whole lifecycle.
- `ChartSubjectViewManager`는 whole subject signature/revision/replace(owner).
- JSON에는 compare `subjects[]`, restore-only `__layout` authority가 남아 있음.
- `MarketChart.whenAddonsIdle()` 뒤 별도 layout restore/stabilize/viewport 경로가 남아 있음.
- PR #5는 계속 draft이며 dsl submodule main baseline은 아직 advance하지 않는다.

## 할 일

1. **Compare를 independent child node 구조로 준비한다.**
   - 기존 `subjects[]`를 migration input으로만 읽는다.
   - one compare subject = one persisted child node + one bars stream + one pane/candlestick/legend descriptor.
   - stable child id / `parentId` / item-local delete/select command를 사용한다.
   - whole signature/revision/pending/replace(owner)를 새 표준 정의에 재현하지 않는다.

2. SectorLeadership / ConditionSearch를 같은 independent child node + generic data/stream pipeline 구조로 준비한다.
   - realtime membership은 state node add/remove만 수행하고 drawing handle을 직접 소유하지 않는다.

3. 모든 feature가 pure definition/data/stream/reducer 준비된 뒤 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create`/`.describe` fallback 또는 이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

4. 그 뒤 `ChartSubjectViewManager` collection lifecycle, compare collection JSON, restore-only `__layout`, 별도 layout stabilization path를 제거/마이그레이션한다.

5. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, restart==normal apply, idempotence, single-path.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
