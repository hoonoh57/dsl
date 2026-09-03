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

- `ChartDrawingGrammar`: JSON-only generic primitives.
- `ChartDrawingRuntime`: item-local `ensure/update/setVisible/remove`.
- `ChartDrawingDefinition`: pure synchronous `describe(...,data?)` + optional pure `reduce()`.
- `ChartDrawingReconciler`: independent desired-item diff + targeted `reconcileItem()`.
- `ChartDrawingDataDefinition/DataRuntime`: one-shot async per-item generation/cancel/stale rejection + `dataKey()` + AbortSignal.
- `ChartDrawingStreamDefinition/StreamRuntime`: live stream per-item request/open/lease/reduce; 1000/item-537 locality gate PASS.
- `ChartDrawingPipeline`: sync/async/stream 한 generic pipeline; ready/change는 addressed item만 재적용.
- `ChartDrawingSurfaceRouter/ContextRegistry`: opaque surfaceId translation.
- `ChartSubjectDrawingSurfaceBinder`: legacy subjectViews와 새 renderer 사이 임시 bridge; final child 전환 후 삭제 대상.
- `ChartAddonStateStore`: `addons[id]` 독립 node + optional `parentId` persistence.
- `ChartDesiredItemProjection`: generic parent-chain effectiveEnabled.
- `ChartDrawingActionDispatcher`: semantic action은 Add-on reducer로 위임; generic `chart.item.remove`, `chart.selection.set`만 Runtime lifecycle command로 허용.

### pure Add-on 준비 완료 범위

- Indicator 11종 pure descriptor + 기존 계산 equivalence.
- Trend Regime pure descriptor.
- Managed Strategy pure descriptor.
- N_UP_COUNT `dataKey + loadData + descriptor`.
- MarketBeta parent + independent subject child 준비.
- Compare independent child 준비 완료:
  - legacy `subjects[]` migration input → one child node/stream/pane descriptor.
  - `__layout` height를 child paneHeight로 정확히 이관.
  - selectedPaneId는 generic selection으로 migration.
  - 1000 subject locality gate PASS.
- SectorLeadership independent child 준비 완료:
  - leader/follower one child node + bars stream + pane/candlestick/legend.
  - child id는 instrument code 기준으로 stable; role 변경도 same id update.
  - role/palette slot을 child state에 고정하여 sibling 삭제 후 새 lifecycle 의존 제거.
  - selection/delete는 generic commands.
- ConditionSearch independent child base 준비 완료:
  - current authoritative session일 때만 legacy selectedSubjects를 child node로 projection.
  - one selected stock = one child node + bars stream + pane/candlestick/legend.
  - stale persisted selection은 session authority가 없으면 child 0개로 fail-closed.
  - delete는 generic `chart.item.remove`.

### semantic gate / 최근 PASS

- MarketBeta stream/pipeline `8700ea1185773660fc1145e585427c5e0ae3b174`, workflow #100 PASS.
- Compare child + generic selection `2cf88bbdd78824f9428df617c29db45dc11a8e33`, workflow #107 PASS.
- SectorLeadership child `2b775500b9c42bc85b4221ccb6c9bd13b83b1f3c`, workflow #110 PASS.
- ConditionSearch child base `8fa762820021a4b242d7db0f8ab78682d1fef5ef`, workflow #112 **PASS**.

### 현재 발견된 핵심 미해결 표준화 결함

- ConditionSearch legacy semantics는 새 세션에서 persisted selected results를 STALE로 막는다.
- independent Condition child를 일반 persistent node로 저장하면 다음 재시작 때 stale child가 다시 표시될 수 있다.
- 현재 persistence controller는 StateStore 전체 snapshot을 JSON으로 저장하므로 이 문제가 실제로 발생할 수 있다.
- 따라서 Condition 전용 예외가 아니라 **generic session-scoped desired node**가 필요하다: Runtime render path는 persistent node와 동일하되 disk JSON에는 저장하지 않는다.

### 아직 NONSTANDARD

- active `ChartRuntimeHost`/catalog는 legacy `definition.create(context)` live-object path.
- MarketBeta/Compare/SectorLeadership/ConditionSearch active legacy lifecycle은 아직 살아 있음.
- `ChartSubjectViewManager` whole collection lifecycle이 살아 있음.
- JSON에는 legacy collection state와 restore-only `__layout` authority가 남아 있음.
- `MarketChart.whenAddonsIdle()` 뒤 별도 layout restore/stabilize/viewport 경로가 남아 있음.

## 할 일

1. **generic session-scoped desired node persistence 계약을 만든다.**
   - in-memory State/Projection/Pipeline 경로는 persistent node와 동일해야 한다.
   - session-scoped node는 disk JSON save/hydrate authority에서 제외한다.
   - restart 시 session node가 0개임을 gate로 검증한다.
   - persistent sibling은 동일 snapshot/save 경로에서 손실되면 안 된다.
   - ConditionSearch 전용 분기 금지.

2. session-scope PASS 후 ConditionSearch realtime membership을 parent feature state + generic child node add/remove command로 분리한다.
   - membership D는 해당 child node만 제거.
   - membership I는 resultCodes feature state만 갱신하며 selected child를 임의 생성하지 않는다.

3. 모든 feature pure definition/data/stream/reducer 준비 후 `ChartRuntimeHost`를 **한 번의 경계 변경**으로 `State -> DesiredItemProjection -> DrawingPipeline -> Core` 단일 active path로 전환한다.
   - `.create`/`.describe` fallback 또는 이중 active path 금지.
   - 전환과 동시에 legacy drawing live implementations 제거.

4. 이후 `ChartSubjectViewManager`, legacy collection JSON, restore-only `__layout`, 별도 layout stabilization path를 제거/마이그레이션한다.

5. 최종 제품경로 gate: 1/10/1000 cardinality, locality, async/stream locality, global/item/parent equivalence, restart==normal apply, idempotence, single-path.

- semantic gate는 제품에 맞춰 완화하지 않는다.
- tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
