# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일은 `rules.md` + `todo.md` 두 개뿐이다.** 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다.
- `rules.md`에 4축 의미, semantic invariant, semantic gate 불변성, 주기적 STANDARDIZATION CYCLE을 고정했다.
- **Core 축 `src/core/chart` 표준화 완료.**
  - JMA/SMA/EMA feature 계산을 Core에서 제거하고 Add-on-owned `src/addons/indicator/math/`로 내용 변경 없이 이동했다.
  - `src/core/chart`에는 `ChartAddonSurface`, `ChartCore`, `PaneLegendDescriptor`, `PriceDisplayMode`의 generic chart primitive만 남겼다.
  - Chart PR #4 CI PASS, main merge `ded98eb6d782d853ed1bd805abc83692d50b3ff1`, main workflow `33720008027` PASS.
  - dsl `vendor/kiwoom-condition`도 `ded98eb6d782d853ed1bd805abc83692d50b3ff1`로 advance했다.
  - 이 감사 범위의 Core는 `STANDARD`; 전체 4축/global PASS는 아니다.
- **4축 baseline 사전감사를 완료했고 나머지 축은 NONSTANDARD로 확정했다.**
  - **Add-on = NONSTANDARD.** 11개 indicator Add-on 모두 feature 계산 자체는 Add-on 책임에 맞지만 `context.surface.createLineSeries/createPane/createHistogramSeries`, live handle `setData/update/setVisible/dispose`를 직접 소유한다. Add-on이 descriptor가 아니라 renderer/lifecycle owner다.
  - `research.n-up-count`, `trend-regime`, `battlefield-map`, `battlefield-force-allocation`, `market-beta-cohort`도 raw series/pane/marker/region lifecycle을 직접 소유한다.
  - `research.compare-subjects`는 자체 `revision/pending`과 whole `subjects[] -> subjectViews.replace(owner)` collection lifecycle을 소유한다.
  - `ConditionSearchAddon`, `SectorLeadershipAddon`은 pane/candlestick/bar-window/projection/view collection 생성·재구축·dispose까지 Add-on 내부에서 직접 소유한다.
  - 비그리기 `FeatureValidationAddon` 같은 stub은 drawing-handle 오염은 없지만, `strategy.manager`는 DOM/UI lifecycle을 Add-on이 직접 소유해 UI 축 별도 표준화 대상이다.
  - **Bridge/Runtime = NONSTANDARD.** `ChartRuntimeHost`의 기본 실행계약이 `definition.create(context)` live object이며 raw `surface`, `layout`, `createProjection`, capability를 Add-on에 전달한다. live authority가 render-item `Map<itemId, liveHandle>`가 아니라 Add-on instance 객체다.
  - `ChartSubjectViewManager`는 owner collection/signature/whole replace lifecycle을 가진다. item cardinality/locality 규칙과 맞지 않는다.
  - `ChartPaneLayoutManager`는 JSON `__layout`을 읽어 frame-loop `stabilizePersistedLayout()`과 restore completion 판정을 수행한다. `restart == normal apply` 위반이다.
  - `ChartStateRuntimeAudit`는 JSON/active Add-on/`__layout` pane를 복원 후 별도로 대조한다. 표준화 후 진단용이 아니라 제품 정상동작 성립에 필수라면 비표준이다.
  - **JSON/Persistence = PARTIAL/NONSTANDARD.** `ChartAddonStateStore`의 top-level `enabled/visible/state`와 persistence serialization 자체는 generic 기반이다. 그러나 JSON Add-on node와 실제 render item이 1:1로 강제되지 않아 `state.subjects[]`, `state.__layout` 같은 collection/restore authority를 숨길 수 있다. `research.compare-subjects`가 실제 사례다.
  - **UI/Composition single path = NONSTANDARD.** `MarketChart.whenAddonsIdle()`이 Runtime idle 뒤 `paneLayout.stabilizePersistedLayout()`을 별도 실행하고 startup viewport 재적용도 가진다. normal lifecycle과 restore lifecycle이 분리되어 있다.
- 따라서 현재 판정은 `Core(chart scope)=STANDARD / Add-on=NONSTANDARD / Runtime=NONSTANDARD / JSON=NONSTANDARD / single-path=NONSTANDARD`다.
- 기존 static `audit-addon-boundaries.mjs` PASS는 위 semantic 결함을 뒤집지 못한다.
- 추가 compare restore/height/timing 보정 패치는 중단 상태다.
- 작업 branch는 `dsl-live-studio`; `origin/main`을 섞지 않는다.
- repo-wide/global compliance는 `REMEDIATION_REQUIRED`다.

## 할 일

- **이제 감사가 아니라 구조 교체 단계로 진입한다.** 기존 비표준 lifecycle에 보정층을 추가하지 않는다.
- 목표 실행계약을 하나로 고정한다.
  - JSON = 독립 desired item `{id, definitionId/type, enabled, visible, props/state, layout}`.
  - Add-on = live handle 없이 one-item drawing descriptor + feature 계산만 반환.
  - Runtime = descriptor를 generic Core grammar로 번역하고 `Map<itemId, liveHandle>`에서 `ensure/update/remove`만 수행.
  - restart/global/item ON/OFF 모두 같은 desired-state apply 경로를 사용.
- 구현은 **별도 표준화 branch에서 완성 전까지 main에 merge하지 않는다.** 중간 migration 때문에 legacy와 descriptor active path가 공존하는 상태를 최종 main에 남기지 않는다.
- 첫 구현 tranche:
  1. generic one-item drawing descriptor contract를 확정한다. 최소 primitive는 primary/dedicated pane + line/histogram/candlestick/marker/region/legend + data/options/layout이다.
  2. generic Runtime renderer가 descriptor를 `ensure/update/remove(itemId)`로 소유하도록 만든다. Add-on에 raw surface/live handle을 넘기지 않는 것이 최종 계약이다.
  3. 먼저 SMA/EMA/JMA 같은 단순 primary-line indicator를 descriptor 방식으로 옮겨 구조를 증명한다.
  4. 이어 모든 indicator를 같은 방식으로 이동한다.
  5. research/compare의 async data는 Add-on-owned pane lifecycle이 아니라 generic data request/desired child item으로 변환한다.
  6. 마지막 legacy `definition.create(context)` drawing path를 삭제한 뒤에만 Runtime 표준화 branch를 merge한다.
- 그 후 JSON compare `subjects[]`를 independent desired items로 변환하고 `__layout` restore state-machine을 제거한다.
- 마지막에 semantic operation recorder로 1/10/1000 cardinality, locality, global/item visibility, restart==normal apply, idempotence, single-path를 고정한다.
- semantic gate는 제품에 맞춰 완화하지 않는다.
- 전체 4축 baseline이 STANDARD가 되기 전 UIA-1/Chart 구조 PASS를 선언하지 않는다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
