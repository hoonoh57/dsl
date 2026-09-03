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
- JSON/State = independent desired node persistence/ON-OFF만.
- invariant = `1 item ON/OFF == N items 중 1 item ON/OFF`; parent/global OFF와 restart도 같은 per-item path 반복.

### 표준 부품 완료

- `ChartDrawingGrammar`: JSON-only `pane/line/histogram/candlestick/legend/markers/region`.
- `ChartDrawingRuntime`: item-local `ensure/update/setVisible/remove`.
- `ChartDrawingDefinition`: pure synchronous `describe(...,data?)`, optional pure `reduce()`.
- `ChartDrawingReconciler`: independent desired-item diff + targeted `reconcileItem()`.
- `ChartDrawingDataDefinition/DataRuntime`: one-shot async per-item generation/cancel/stale rejection + `dataKey()` + AbortSignal.
- `ChartDrawingStreamDefinition/StreamRuntime`: live stream per-item `request -> service.open -> lease(snapshot/release) -> pure event reduce`.
- `ChartDrawingPipeline`: sync / one-shot async / live stream을 한 generic pipeline에서 처리; ready/change는 addressed item만 `reconcileItem()`.
- `ChartDrawingSurfaceRouter/ContextRegistry`: opaque `surfaceId` translation.
- `ChartSubjectDrawingSurfaceBinder`: legacy subjectViews와 새 renderer 사이 임시 bridge; final child 전환 후 삭제 대상.
- `ChartAddonStateStore`: `addons[id]` 독립 node + optional `parentId` persistence.
- `ChartDesiredItemProjection`: generic parent-chain `effectiveEnabled`; missing parent/cycle은 invalid chain만 fail-closed.
- `ChartDrawingActionDispatcher`: semantic action은 Add-on reducer로 위임; generic `chart.item.remove`, `chart.selection.set`만 Runtime lifecycle command로 허용.

### pure Add-on 준비 완료 범위

- Indicator 11종 pure descriptor + 기존 계산 equivalence.
- Trend Regime pure line/marker/region descriptor.
- Managed Strategy pure fast/slow JMA + signal markers descriptor.
- N_UP_COUNT `dataKey + loadData + pane/histogram descriptor`.
- MarketBeta parent: primary beta high/low line + async raw panel data.
- MarketBeta child: one stock = one child node + bars stream + pane/candlestick/legend; delete=`chart.item.remove`.
- **Compare child 준비 완료**:
  - legacy `subjects[]`는 migration input으로만 projection.
  - one compare subject = one stable child node + `parentId` + bars stream + pane/candlestick/legend.
  - legacy `__layout.panes[paneId].height`를 child `paneHeight`로 정확히 이관(52/108/327 포함).
  - parent pure state에서 `subjects[]`, `__layout`, `selectedPaneId` 제거.
  - legacy selectedPaneId는 generic `chart.selection.set` payload로 migration.
  - legend select=`chart.selection.set`, delete=`chart.item.remove`; feature callback 없음.
  - 1000 legacy subjects에서 subject-537 제거 시 child id 1개만 사라지는 locality gate PASS.

### semantic gate / 최근 PASS

- drawing/async/stream/state parent-child cardinality 1/1000 + item-537 locality PASS.
- restart == normal apply, global/parent OFF == 동일 per-item remove 반복 PASS for new standard components.
- stale relative Core import integrity gate PASS.
- MarketBeta stream/pipeline checkpoint `8700ea1185773660fc1145e585427c5e0ae3b174`, workflow #100 PASS.
- Compare child + generic selection checkpoint `2cf88bbdd78824f9428df617c29db45dc11a8e33`, workflow #107 **PASS**.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`/catalog는 legacy `definition.create(context)` live-object path.
- MarketBeta active implementation은 `selectedSubjects[] -> subjectViews.replace(owner)`가 아직 살아 있음.
- Compare active implementation은 `subjects[] -> revision/pending -> subjectViews.replace(owner)`가 아직 살아 있음.
- SectorLeadership / ConditionSearch는 Add-on-owned collection/live drawing lifecycle.
- `ChartSubjectViewManager`는 whole subject signature/revision/replace(owner).
- JSON에는 legacy collection state와 restore-only `__layout` authority가 남아 있음.
- `MarketChart.whenAddonsIdle()` 뒤 별도 layout restore/stabilize/viewport 경로가 남아 있음.

## 할 일

1. **SectorLeadership을 independent child node 구조로 준비한다.**
   - leader/follower 1개 = one child node + bars stream + pane/candlestick/legend descriptor.
   - palette/role/selection은 child pure state/descriptor로만 표현.
   - Add-on `#views/#revision/#rebuild`, direct pane/barWindow/projection lifecycle을 새 정의에 재현하지 않는다.
   - subject 하나 추가/삭제/선택이 sibling lifecycle을 건드리지 않아야 한다.

2. ConditionSearch를 independent child node + generic stream/state 구조로 준비한다.
   - realtime membership 변화는 state node add/remove만 수행하고 drawing handle을 직접 소유하지 않는다.

3. 모든 feature pure definition/data/stream/reducer 준비 후 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create`/`.describe` fallback 또는 이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

4. 그 뒤 `ChartSubjectViewManager` collection lifecycle, legacy collection JSON, restore-only `__layout`, 별도 layout stabilization path를 제거/마이그레이션한다.

5. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, restart==normal apply, idempotence, single-path.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
